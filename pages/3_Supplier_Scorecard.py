import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from src.ui_helpers import inject_shared_css, get_health_color, cards_grid, metric_card_html

inject_shared_css()

st.title("📋 Supplier Performance Scorecard")
st.caption("Know Which Suppliers Are Helping You and Which Are Hurting You")

st.markdown(
    "Edit the table below (add rows for your own suppliers, or just tweak the demo "
    "rows), or upload a CSV with the same columns. All scores update live."
)

DEMO_SUPPLIERS = pd.DataFrame([
    {"Supplier": "Supplier A (Vietnam)", "On-Time Delivery %": 94, "Defect Rate %": 6.0,
     "Price Variance %": 4, "Lead Time Reliability %": 88, "Communication (1-5)": 4,
     "Monthly Orders": 40},
    {"Supplier": "Supplier B (China)", "On-Time Delivery %": 82, "Defect Rate %": 2.0,
     "Price Variance %": 9, "Lead Time Reliability %": 75, "Communication (1-5)": 3,
     "Monthly Orders": 60},
    {"Supplier": "Supplier C (Domestic)", "On-Time Delivery %": 97, "Defect Rate %": 1.0,
     "Price Variance %": 2, "Lead Time Reliability %": 95, "Communication (1-5)": 5,
     "Monthly Orders": 20},
])

WEIGHTS = {
    "On-Time Delivery %": 0.30, "Defect Rate %": 0.25, "Price Variance %": 0.15,
    "Lead Time Reliability %": 0.20, "Communication (1-5)": 0.10,
}

uploaded = st.file_uploader("Or upload a CSV with the same columns", type=["csv"])
if uploaded is not None:
    try:
        base_df = pd.read_csv(uploaded)
    except Exception as e:
        st.error(f"Couldn't read that file: {e}")
        base_df = DEMO_SUPPLIERS
else:
    base_df = st.session_state.get("supplier_df", DEMO_SUPPLIERS)

edited = st.data_editor(base_df, num_rows="dynamic", width="stretch", key="supplier_editor")
st.session_state["supplier_df"] = edited

required_cols = {"Supplier", "On-Time Delivery %", "Defect Rate %", "Price Variance %",
                  "Lead Time Reliability %", "Communication (1-5)", "Monthly Orders"}
missing = required_cols - set(edited.columns)
if missing:
    st.error(f"Missing columns: {', '.join(missing)}")
    st.stop()

df = edited.dropna(subset=["Supplier"]).copy()
if df.empty:
    st.info("Add at least one supplier row above.")
    st.stop()


def score_supplier(row):
    on_time = max(0, min(100, row["On-Time Delivery %"]))
    defect_score = max(0, 100 - row["Defect Rate %"] * 10)       # 10% defects -> 0
    price_score = max(0, 100 - row["Price Variance %"] * 8)       # 12.5% variance -> 0
    lead_time = max(0, min(100, row["Lead Time Reliability %"]))
    comm_score = max(0, min(100, row["Communication (1-5)"] / 5 * 100))
    composite = (
        on_time * WEIGHTS["On-Time Delivery %"]
        + defect_score * WEIGHTS["Defect Rate %"]
        + price_score * WEIGHTS["Price Variance %"]
        + lead_time * WEIGHTS["Lead Time Reliability %"]
        + comm_score * WEIGHTS["Communication (1-5)"]
    )
    return round(composite, 1)


def grade(score):
    if score >= 90: return "A"
    elif score >= 80: return "B"
    elif score >= 70: return "C"
    elif score >= 60: return "D"
    return "F"


df["Score"] = df.apply(score_supplier, axis=1)
df["Grade"] = df["Score"].apply(grade)
df = df.sort_values("Score", ascending=False).reset_index(drop=True)

st.markdown("---")
st.markdown("### Scorecard")
st.markdown(
    cards_grid([
        metric_card_html(
            row["Supplier"],
            f"{row['Score']} <span style='font-size:16px;'>({row['Grade']})</span>",
            f"{row['On-Time Delivery %']:.0f}% on-time, {row['Defect Rate %']:.1f}% defect rate",
            get_health_color(row["Score"]),
        )
        for _, row in df.iterrows()
    ]),
    unsafe_allow_html=True,
)

fig = go.Figure(go.Bar(
    x=df["Score"], y=df["Supplier"], orientation="h",
    marker_color=[get_health_color(s) for s in df["Score"]],
    text=df["Grade"], textposition="outside",
))
fig.update_layout(
    height=max(220, 60 * len(df)), margin=dict(t=10, b=10, l=10, r=30),
    xaxis=dict(title="Score", range=[0, 105]),
    yaxis=dict(autorange="reversed"),
    font=dict(family="Inter, sans-serif", color="#1E293B"),
    plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.markdown("### Cost of Poor Performance")
st.caption(
    "These are estimates based on adjustable assumptions below, not measured costs - "
    "tune them to match your real expediting/rework costs for a more accurate number."
)
col_a, col_b = st.columns(2)
with col_a:
    cost_per_late = st.number_input("Estimated cost per late delivery ($)", min_value=0, value=60, step=5)
with col_b:
    cost_per_defect_pct = st.number_input("Estimated cost per 1% defect rate, per month ($)", min_value=0, value=40, step=5)

cost_rows = []
for _, row in df.iterrows():
    late_orders = row["Monthly Orders"] * (1 - row["On-Time Delivery %"] / 100)
    late_cost = late_orders * cost_per_late
    defect_cost = row["Defect Rate %"] * cost_per_defect_pct
    cost_rows.append({"Supplier": row["Supplier"], "Est. Monthly Cost": round(late_cost + defect_cost)})

cost_df = pd.DataFrame(cost_rows).sort_values("Est. Monthly Cost", ascending=False)
total_cost = cost_df["Est. Monthly Cost"].sum()

st.markdown(
    cards_grid([
        metric_card_html("Total Estimated Monthly Cost", f"${total_cost:,.0f}",
                          "Across all suppliers, from late deliveries + defects", "#E74C3C"),
    ] + [
        metric_card_html(row["Supplier"], f"${row['Est. Monthly Cost']:,.0f}/mo", None, "#F39C12")
        for _, row in cost_df.iterrows()
    ]),
    unsafe_allow_html=True,
)

worst = df.iloc[-1]
if worst["Grade"] in ("D", "F"):
    st.error(
        f"🔴 **Recommendation:** Consider replacing **{worst['Supplier']}** (Grade {worst['Grade']}, "
        f"score {worst['Score']}). When evaluating an alternative, prioritize whichever of "
        f"on-time delivery, defect rate, or price consistency is weakest here."
    )
