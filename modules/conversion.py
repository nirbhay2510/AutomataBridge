
import streamlit as st
from collections import deque


# ============================================================
# MEALY TO MOORE CONVERSION
# ============================================================

def convert_mealy_to_moore(machine, transitions):

    states = machine["states"]
    inputs = machine["inputs"]
    outputs = machine["outputs"]
    initial_state = machine["initial_state"]

    transition_lookup = {
        row["State"]: row
        for row in transitions
    }

    if initial_state not in transition_lookup:
        raise ValueError(
            f"Initial state '{initial_state}' has no transition row."
        )

    # Validate transition rows.
    for state in states:

        if state not in transition_lookup:
            raise ValueError(
                f"Missing transition row for state '{state}'."
            )

        row = transition_lookup[state]

        for symbol in inputs:

            next_col = f"Input {symbol} - Next State"
            output_col = f"Input {symbol} - Output"

            if next_col not in row or output_col not in row:
                raise ValueError(
                    f"Incomplete transition for state '{state}' "
                    f"and input '{symbol}'."
                )

            destination = row[next_col]
            transition_output = str(row[output_col])

            if destination not in states:
                raise ValueError(
                    f"Unknown destination state '{destination}'."
                )

            if transition_output not in outputs:
                raise ValueError(
                    f"Unknown output symbol '{transition_output}'."
                )

    # None is used internally for the initial no-output condition.
    # This avoids conflicts if epsilon is configured as an output.
    epsilon = "ε"
    initial_pair = (initial_state, None)

    # --------------------------------------------------------
    # STEP 1: FIND REACHABLE STATE-OUTPUT PAIRS
    # --------------------------------------------------------

    reachable_pairs = []
    visited = set()
    queue = deque([initial_pair])

    while queue:

        pair = queue.popleft()

        if pair in visited:
            continue

        visited.add(pair)
        reachable_pairs.append(pair)

        state, _ = pair
        row = transition_lookup[state]

        for symbol in inputs:

            destination = row[
                f"Input {symbol} - Next State"
            ]

            transition_output = str(
                row[f"Input {symbol} - Output"]
            )

            next_pair = (
                destination,
                transition_output
            )

            if next_pair not in visited:
                queue.append(next_pair)

    # --------------------------------------------------------
    # STEP 2: COLLECT DISTINCT INCOMING OUTPUTS
    # --------------------------------------------------------

    state_outputs = {
        state: []
        for state in states
    }

    for state, output in reachable_pairs:

        if output is None:
            continue

        if output not in state_outputs[state]:
            state_outputs[state].append(output)

    # Preserve the configured output alphabet order.
    for state in states:

        state_outputs[state].sort(
            key=lambda output: (
                outputs.index(output)
                if output in outputs
                else len(outputs)
            )
        )

    # --------------------------------------------------------
    # STEP 3: GENERATE MOORE STATE NAMES
    # --------------------------------------------------------

    state_mapping = {}
    used_names = set()

    def make_state_name(state, output, split):

        if output is None:
            base_name = state

        elif split:
            base_name = f"{state}{output}"

        else:
            base_name = state

        candidate = base_name
        counter = 2

        # Avoid duplicate generated state names.
        while candidate in used_names:

            candidate = f"{base_name}_{counter}"
            counter += 1

        used_names.add(candidate)

        return candidate

    for state in states:

        distinct_outputs = state_outputs[state]

        # CASE 1: No incoming output.
        if not distinct_outputs:

            state_mapping[(state, None)] = (
                make_state_name(
                    state,
                    None,
                    False
                )
            )

        # CASE 2: Only one distinct incoming output.
        elif len(distinct_outputs) == 1:

            output = distinct_outputs[0]

            state_mapping[(state, output)] = (
                make_state_name(
                    state,
                    output,
                    False
                )
            )

        # CASE 3: Multiple distinct incoming outputs.
        else:

            for output in distinct_outputs:

                state_mapping[(state, output)] = (
                    make_state_name(
                        state,
                        output,
                        True
                    )
                )

    # --------------------------------------------------------
    # STEP 4: DETERMINE THE INITIAL MOORE STATE
    # --------------------------------------------------------

    initial_outputs = state_outputs[initial_state]

    if not initial_outputs:

        # No incoming output:
        # Keep the original initial state with epsilon.

        converted_initial_state = state_mapping[
            (initial_state, None)
        ]

    else:

        # One incoming output:
        # Keep original state name.
        #
        # Multiple incoming outputs:
        # Select the first output-specific variant according
        # to the configured output alphabet.

        selected_output = initial_outputs[0]

        converted_initial_state = state_mapping[
            (initial_state, selected_output)
        ]

        # Map the initial no-output condition to the selected
        # variant. No additional A/epsilon state is generated.

        state_mapping[(initial_state, None)] = (
            converted_initial_state
        )

    # --------------------------------------------------------
    # STEP 5: REMOVE EXTRA INITIAL EPSILON PAIR
    # --------------------------------------------------------

    final_pairs = []

    for state, output in reachable_pairs:

        if (
            state == initial_state
            and output is None
            and initial_outputs
        ):
            continue

        final_pairs.append((state, output))

    # --------------------------------------------------------
    # STEP 6: CREATE CONVERTED MOORE TRANSITION TABLE
    # --------------------------------------------------------

    converted_rows = []

    for state, output in final_pairs:

        if output is None:
            display_output = epsilon
        else:
            display_output = output

        new_row = {
            "State": state_mapping[(state, output)],
            "Original State": state,
            "Output": display_output,
        }

        source_row = transition_lookup[state]

        for symbol in inputs:

            destination = source_row[
                f"Input {symbol} - Next State"
            ]

            transition_output = str(
                source_row[
                    f"Input {symbol} - Output"
                ]
            )

            destination_pair = (
                destination,
                transition_output
            )

            if destination_pair not in state_mapping:
                raise ValueError(
                    f"Unable to map destination pair "
                    f"{destination_pair}."
                )

            new_row[f"Input {symbol}"] = (
                state_mapping[destination_pair]
            )

        converted_rows.append(new_row)

    # --------------------------------------------------------
    # STEP 7: GROUP REACHABLE ORIGINAL STATES
    # --------------------------------------------------------

    reachable_original_states = list(
        dict.fromkeys(
            state
            for state, _ in final_pairs
        )
    )

    # --------------------------------------------------------
    # STEP 8: RETURN CONVERTED MACHINE
    # --------------------------------------------------------

    return {
        "type": "Moore",
        "rows": converted_rows,
        "initial_state": converted_initial_state,
        "state_mapping": state_mapping,
        "state_outputs": state_outputs,
        "groups": reachable_original_states,
        "inputs": inputs,
    }


# ============================================================
# MOORE TO MEALY CONVERSION
# ============================================================

def convert_moore_to_mealy(machine, transitions):

    states = machine["states"]
    inputs = machine["inputs"]
    initial_state = machine["initial_state"]

    state_outputs = {
        row["State"]: row["Output"]
        for row in transitions
    }

    converted_rows = []

    for row in transitions:

        new_row = {
            "State": row["State"],
        }

        for symbol in inputs:

            destination = row[
                f"Input {symbol} - Next State"
            ]

            if destination not in state_outputs:
                raise ValueError(
                    f"No output found for destination state "
                    f"'{destination}'."
                )

            new_row[
                f"Input {symbol} - Next State"
            ] = destination

            new_row[
                f"Input {symbol} - Output"
            ] = state_outputs[destination]

        converted_rows.append(new_row)

    return {
        "type": "Mealy",
        "rows": converted_rows,
        "initial_state": initial_state,
        "state_outputs": state_outputs,
        "groups": states,
        "inputs": inputs,
    }


# ============================================================
# OUTPUT EQUIVALENCE CHECK
# ============================================================

def check_output_equivalence(
    machine,
    original_transitions,
    result,
    input_sequence,
):

    """Compare original and converted outputs."""

    inputs = machine["inputs"]

    unknown = [
        symbol
        for symbol in input_sequence
        if symbol not in inputs
    ]

    if unknown:

        raise ValueError(
            "Unknown input symbol(s): "
            + ", ".join(dict.fromkeys(unknown))
        )

    original_lookup = {
        row["State"]: row
        for row in original_transitions
    }

    converted_lookup = {
        row["State"]: row
        for row in result["rows"]
    }

    original_state = machine["initial_state"]
    converted_state = result["initial_state"]

    original_outputs = []
    converted_outputs = []

    for symbol in input_sequence:

        if original_state not in original_lookup:

            raise ValueError(
                f"No transition row exists for state "
                f"'{original_state}'."
            )

        if converted_state not in converted_lookup:

            raise ValueError(
                f"No converted transition row exists for state "
                f"'{converted_state}'."
            )

        original_row = original_lookup[original_state]
        converted_row = converted_lookup[converted_state]

        # ----------------------------------------------------
        # MEALY TO MOORE
        # ----------------------------------------------------

        if machine["direction"] == "Mealy to Moore":

            original_output = original_row[
                f"Input {symbol} - Output"
            ]

            original_outputs.append(original_output)

            original_state = original_row[
                f"Input {symbol} - Next State"
            ]

            converted_state = converted_row[
                f"Input {symbol}"
            ]

            if converted_state not in converted_lookup:

                raise ValueError(
                    f"Converted destination state "
                    f"'{converted_state}' does not exist."
                )

            converted_output = converted_lookup[
                converted_state
            ]["Output"]

            converted_outputs.append(converted_output)

        # ----------------------------------------------------
        # MOORE TO MEALY
        # ----------------------------------------------------

        else:

            original_state = original_row[
                f"Input {symbol} - Next State"
            ]

            if original_state not in result["state_outputs"]:

                raise ValueError(
                    f"No Moore output exists for state "
                    f"'{original_state}'."
                )

            original_output = result[
                "state_outputs"
            ][original_state]

            original_outputs.append(original_output)

            converted_output = converted_row[
                f"Input {symbol} - Output"
            ]

            converted_outputs.append(converted_output)

            converted_state = converted_row[
                f"Input {symbol} - Next State"
            ]

    return {
        "original_outputs": original_outputs,
        "converted_outputs": converted_outputs,
        "equivalent": (
            original_outputs == converted_outputs
        ),
        "input_sequence": list(input_sequence),
    }


# ============================================================
# OUTPUT EQUIVALENCE TEST UI
# ============================================================

def render_output_equivalence_test(
    machine,
    transitions,
    result,
):

    st.markdown("### Output-equivalence test")

    st.caption(
        "Enter an input sequence to run it on both machines "
        "and compare their outputs. Separate symbols with "
        "commas (for example: 0, 1, 0)."
    )

    sequence_text = st.text_input(
        "Input sequence",
        key=f"equivalence_sequence_"
            f"{st.session_state.machine_version}",
        placeholder="0, 1, 0",
    )

    if st.button(
        "Test output equivalence",
        key=f"run_equivalence_"
            f"{st.session_state.machine_version}",
        use_container_width=True,
    ):

        sequence = [
            part.strip()
            for part in sequence_text.split(",")
            if part.strip()
        ]

        try:

            comparison = check_output_equivalence(
                machine,
                transitions,
                result,
                sequence,
            )

        except (KeyError, ValueError) as error:

            st.error(
                f"Unable to run comparison: {error}"
            )

            return

        if comparison["equivalent"]:

            st.success(
                "The output sequences match for this input sequence."
            )

        else:

            st.error(
                "The output sequences do not match. "
                "Check the conversion logic."
            )

        col1, col2 = st.columns(2)

        with col1:

            st.markdown("**Original machine output**")

            st.code(
                " → ".join(
                    comparison["original_outputs"]
                ) or "(empty sequence)"
            )

        with col2:

            st.markdown("**Converted machine output**")

            st.code(
                " → ".join(
                    comparison["converted_outputs"]
                ) or "(empty sequence)"
            )

        if machine["direction"] == "Mealy to Moore":

            st.caption(
                "The initial Moore-state output is excluded "
                "from this comparison because the Mealy "
                "machine emits no output before the first input."
            )


# ============================================================
# STATE-BY-STATE CONVERSION DETAILS
# ============================================================

def _render_state_details(
    machine,
    result,
    current_state,
):

    if machine["direction"] == "Mealy to Moore":

        outputs = result["state_outputs"][current_state]

        if not outputs:

            generated_state = result["state_mapping"][
                (current_state, None)
            ]

            st.info(
                f"Original state {current_state} has no "
                "reachable incoming output. It remains as "
                f"{generated_state} with output ε."
            )

        else:

            generated = [
                result["state_mapping"][
                    (current_state, output)
                ]
                for output in outputs
            ]

            if len(outputs) == 1:

                st.info(
                    f"Original state {current_state} has only "
                    "one distinct incoming output. No splitting "
                    f"is required. Its Moore state is {generated[0]}."
                )

            else:

                st.info(
                    f"Original state {current_state} has "
                    f"{len(outputs)} distinct incoming outputs. "
                    "It is split into separate Moore states."
                )

            for output, generated_state in zip(
                outputs,
                generated,
            ):

                st.markdown(
                    f"- **{generated_state}** — "
                    f"Moore output: `{output}`"
                )

        rows = [
            row
            for row in result["rows"]
            if row["Original State"] == current_state
        ]

        if rows:

            st.caption(
                "Transitions created for this original state:"
            )

            for row in rows:

                transitions_text = " · ".join(
                    f"{symbol} → {row[f'Input {symbol}']}"
                    for symbol in machine["inputs"]
                )

                st.markdown(
                    f"**{row['State']}** "
                    f"(output `{row['Output']}`): "
                    f"{transitions_text}"
                )

    else:

        output = result["state_outputs"][current_state]

        st.info(
            f"Moore state {current_state} has output "
            f"`{output}`. Each outgoing Mealy transition "
            "receives the output of its destination state."
        )

        row = next(
            row
            for row in result["rows"]
            if row["State"] == current_state
        )

        for symbol in machine["inputs"]:

            st.markdown(
                f"- Input `{symbol}` → "
                f"next state "
                f"`{row[f'Input {symbol} - Next State']}`, "
                f"Mealy output "
                f"`{row[f'Input {symbol} - Output']}`"
            )


# ============================================================
# CONVERSION WORKSPACE
# ============================================================

def render_conversion_workspace(
    machine,
    transitions,
    converter,
):

    direction = machine["direction"]

    if not st.session_state.conversion_started:

        if direction == "Mealy to Moore":

            st.markdown("### Initial Moore state")

            st.info(
                "The initial Moore state follows the compact "
                "initial-state convention. If the original "
                "initial state has incoming outputs, one of "
                "its output-specific variants is selected as "
                "the initial state. If it has no incoming "
                "outputs, it retains ε (epsilon). The initial "
                "Moore output is excluded when comparing "
                "output sequences."
            )

        else:

            st.caption(
                "The conversion uses the output of each "
                "destination state."
            )

        if not st.button(
            "Start conversion",
            use_container_width=True,
        ):

            return None

        result = converter(
            machine,
            transitions,
        )

        st.session_state.conversion_result = result
        st.session_state.conversion_started = True
        st.session_state.conversion_index = 0

        st.rerun()

    result = st.session_state.conversion_result
    groups = result["groups"]

    if not groups:

        st.warning(
            "No reachable states were produced by this conversion."
        )

        return result

    index = min(
        st.session_state.conversion_index,
        len(groups) - 1,
    )

    current_state = groups[index]

    st.markdown("### State-by-state conversion")

    st.progress(
        (index + 1) / len(groups)
    )

    st.caption(
        f"Step {index + 1} of {len(groups)} · "
        f"Processing original state {current_state}"
    )

    previous_col, next_col, status_col = st.columns(
        [1, 1, 2]
    )

    with previous_col:

        if st.button(
            "← Previous",
            disabled=index == 0,
            use_container_width=True,
        ):

            st.session_state.conversion_index -= 1
            st.rerun()

    with next_col:

        if st.button(
            "Next →",
            disabled=index == len(groups) - 1,
            use_container_width=True,
        ):

            st.session_state.conversion_index += 1
            st.rerun()

    with status_col:

        if index == len(groups) - 1:

            st.success("All states converted")

        else:

            st.caption(
                "Use Next to reveal the next state's "
                "conversion in the diagram."
            )

    st.markdown(
        f"#### Current step: `{current_state}`"
    )

    _render_state_details(
        machine,
        result,
        current_state,
    )

    processed = set(
        groups[:index + 1]
    )

    if direction == "Mealy to Moore":

        visible_rows = [
            row
            for row in result["rows"]
            if row["Original State"] in processed
        ]

    else:

        visible_rows = [
            row
            for row in result["rows"]
            if row["State"] in processed
        ]

    result["visible_rows"] = visible_rows

    result["conversion_complete"] = (
        index == len(groups) - 1
    )

    return result
