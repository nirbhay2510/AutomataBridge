
import streamlit as st
import pandas as pd

from modules.ui_theme import apply_theme
from modules.machine_config import render_configuration
from modules.transition_table import render_transition_table
from modules.state_diagram import render_state_diagram
from modules.conversion import (
    convert_mealy_to_moore,
    convert_moore_to_mealy,
    render_output_equivalence_test,
)


st.set_page_config(
    page_title="Automata Studio",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_theme()

DEFAULTS = {
    "machine": None,
    "transitions": None,
    "conversion_result": None,
    "machine_version": 0,
    "edit_transitions": True,
    "page_navigation": "01 Machine Configuration",
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


pages = [
    "01 Machine Configuration",
    "02 Machine Comparison",
    "03 Summary",
]


def navigate_to(page):
    st.session_state.page_navigation = page


def page_heading(number, heading, description=None):
    st.markdown(
        f"""
        <div style="margin: 12px 0 22px 0;">
            <div style="
                color:#6878d6;
                font-size:11px;
                font-weight:800;
                letter-spacing:2px;
            ">{number}</div>
            <h2 style="margin:5px 0 0 0;">{heading}</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if description:
        st.caption(description)


st.markdown(
    """
    <div class="hero">
        <div class="hero-tag">AUTOMATA THEORY · INTERACTIVE SIMULATOR</div>
        <h1>FINITE STATE MACHINE SIMULATOR</h1>
        <p>
            Design, convert, and compare Mealy and Moore machines
            through interactive transition tables and state diagrams.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


st.radio(
    "Navigation",
    pages,
    horizontal=True,
    key="page_navigation",
    label_visibility="collapsed",
)

current_page = st.session_state.page_navigation

st.divider()


# --------------------------------------------------
# PAGE 01 — MACHINE CONFIGURATION
# --------------------------------------------------

if current_page == pages[0]:

    page_heading(
        "PAGE 01",
        "Machine Configuration",
        "Define the machine type, states, alphabets, and initial state.",
    )

    direction = st.radio(
        "Conversion direction",
        ["Mealy to Moore", "Moore to Mealy"],
        horizontal=True,
        key="machine_direction",
    )

    if (
        st.session_state.machine
        and st.session_state.machine["direction"] != direction
    ):
        st.session_state.machine = None
        st.session_state.transitions = None
        st.session_state.conversion_result = None
        st.session_state.machine_version += 1

    machine = render_configuration(direction)

    if machine is not None:
        st.session_state.machine = machine
        st.session_state.transitions = None
        st.session_state.conversion_result = None
        st.session_state.machine_version += 1

    if st.session_state.machine:

        st.success(
            f"Machine '{st.session_state.machine['name']}' "
            "is configured."
        )

        st.button(
            "Continue to Machine Comparison",
            type="primary",
            use_container_width=True,
            on_click=navigate_to,
            args=(pages[1],),
        )


# --------------------------------------------------
# PAGE 02 — MACHINE COMPARISON
# --------------------------------------------------

elif current_page == pages[1]:

    page_heading(
        "PAGE 02",
        "Machine Comparison",
        "Edit the original machine, convert it, and compare both machines.",
    )

    machine = st.session_state.machine

    if not machine:

        st.warning("Configure a machine on Page 01 first.")

        st.button(
            "Go to Machine Configuration",
            on_click=navigate_to,
            args=(pages[0],),
        )

    else:

        states = machine["states"]
        inputs = machine["inputs"]
        direction = machine["direction"]

        metric1, metric2, metric3, metric4 = st.columns(4)

        metric1.metric("States", len(states))
        metric2.metric("Input Symbols", len(inputs))
        metric3.metric("Machine Type", direction.split(" to ")[0])
        metric4.metric("Initial State", machine["initial_state"])

        st.divider()

        converter = (
            convert_mealy_to_moore
            if direction == "Mealy to Moore"
            else convert_moore_to_mealy
        )

        left, right = st.columns(2, gap="large")

        with left:

            st.markdown("### Original Machine")
            st.caption("Edit the transition table below.")

            edited_transitions = render_transition_table(machine)

            if edited_transitions is not None:

                if edited_transitions != st.session_state.transitions:
                    st.session_state.transitions = edited_transitions
                    st.session_state.conversion_result = None

            original_rows = st.session_state.transitions

            if original_rows:

                st.markdown("#### Original State Diagram")

                original_type = (
                    "mealy"
                    if direction == "Mealy to Moore"
                    else "moore"
                )

                render_state_diagram(
                    original_rows,
                    inputs,
                    machine["initial_state"],
                    original_type,
                    diagram_key="original",
                    layout_states=states,
                )

        with right:

            st.markdown("### Converted Machine")

            result = st.session_state.conversion_result

            if result is None:

                st.info(
                    "The converted transition table and state diagram "
                    "will appear here after conversion."
                )

            else:

                converted_rows = result["rows"]

                st.markdown("#### Converted Transition Table")

                st.dataframe(
                    pd.DataFrame(converted_rows),
                    use_container_width=True,
                    hide_index=True,
                )

                st.markdown("#### Converted State Diagram")

                converted_type = (
                    "moore"
                    if direction == "Mealy to Moore"
                    else "mealy"
                )

                converted_states = [
                    row["State"]
                    for row in converted_rows
                ]

                render_state_diagram(
                    converted_rows,
                    inputs,
                    result["initial_state"],
                    converted_type,
                    diagram_key="converted",
                    layout_states=converted_states,
                )

        st.divider()

        original_rows = st.session_state.transitions

        if not original_rows:

            st.info(
                "Complete the original transition table to enable conversion."
            )

        else:

            if st.button(
                "Convert Machine",
                type="primary",
                use_container_width=True,
                key="convert_machine_button",
            ):

                try:
                    st.session_state.conversion_result = converter(
                        machine,
                        original_rows,
                    )

                    st.rerun()

                except (KeyError, ValueError, IndexError) as error:
                    st.error(f"Conversion failed: {error}")

        if st.session_state.conversion_result is not None:

            st.button(
                "View Summary",
                use_container_width=True,
                on_click=navigate_to,
                args=(pages[2],),
            )


# --------------------------------------------------
# PAGE 03 — SUMMARY
# --------------------------------------------------

else:

    page_heading(
        "PAGE 03",
        "Conversion Summary",
        "Review the machine conversion and test output equivalence.",
    )

    machine = st.session_state.machine
    result = st.session_state.conversion_result
    transitions = st.session_state.transitions

    if not machine:

        st.warning("Configure a machine first.")

    elif not result or not transitions:

        st.warning(
            "Convert the machine on Page 02 before viewing the summary."
        )

        st.button(
            "Go to Machine Comparison",
            on_click=navigate_to,
            args=(pages[1],),
        )

    else:

        original_type = machine["direction"].split(" to ")[0]
        converted_type = result["type"]

        col1, col2, col3 = st.columns(3)

        col1.metric("Original Machine", original_type)
        col2.metric("Converted Machine", converted_type)
        col3.metric("Converted States", len(result["rows"]))

        st.markdown("### Machine Details")

        detail1, detail2 = st.columns(2)

        with detail1:

            st.markdown("**Original Machine**")
            st.write("Name:", machine["name"])
            st.write("Initial state:", machine["initial_state"])
            st.write("States:", ", ".join(machine["states"]))
            st.write("Inputs:", ", ".join(machine["inputs"]))

        with detail2:

            st.markdown("**Converted Machine**")
            st.write("Type:", converted_type)
            st.write("Initial state:", result["initial_state"])
            st.write(
                "States:",
                ", ".join(row["State"] for row in result["rows"]),
            )
            st.write("Inputs:", ", ".join(result["inputs"]))

        st.divider()

        st.markdown("### Converted Transition Table")

        st.dataframe(
            pd.DataFrame(result["rows"]),
            use_container_width=True,
            hide_index=True,
        )

        st.divider()

        render_output_equivalence_test(
            machine,
            transitions,
            result,
        )

        st.divider()

        st.button(
            "Back to Machine Comparison",
            use_container_width=True,
            on_click=navigate_to,
            args=(pages[1],),
        )


st.markdown(
    """
    <div class="footer">
        FINITE STATE MACHINE SIMULATOR · AUTOMATA STUDIO
    </div>
    """,
    unsafe_allow_html=True,
)
