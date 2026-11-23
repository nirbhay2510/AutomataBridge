
import streamlit as st
import pandas as pd


def render_transition_table(machine):

    states = machine["states"]
    inputs = machine["inputs"]
    outputs = machine["outputs"]
    direction = machine["direction"]

    existing = st.session_state.get("transitions")

    columns = ["State"]

    if direction == "Moore to Mealy":
        columns.append("Output")

    for symbol in inputs:

        columns.append(
            f"Input {symbol} - Next State"
        )

        if direction == "Mealy to Moore":
            columns.append(
                f"Input {symbol} - Output"
            )

    # --------------------------------------------------
    # INITIAL DATA
    # --------------------------------------------------

    if existing:

        data = pd.DataFrame(existing)

    else:

        rows = []

        for state in states:

            row = {
                "State": state,
            }

            if direction == "Moore to Mealy":
                row["Output"] = outputs[0]

            for symbol in inputs:

                row[
                    f"Input {symbol} - Next State"
                ] = states[0]

                if direction == "Mealy to Moore":

                    row[
                        f"Input {symbol} - Output"
                    ] = outputs[0]

            rows.append(row)

        data = pd.DataFrame(rows)

    data = data.reindex(columns=columns)

    # --------------------------------------------------
    # COLUMN CONFIGURATION
    # --------------------------------------------------

    column_config = {

        "State": st.column_config.TextColumn(
            "State",
            width="small",
            disabled=True,
        ),
    }

    if direction == "Moore to Mealy":

        column_config["Output"] = (
            st.column_config.SelectboxColumn(
                "State Output",
                options=outputs,
                width="small",
                required=True,
            )
        )

    for symbol in inputs:

        next_column = f"Input {symbol} - Next State"

        column_config[next_column] = (
            st.column_config.SelectboxColumn(
                f"Next ({symbol})",
                options=states,
                width="small",
                required=True,
            )
        )

        if direction == "Mealy to Moore":

            output_column = f"Input {symbol} - Output"

            column_config[output_column] = (
                st.column_config.SelectboxColumn(
                    f"Output ({symbol})",
                    options=outputs,
                    width="small",
                    required=True,
                )
            )

    # --------------------------------------------------
    # EDITABLE TABLE
    # --------------------------------------------------

    st.caption(
        "Select the next state and output directly in each cell."
    )

    edited = st.data_editor(
        data,
        key=f"transition_editor_{st.session_state.machine_version}",
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        column_config=column_config,
        disabled=["State"],
        height=min(320, 65 + len(states) * 36),
    )

    result = edited.to_dict(orient="records")

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    for row in result:

        for column in columns:

            value = row.get(column)

            if value is None or pd.isna(value) or str(value).strip() == "":

                st.error(
                    f"Missing value in '{column}' "
                    f"for state '{row['State']}'."
                )

                return None

    return result
