
import streamlit as st


def render_configuration(direction):

    with st.container(border=True):

        st.markdown("### Define Your Machine")

        name = st.text_input(
            "Machine Name",
            key="config_machine_name",
        )

        count = st.number_input(
            "Number of States",
            min_value=1,
            max_value=50,
            value=3,
            step=1,
            key="config_state_count",
        )

        state_names = st.text_input(
            "State Names",
            key="config_state_names",
        )

        col1, col2 = st.columns(2)

        with col1:
            input_alphabet = st.text_input(
                "Input Alphabet",
                key="config_input_alphabet",
            )

        with col2:
            output_alphabet = st.text_input(
                "Output Alphabet",
                key="config_output_alphabet",
            )

        initial_state = st.text_input(
            "Initial State",
            key="config_initial_state",
        )

        submitted = st.button(
            "Create Machine",
            use_container_width=True,
            type="primary",
            key="create_machine_button",
        )

        if not submitted:
            return None

        states = [
            x.strip()
            for x in state_names.split(",")
            if x.strip()
        ]

        inputs = [
            x.strip()
            for x in input_alphabet.split(",")
            if x.strip()
        ]

        outputs = [
            x.strip()
            for x in output_alphabet.split(",")
            if x.strip()
        ]

        errors = []

        if not name.strip():
            errors.append("Enter a machine name.")

        if len(states) != count:
            errors.append(
                "State count and state names do not match."
            )

        if len(states) != len(set(states)):
            errors.append("State names must be unique.")

        if not inputs:
            errors.append("Enter at least one input symbol.")

        if len(inputs) != len(set(inputs)):
            errors.append("Input symbols must be unique.")

        if not outputs:
            errors.append("Enter at least one output symbol.")

        if len(outputs) != len(set(outputs)):
            errors.append("Output symbols must be unique.")

        if initial_state.strip() not in states:
            errors.append(
                "Initial state must be one of the defined states."
            )

        if errors:
            for error in errors:
                st.error(error)

            return None

        return {
            "name": name.strip(),
            "direction": direction,
            "states": states,
            "inputs": inputs,
            "outputs": outputs,
            "initial_state": initial_state.strip(),
        }
