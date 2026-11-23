
import streamlit as st
from collections import deque


def convert_mealy_to_moore(machine, transitions):

    states = machine["states"]
    inputs = machine["inputs"]
    initial_state = machine["initial_state"]

    transition_lookup = {
        row["State"]: row
        for row in transitions
    }

    # Epsilon represents no output before the first input.
    initial_pair = (initial_state, "ε")

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

            output = row[
                f"Input {symbol} - Output"
            ]

            next_pair = (
                destination,
                output,
            )

            if next_pair not in visited:
                queue.append(next_pair)

    state_outputs = {
        state: []
        for state in states
    }

    for state, output in reachable_pairs:

        if output not in state_outputs[state]:
            state_outputs[state].append(output)

    # Rename states only when splitting is required.
    # If a state has only one output, retain its original name.
    state_mapping = {}

    for state in states:

        outputs = state_outputs[state]

        for index, output in enumerate(outputs):

            if len(outputs) == 1:
                new_state_name = state
            else:
                new_state_name = f"{state}{index}"

            state_mapping[
                (state, output)
            ] = new_state_name

    converted_rows = []

    for state, output in reachable_pairs:

        new_row = {
            "State": state_mapping[(state, output)],
            "Original State": state,
            "Output": output,
        }

        source_row = transition_lookup[state]

        for symbol in inputs:

            destination = source_row[
                f"Input {symbol} - Next State"
            ]

            transition_output = source_row[
                f"Input {symbol} - Output"
            ]

            new_row[
                f"Input {symbol}"
            ] = state_mapping[
                (destination, transition_output)
            ]

        converted_rows.append(new_row)

    reachable_original_states = [
        state
        for state in states
        if state_outputs[state]
    ]

    return {
        "type": "Moore",
        "rows": converted_rows,
        "initial_state": state_mapping[initial_pair],
        "state_mapping": state_mapping,
        "state_outputs": state_outputs,
        "groups": reachable_original_states,
        "inputs": inputs,
    }


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


def check_output_equivalence(
    machine,
    original_transitions,
    result,
    input_sequence,
):

    """Compare original and converted outputs for an input sequence."""

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
                f"No transition row exists for state '{original_state}'."
            )

        if converted_state not in converted_lookup:
            raise ValueError(
                f"No converted transition row exists for state '{converted_state}'."
            )

        original_row = original_lookup[original_state]
        converted_row = converted_lookup[converted_state]

        if machine["direction"] == "Mealy to Moore":

            original_outputs.append(
                original_row[
                    f"Input {symbol} - Output"
                ]
            )

            original_state = original_row[
                f"Input {symbol} - Next State"
            ]

            converted_state = converted_row[
                f"Input {symbol}"
            ]

            converted_outputs.append(
                converted_lookup[converted_state]["Output"]
            )

        else:

            original_state = original_row[
                f"Input {symbol} - Next State"
            ]

            original_outputs.append(
                result["state_outputs"][original_state]
            )

            converted_outputs.append(
                converted_row[
                    f"Input {symbol} - Output"
                ]
            )

            converted_state = converted_row[
                f"Input {symbol} - Next State"
            ]

    return {
        "original_outputs": original_outputs,
        "converted_outputs": converted_outputs,
        "equivalent": original_outputs == converted_outputs,
        "input_sequence": list(input_sequence),
    }


def render_output_equivalence_test(
    machine,
    transitions,
    result,
):

    st.markdown("### Output-equivalence test")

    st.caption(
        "Enter an input sequence to run it on both machines and compare "
        "their outputs. Separate symbols with commas (for example: 0, 1, 0)."
    )

    sequence_text = st.text_input(
        "Input sequence",
        key=f"equivalence_sequence_{st.session_state.machine_version}",
        placeholder="0, 1, 0",
    )

    if st.button(
        "Test output equivalence",
        key=f"run_equivalence_{st.session_state.machine_version}",
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
                "The output sequences do not match. Check the conversion logic."
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
                "The initial Moore-state output is excluded from this "
                "comparison because the Mealy machine emits no output "
                "before the first input."
            )


def _render_state_details(
    machine,
    result,
    current_state,
):

    if machine["direction"] == "Mealy to Moore":

        outputs = result["state_outputs"][current_state]

        generated = [
            result["state_mapping"][
                (current_state, output)
            ]
            for output in outputs
        ]

        st.info(
            f"Original state {current_state} produces "
            f"{len(generated)} reachable Moore state(s), "
            "one for each distinct incoming output value, plus ε for "
            "the initial no-output condition when applicable."
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
                "Transitions created for this state's "
                "generated Moore state(s):"
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
                "The initial Moore state is assigned ε (epsilon), meaning "
                "no output has been produced before the first input. This "
                "is automatic; you do not need to choose an output. After "
                "each input, the Moore machine produces the output associated "
                "with the reached state."
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

        else:

            st.caption(
                "The conversion uses the output of each destination state."
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
                "Use Next to reveal the next state's conversion in the diagram."
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
