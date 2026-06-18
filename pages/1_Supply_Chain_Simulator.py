import streamlit as st
import plotly.graph_objects as go

from src.ui_helpers import inject_shared_css, get_health_color, get_health_label, metric_card_html, cards_grid

st.set_page_config(page_title="Supply Chain Simulator - SupplyIQ", page_icon="🧭", layout="wide")
inject_shared_css()

st.title("🧭 Supply Chain Simulator")
st.caption("Build Your Supply Chain in 5 Minutes")

st.markdown(
    "Answer 5 quick questions and see your supply chain visualized end to end - "
    "probably for the first time. The health scores below are a simple, transparent "
    "heuristic based on what you enter here (not live data), meant to give you a "
    "starting mental model, not a precise audit."
)

PRODUCT_CATEGORIES = [
    "Food & Beverage", "Apparel & Accessories", "Electronics", "Handmade / Craft Goods",
    "Health & Beauty", "Home Goods", "Other",
]
SOURCING_REGIONS = ["Local / Domestic", "Regional (same continent)", "International (overseas)"]
CUSTOMER_REACH = ["Local", "National", "International"]


def compute_node_health(num_suppliers, sourcing_region, customer_reach, monthly_volume):
    if num_suppliers <= 1:
        supplier_score, supplier_why = 25, "Single-source dependency - one disruption stops everything"
    elif num_suppliers <= 3:
        supplier_score, supplier_why = 55, "Some diversification, but still a small supplier base"
    else:
        supplier_score, supplier_why = 85, "Diversified supplier base"

    if sourcing_region == "Local / Domestic":
        manufacturing_score, manufacturing_why = 80, "Local sourcing - shorter lead times, less customs complexity"
    elif sourcing_region == "Regional (same continent)":
        manufacturing_score, manufacturing_why = 60, "Regional sourcing - moderate lead time and complexity"
    else:
        manufacturing_score, manufacturing_why = 45, "Overseas sourcing - longer lead times, customs/tariff exposure"

    if monthly_volume < 500:
        warehouse_score, warehouse_why = 85, "Low volume - manageable with simple storage"
    elif monthly_volume < 5000:
        warehouse_score, warehouse_why = 65, "Moderate volume - storage/fulfillment starts to need real process"
    else:
        warehouse_score, warehouse_why = 45, "High volume - likely outgrowing ad hoc storage/fulfillment"

    distribution_map = {
        "Local": (85, "Local delivery - short, simple, cheap"),
        "National": (60, "National shipping - more carriers/zones to manage"),
        "International": (40, "International shipping - customs, duties, longer transit"),
    }
    distribution_score, distribution_why = distribution_map[customer_reach]

    customer_score = round((supplier_score + manufacturing_score + warehouse_score + distribution_score) / 4)
    customer_why = "Reflects the average health of every upstream stage - risk passed through to customer experience"

    return {
        "Supplier": (supplier_score, supplier_why),
        "Manufacturing": (manufacturing_score, manufacturing_why),
        "Warehouse": (warehouse_score, warehouse_why),
        "Distribution": (distribution_score, distribution_why),
        "Customer": (customer_score, customer_why),
    }


with st.form("simulator_form"):
    col1, col2 = st.columns(2)
    with col1:
        product = st.selectbox("What do you sell?", PRODUCT_CATEGORIES)
        sourcing_region = st.selectbox("Where do you source from?", SOURCING_REGIONS)
        num_suppliers = st.number_input("How many suppliers do you have?", min_value=1, max_value=50, value=2)
    with col2:
        customer_reach = st.selectbox("Where are your customers?", CUSTOMER_REACH)
        monthly_volume = st.number_input("How much do you sell per month? (units)", min_value=1, value=500, step=50)
    submitted = st.form_submit_button("Build My Supply Chain", type="primary", width="stretch")

if submitted:
    st.session_state["sim_result"] = {
        "product": product, "sourcing_region": sourcing_region, "num_suppliers": num_suppliers,
        "customer_reach": customer_reach, "monthly_volume": monthly_volume,
        "health": compute_node_health(num_suppliers, sourcing_region, customer_reach, monthly_volume),
    }

if "sim_result" in st.session_state:
    result = st.session_state["sim_result"]
    health = result["health"]
    nodes = ["Supplier", "Manufacturing", "Warehouse", "Distribution", "Customer"]

    st.markdown("---")
    st.markdown(f"### Your Supply Chain — {result['product']}")

    node_colors = [get_health_color(health[n][0]) for n in nodes]
    fig = go.Figure(
        go.Sankey(
            node=dict(label=nodes, color=node_colors, pad=30, thickness=30, line=dict(color="white", width=1)),
            link=dict(
                source=[0, 1, 2, 3],
                target=[1, 2, 3, 4],
                value=[result["monthly_volume"]] * 4,
                color="rgba(148,163,184,0.35)",
            ),
        )
    )
    fig.update_layout(
        height=320, margin=dict(t=30, b=10, l=10, r=10),
        font=dict(family="Inter, sans-serif", size=14, color="#1E293B"),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        cards_grid([
            metric_card_html(
                stage,
                f"{score} <span style='font-size:14px;'>({get_health_label(score)})</span>",
                why,
                get_health_color(score),
            )
            for stage, (score, why) in health.items()
        ]),
        unsafe_allow_html=True,
    )
else:
    st.info("Fill in the form above and click \"Build My Supply Chain\" to see your visualization.")
