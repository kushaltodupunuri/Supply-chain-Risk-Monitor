import math
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from src.ui_helpers import inject_shared_css, cards_grid, metric_card_html

st.set_page_config(page_title="Logistics & Route Optimizer - SupplyIQ", page_icon="🚚", layout="wide")
inject_shared_css()

st.title("🚚 Logistics & Route Optimizer")
st.caption("Find the Fastest, Cheapest Way to Get Your Product to Your Customer")

st.warning(
    "⚠️ **No carrier API is wired up here.** Real FedEx/UPS/USPS/DHL rate quotes require a "
    "business shipping account with each carrier, not a free public API. The cost model below "
    "is a hand-built approximation reflecting each carrier's typical relative pricing pattern "
    "(USPS cheaper for light/short-zone, DHL stronger for distance/international, etc.) - useful "
    "for comparing *relative* options, not a real quote. Swap in your actual negotiated rates for "
    "a precise number."
)

# Approximate lat/lon for major shipping hubs - real coordinates, used for a real Haversine
# distance calculation, which is the one part of this module that's not an approximation.
CITY_COORDS = {
    "New York, NY": (40.71, -74.01), "Los Angeles, CA": (34.05, -118.24), "Chicago, IL": (41.88, -87.63),
    "Houston, TX": (29.76, -95.37), "Phoenix, AZ": (33.45, -112.07), "Philadelphia, PA": (39.95, -75.17),
    "San Antonio, TX": (29.42, -98.49), "San Diego, CA": (32.72, -117.16), "Dallas, TX": (32.78, -96.80),
    "Austin, TX": (30.27, -97.74), "Seattle, WA": (47.61, -122.33), "Denver, CO": (39.74, -104.99),
    "Atlanta, GA": (33.75, -84.39), "Miami, FL": (25.76, -80.19), "Boston, MA": (42.36, -71.06),
    "Toronto, ON": (43.65, -79.38), "London, UK": (51.51, -0.13), "Mexico City, MX": (19.43, -99.13),
}

CARRIERS = {
    "USPS": {"base": 4.50, "per_lb": 0.45, "per_100mi": 0.15, "express_mult": 2.2, "overnight_mult": 4.5},
    "FedEx": {"base": 7.00, "per_lb": 0.55, "per_100mi": 0.10, "express_mult": 1.8, "overnight_mult": 3.2},
    "UPS": {"base": 7.20, "per_lb": 0.52, "per_100mi": 0.11, "express_mult": 1.85, "overnight_mult": 3.3},
    "DHL": {"base": 9.00, "per_lb": 0.60, "per_100mi": 0.08, "express_mult": 1.5, "overnight_mult": 2.8},
}

CARBON_KG_PER_LB_MILE = 0.0002  # rough illustrative ground-freight emissions factor


def haversine_miles(coord1, coord2):
    lat1, lon1, lat2, lon2 = map(math.radians, [*coord1, *coord2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * 3958.8 * math.asin(math.sqrt(a))


def estimate_cost(carrier, distance_miles, weight_lbs, service_level):
    c = CARRIERS[carrier]
    base_cost = c["base"] + weight_lbs * c["per_lb"] + (distance_miles / 100) * c["per_100mi"]
    mult = {"Standard": 1.0, "Express": c["express_mult"], "Overnight": c["overnight_mult"]}[service_level]
    return base_cost * mult


st.markdown("**Step 1: Your origin and shipment profile**")
col1, col2, col3 = st.columns(3)
with col1:
    origin = st.selectbox("Warehouse / origin location", list(CITY_COORDS.keys()), index=2)
with col2:
    avg_weight = st.number_input("Average package weight (lbs)", min_value=0.1, value=2.5, step=0.5)
with col3:
    service_level = st.selectbox("Delivery time requirement", ["Standard", "Express", "Overnight"])

st.markdown("**Step 2: Your customer destinations**")
DEMO_DESTINATIONS = pd.DataFrame([
    {"City": "Chicago, IL", "Monthly Orders": 50, "Current Cost/Delivery ($)": 7.50},
    {"City": "Chicago, IL", "Monthly Orders": 30, "Current Cost/Delivery ($)": 7.50},
    {"City": "Los Angeles, CA", "Monthly Orders": 40, "Current Cost/Delivery ($)": 9.00},
    {"City": "New York, NY", "Monthly Orders": 60, "Current Cost/Delivery ($)": 8.20},
    {"City": "Houston, TX", "Monthly Orders": 25, "Current Cost/Delivery ($)": 6.80},
])
dest_df = st.data_editor(
    st.session_state.get("dest_df", DEMO_DESTINATIONS),
    num_rows="dynamic", width="stretch", key="dest_editor",
    column_config={"City": st.column_config.SelectboxColumn(options=list(CITY_COORDS.keys()))},
)
st.session_state["dest_df"] = dest_df
dest_df = dest_df.dropna(subset=["City"])
dest_df = dest_df[dest_df["City"].isin(CITY_COORDS)]

if dest_df.empty:
    st.info("Add at least one destination city above.")
    st.stop()

origin_coord = CITY_COORDS[origin]
rows = []
for _, row in dest_df.iterrows():
    dest_coord = CITY_COORDS[row["City"]]
    distance = haversine_miles(origin_coord, dest_coord)
    costs = {carrier: estimate_cost(carrier, distance, avg_weight, service_level) for carrier in CARRIERS}
    best_carrier = min(costs, key=costs.get)
    rows.append({
        "City": row["City"], "Monthly Orders": row["Monthly Orders"], "Distance (mi)": round(distance),
        "Current Cost/Delivery ($)": row.get("Current Cost/Delivery ($)", None),
        "Best Carrier": best_carrier, "Best Cost/Delivery ($)": round(costs[best_carrier], 2),
        **{f"{c} ($)": round(v, 2) for c, v in costs.items()},
    })
result_df = pd.DataFrame(rows)

st.markdown("---")
st.markdown("### Carrier Comparison")
st.dataframe(
    result_df[["City", "Monthly Orders", "Distance (mi)", "USPS ($)", "FedEx ($)", "UPS ($)", "DHL ($)", "Best Carrier"]],
    width="stretch", hide_index=True,
)

result_df["Optimized Monthly Cost"] = result_df["Monthly Orders"] * result_df["Best Cost/Delivery ($)"]
has_current = result_df["Current Cost/Delivery ($)"].notna().any()
if has_current:
    result_df["Current Monthly Cost"] = result_df["Monthly Orders"] * result_df["Current Cost/Delivery ($)"].fillna(result_df["Best Cost/Delivery ($)"])
    total_current = result_df["Current Monthly Cost"].sum()
    total_optimized = result_df["Optimized Monthly Cost"].sum()
    savings = total_current - total_optimized
else:
    total_current = total_optimized = savings = None

total_distance_weighted = (result_df["Monthly Orders"] * result_df["Distance (mi)"]).sum()
carbon_kg = total_distance_weighted * avg_weight * CARBON_KG_PER_LB_MILE

cards = [
    metric_card_html("Optimized Monthly Shipping Cost", f"${total_optimized:,.0f}",
                      "Across all destinations, using the cheapest carrier per route", "#4F46E5"),
]
if savings is not None:
    cards.append(metric_card_html(
        "Estimated Monthly Savings", f"${savings:,.0f}",
        f"vs. your entered current cost (${total_current:,.0f}/mo)",
        "#2ECC71" if savings > 0 else "#94A3B8",
    ))
cards.append(metric_card_html("Estimated Carbon Footprint", f"{carbon_kg:,.0f} kg CO2/mo",
                               "Rough estimate based on distance x weight", "#F39C12"))
st.markdown(cards_grid(cards), unsafe_allow_html=True)

# Consolidation: same city appearing in more than one row means separate shipment
# batches that could likely be combined into fewer, larger shipments.
st.markdown("---")
st.markdown("### Consolidation Opportunities")
city_counts = dest_df.groupby("City").size()
dupe_cities = city_counts[city_counts > 1]
if len(dupe_cities) > 0:
    for city in dupe_cities.index:
        rows_for_city = result_df[result_df["City"] == city]
        combined_orders = rows_for_city["Monthly Orders"].sum()
        separate_cost = rows_for_city["Optimized Monthly Cost"].sum()
        consolidated_cost = combined_orders * rows_for_city["Best Cost/Delivery ($)"].iloc[0] * 0.85  # ~15% volume discount, illustrative
        st.info(
            f"📦 **{city}**: {len(rows_for_city)} separate shipment batches totaling {combined_orders:.0f} "
            f"orders/month. Consolidating into one shipment plan could save an estimated "
            f"**${separate_cost - consolidated_cost:,.0f}/month** (assumes a ~15% volume discount, "
            f"a placeholder for whatever your real carrier discount tier offers)."
        )
else:
    st.caption("No destination appears more than once - no obvious consolidation opportunity in this data.")

st.markdown("---")
st.markdown("### Cost by Destination")
by_city = result_df.groupby("City", as_index=False).agg(
    **{"Optimized Monthly Cost": ("Optimized Monthly Cost", "sum")}
)
by_city["Best Carrier"] = by_city["City"].map(
    result_df.groupby("City")["Best Carrier"].first()
)
fig = go.Figure(go.Bar(
    x=by_city["City"], y=by_city["Optimized Monthly Cost"],
    marker_color="#4F46E5", text=by_city["Best Carrier"], textposition="outside",
))
fig.update_layout(
    height=320, margin=dict(t=20, b=10, l=10, r=10),
    yaxis=dict(title="Optimized Monthly Cost ($)"),
    font=dict(family="Inter, sans-serif", color="#1E293B"),
    plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
)
st.plotly_chart(fig, use_container_width=True)
