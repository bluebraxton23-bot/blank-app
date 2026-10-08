import streamlit as st
import pandas as pd
import numpy as np
import requests
import re

CURRENT_DIESEL_PRICE = 6.382

MPG = 7.5

DRIVER_RATE = 0.70

OVERHEAD_COST = 229.00

INSURANCE_COST = 79.00

@st.cache_data
def get_coordinates(city, state):

    query = f"{city}, {state}"

    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": query,
        "format": "json",
        "limit": 1
    }

    headers = {
        "User-Agent": "BeyondDispatch"
    }

    try:

        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=10
        )

        data = response.json()

        if not data:

            st.write(
                f"❌ No coordinates found for {city}, {state}"
            )

            return None

        return (
            float(data[0]["lat"]),
            float(data[0]["lon"])
        )

    except Exception as e:

        st.write(
            f"❌ Coordinate lookup failed for {city}, {state}: {e}"
        )

        return None

from math import (
    radians,
    sin,
    cos,
    sqrt,
    atan2
)
def distance_miles(
    lat1,
    lon1,
    lat2,
    lon2
):

    earth_radius = 3958.8

    dlat = radians(
        lat2 - lat1
    )

    dlon = radians(
        lon2 - lon1
    )

    a = (
        sin(dlat / 2) ** 2
        +
        cos(radians(lat1))
        *
        cos(radians(lat2))
        *
        sin(dlon / 2) ** 2
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )

    return (
        earth_radius * c
    )
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

    route_home = st.checkbox(
        "🏠 Route Toward Home"
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

def calculate_fuel_cost(miles):

    return round(
        (miles / MPG)
        * CURRENT_DIESEL_PRICE,
        2
    )
def build_offer_profitability(offer_df):

    offers = offer_df.copy()

    offers["Miles"] = offers["MI"]

    offers["Revenue"] = offers["Rate"]

    offers["Fuel Cost"] = (
        offers["Miles"].apply(
            calculate_fuel_cost
        )
    )

    offers["Driver Cost"] = (
        offers["Miles"] * DRIVER_RATE
    )

    offers["Operating Cost"] = (
        OVERHEAD_COST
        +
        INSURANCE_COST
        +
        300
    )

    offers["Total Cost"] = (
        offers["Fuel Cost"]
        +
        offers["Driver Cost"]
        +
        offers["Operating Cost"]
    )

    offers["Pocket"] = (
        offers["Revenue"]
        -
        offers["Total Cost"]
    )

    def recommendation(pocket):

        if pocket >= 500:
            return "TAKE IT"

        if pocket >= 300:
            return "ACCEPTABLE"

        if pocket > 0:
            return "MARGINAL"

        return "DECLINE"

    offers["Recommendation"] = (
        offers["Pocket"]
        .apply(recommendation)
    )

    offers["Pocket 300 Bid"] = (
        offers["Total Cost"] + 300
    )

    offers["Pocket 500 Bid"] = (
        offers["Total Cost"] + 500
    )

    return offers
def build_three_leg_route(
    profit_df,
    start_city,
    start_state,
    home_city=None,
    home_state=None,
    route_home=False
):

    route = []

    remaining = profit_df.copy()

    origin_city = start_city
    origin_state = start_state

    st.write(
        f"Route Home = {route_home}"
    )

    if route_home:

        st.write(
            f"Home Destination = {home_city}, {home_state}"
        )

    for _ in range(min(3, len(remaining))):

        origin_coords = get_coordinates(
            origin_city,
            origin_state
        )

        scores = []

        for _, row in remaining.iterrows():

            load_coords = get_coordinates(
                row["CITY"],
                row["ST"]
            )

            if origin_coords and load_coords:

                distance = distance_miles(
                    origin_coords[0],
                    origin_coords[1],
                    load_coords[0],
                    load_coords[1]
                )

            else:

                distance = 9999

            score = (
                row["Pocket"]
                -
                (distance * 0.25)
            )

            if route_home and len(route) == 2:

                home_coords = get_coordinates(
                    home_city,
                    home_state
                )

                if home_coords and load_coords:

                    distance_home = distance_miles(
                        load_coords[0],
                        load_coords[1],
                        home_coords[0],
                        home_coords[1]
                    )

                    score = (
                        score
                        -
                        (distance_home * 0.10)
                    )

            scores.append(
                score
            )

        remaining["Route Score"] = scores
        st.write(
            f"Current Origin: {origin_city}, {origin_state}"
        )

        st.dataframe(
            remaining[
                [
                    "CITY",
                    "ST",
                    "Pocket",
                    "Route Score"
                ]
            ].sort_values(
                by="Route Score",
                ascending=False
            )
        )

        best_idx = (
            remaining["Route Score"]
            .idxmax()
        )

        best_load = remaining.loc[
            best_idx
        ]

        route.append(
            best_load
        )

        origin_city = (
            best_load["CITY"]
        )

        origin_state = (
            best_load["ST"]
        )

        remaining = (
            remaining.drop(best_idx)
        )

    return pd.DataFrame(
        route
    )       

if st.button("RUN DISPATCH AI"):

    dispatch_df = pd.DataFrame()

    hotlead_df = pd.DataFrame()

    offer_df = pd.DataFrame()

    if dispatch_text:

        dispatch_df = parse_dispatch_dump(
            dispatch_text
        )

    if hotlead_text:

        hotlead_df = parse_hot_leads(
            hotlead_text
        )

    if offer_text:

        offer_df = parse_offer_list(
            offer_text
        )

        profit_df = build_offer_profitability(
            offer_df
        )

        current_coords = get_coordinates(
            current_city,
            current_state
        )

        distances = []

        for _, row in profit_df.iterrows():

            load_coords = get_coordinates(
                row["CITY"],
                row["ST"]
            )

            if current_coords and load_coords:

                miles = distance_miles(
                    current_coords[0],
                    current_coords[1],
                    load_coords[0],
                    load_coords[1]
                )

            else:

                miles = 9999

            distances.append(
                round(miles)
            )

        profit_df["Distance From Current"] = (
            distances
        )

        profit_df["Dispatch Score"] = (
            profit_df["Pocket"]
            -
            (
                profit_df["Distance From Current"]
                * 0.50
            )
        )

        st.subheader(
            "PROFITABILITY ANALYSIS"
        )

        st.subheader(
            "🏆 TOP RECOMMENDATIONS"
        )

        for _, row in profit_df.sort_values(
            by="Dispatch Score",
            ascending=False
        ).head(1).iterrows():

            st.success(
                f"{row['CITY']}, "
                f"{row['ST']} | "
                f"Pocket: ${row['Pocket']:,.0f} | "
                f"{row['Recommendation']}"
            )

        st.subheader(
            "🚛 BEST 3-LOAD SEQUENCE"
        )

        best_three = build_three_leg_route(
    profit_df,
    current_city,
    current_state,
    home_city,
    home_state,
    route_home
)

        total_pocket = (
            best_three["Pocket"]
            .sum()
        )

        st.write("LEG 1")

        st.success(
            f"{best_three.iloc[0]['CITY']}, "
            f"{best_three.iloc[0]['ST']} | "
            f"Pocket ${best_three.iloc[0]['Pocket']:,.0f}"
        )

        st.write("LEG 2")

        st.success(
            f"{best_three.iloc[1]['CITY']}, "
            f"{best_three.iloc[1]['ST']} | "
            f"Pocket ${best_three.iloc[1]['Pocket']:,.0f}"
        )

        st.write("LEG 3")

        st.success(
            f"{best_three.iloc[2]['CITY']}, "
            f"{best_three.iloc[2]['ST']} | "
            f"Pocket ${best_three.iloc[2]['Pocket']:,.0f}"
        )

        st.subheader(
            f"💰 TOTAL POCKET: ${total_pocket:,.0f}"
        )

        st.dataframe(
            profit_df
        )

    master_df = build_master_load_pool(
        dispatch_df,
        hotlead_df,
        offer_df
    )

    st.subheader(
        "MASTER LOAD POOL"
    )

    st.dataframe(
        master_df,
        use_container_width=True
    )

    st.success(
        "Dispatch AI Running"
    )
