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

def parse_dispatch_dump(text):

    loads = []

    load_ids = re.findall(
        r'\b(36\d{6})\b',
        text
    )

    destinations = re.findall(
        r'-->\s*([A-Z ]+),\s*([A-Z]{2})',
        text
    )

    count = min(
        len(load_ids),
        len(destinations)
    )

    for i in range(count):

        try:

            destination_city = (
                destinations[i][0]
                .strip()
                .title()
            )

            destination_state = (
                destinations[i][1]
                .strip()
            )

            loads.append({

                "Load ID":
                    load_ids[i],

                "Origin City":
                    "Chillicothe",

                "Origin State":
                    "OH",

                "Destination City":
                    destination_city,

                "Destination State":
                    destination_state,

                "Loaded Miles":
                    None

            })

        except:

            pass

    return pd.DataFrame(loads)

     

       
def parse_hot_leads(text):

    loads = []

    for line in text.splitlines():

        if "~" not in line:
            continue

        try:

            left, right = line.split("~")

            origin_match = re.search(
                r'(.+?),\s*([A-Z]{2})',
                left.strip()
            )

            dest_match = re.search(
                r'(.+?),\s*([A-Z]{2})',
                right.strip()
            )

            if not origin_match:
                continue

            if not dest_match:
                continue

            loads.append({

                "Origin City":
                    origin_match.group(1)
                    .replace("1 ", "")
                    .strip()
                    .title(),

                "Origin State":
                    origin_match.group(2),

                "Destination City":
                    dest_match.group(1)
                    .strip()
                    .title(),

                "Destination State":
                    dest_match.group(2)

            })

        except:

            pass

    return pd.DataFrame(loads)

def build_master_load_pool(
    dispatch_df,
    hotlead_df,
    offer_df
):

    dispatch = dispatch_df.copy()

    if not dispatch.empty:

        dispatch["Source"] = "Dispatch"

        dispatch = dispatch[
            [
                "Destination City",
                "Destination State",
                "Source"
            ]
        ]

    hotleads = hotlead_df.copy()

    if not hotleads.empty:

        hotleads["Source"] = "Hot Lead"

        hotleads = hotleads[
            [
                "Destination City",
                "Destination State",
                "Source"
            ]
        ]

    offers = offer_df.copy()

    if not offers.empty:

        offers["Source"] = "Offer"

        offers = offers.rename(
            columns={
                "CITY": "Destination City",
                "ST": "Destination State"
            }
        )

        offers = offers[
            [
                "Destination City",
                "Destination State",
                "Source"
            ]
        ]

    master_df = pd.concat(
        [
            dispatch,
            hotleads,
            offers
        ],
        ignore_index=True
    )

    return master_df

if st.button("RUN DISPATCH AI"):
    dispatch_df = pd.DataFrame()

    hotlead_df = pd.DataFrame()

    offer_df = pd.DataFrame()

if dispatch_text:

        dispatch_df = (
            parse_dispatch_dump(
                dispatch_text
            )
        )

if hotlead_text:

        hotlead_df = (
            parse_hot_leads(
                hotlead_text
            )
        )       
if offer_text:

        offer_df = (
            parse_offer_list(
                offer_text
            )
        )
master_df = (
        build_master_load_pool(
            dispatch_df,
            hotlead_df,
            offer_df
        )
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
if dispatch_text:

    dispatch_df = parse_dispatch_dump(
        dispatch_text
    )

    st.subheader(
        "Dispatch Loads"
    )

    st.dataframe(
        dispatch_df,
        use_container_width=True
    )

if hotlead_text:

        hotlead_df = parse_hot_leads(
            hotlead_text
        )

        st.subheader(
            "Hot Leads"
        )

        st.dataframe(
            hotlead_df,
            use_container_width=True
        )

def build_master_load_pool(
    dispatch_df,
    hotlead_df,
    offer_df
):

    dispatch = dispatch_df.copy()

    if not dispatch.empty:

        dispatch["Source"] = "Dispatch"

        dispatch = dispatch[
            [
                "Destination City",
                "Destination State",
                "Source"
            ]
        ]

    hotleads = hotlead_df.copy()

    if not hotleads.empty:

        hotleads["Source"] = "Hot Lead"

        hotleads = hotleads[
            [
                "Destination City",
                "Destination State",
                "Source"
            ]
        ]

    offers = offer_df.copy()

    if not offers.empty:

        offers["Source"] = "Offer"

        offers = offers.rename(
            columns={
                "CITY":
                    "Destination City",
                "ST":
                    "Destination State"
            }
        )

        offers = offers[
            [
                "Destination City",
                "Destination State",
                "Source"
            ]
        ]

    master_df = pd.concat(
        [
            dispatch,
            hotleads,
            offers
        ],
        ignore_index=True
    )

    return master_df
    st.subheader(
        "MASTER LOAD POOL"
    )

st.dataframe(
        master_df,
        use_container_width=True
    )