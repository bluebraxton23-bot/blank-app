import streamlit as st
import streamlit as st
import pandas as pd
import numpy as np
import requests
import re


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

def parse_offer_list(text):

    VALID_STATES = {
        "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA",
        "HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
        "MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
        "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC",
        "SD","TN","TX","UT","VT","VA","WA","WV","WI","WY"
    }

    rows = []

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        if "VIN" in line.upper() and "RATE" in line.upper():
            continue

        line = re.sub(r"\s+", " ", line)

        try:

            rate_match = re.search(
                r"\$([\d,]+(?:\.\d+)?)",
                line
            )

            if not rate_match:
                continue

            rate = float(
                rate_match.group(1).replace(",", "")
            )

            line = line.replace(
                rate_match.group(0),
                ""
            )

            parts = line.split()

            vin = parts[0]

            miles = float(parts[1])

            state_idx = None

            for i in range(2, len(parts)):

                if parts[i] in VALID_STATES:

                    state_idx = i
                    break

            if state_idx is None:
                continue

            destination = " ".join(
                parts[2:state_idx]
            )

            state = parts[state_idx]

            fifth_wheel = parts[-1]

            city = " ".join(
                parts[state_idx + 1:-1]
            )

            rows.append({

                "VIN": vin,
                "MI": miles,
                "Destination": destination,
                "ST": state,
                "CITY": city,
                "5th Wheel": fifth_wheel,
                "Rate": rate

            })

        except Exception as e:

            print("Parse Error:", e)

    return pd.DataFrame(rows)

if st.button("RUN DISPATCH AI"):

    if offer_text:

        offer_df = parse_offer_list(
            offer_text
        )

        st.success(
            f"Offers Parsed: {len(offer_df)}"
        )

        st.dataframe(
            offer_df
        )

    st.success("Dispatch AI Running")

    st.write(
        f"Driver: {driver}"
    )

    st.write(
        f"Current Location: "
        f"{current_city}, {current_state}"
    )

    st.write(
        f"Home Location: "
        f"{home_city}, {home_state}"
    )

    st.write(
        f"Loads Requested: "
        f"{loads_needed}"
    )

    st.write(
        f"Dispatch Rows: "
        f"{len(dispatch_text.splitlines())}"
    )

    st.write(
        f"Hot Lead Rows: "
        f"{len(hotlead_text.splitlines())}"
    )

    st.write(
        f"Offer Rows: "
        f"{len(offer_text.splitlines())}"
    )
