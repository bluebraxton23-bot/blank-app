import streamlit as st

st.set_page_config(
    page_title="Beyond Dispatch AI",
    layout="wide"
)

st.title("🚛 Beyond Dispatch AI")

driver = st.text_input(
    "Driver Name",
    value="Brax"
)

col1, col2 = st.columns(2)

with col1:
    current_city = st.text_input(
        "Current City",
        value="York"
    )

    current_state = st.text_input(
        "Current State",
        value="PA"
    )

with col2:
    home_city = st.text_input(
        "Home City",
        value="York"
    )

    home_state = st.text_input(
        "Home State",
        value="PA"
    )

loads_needed = st.selectbox(
    "Loads Needed",
    [1, 2, 3],
    index=2
)

dispatch_text = st.text_area(
    "Dispatch Dump",
    height=200
)

hotlead_text = st.text_area(
    "Hot Leads",
    height=200
)

offer_text = st.text_area(
    "Offers",
    height=200
)

if st.button("RUN DISPATCH AI"):

    st.success("System Ready")

    st.write(
        f"Driver: {driver}"
    )

    st.write(
        f"Current Location: "
        f"{current_city}, {current_state}"
    )

    st.write(
        f"Loads Needed: "
        f"{loads_needed}"
    )


    