import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from src.ui_helpers import inject_shared_css, get_health_color, cards_grid, metric_card_html

st.set_page_config(page_title="Executive Dashboard - SupplyIQ", page_icon="🏠", layout="wide")
inject_shared_css()

st.title("🏠 Executive Dashboard")
st.caption("Your Entire Supply Chain. One Screen.")

sim_result = st.session_state.get("sim_result")
forecast_result = st.session_state.get("forecast_result")
supplier_df_raw = st.session_state.get("supplier_df")
supplier_df = supplier_df_raw.dropna(subset=["Supplier"]) if supplier_df_raw is not None else None
cost_result = st.session_state.get("cost_optimization_result")

missing = []
if sim_result is None: missing.append("Supply Chain Simulator")
if forecast_result is None: missing.append("Demand Forecasting")
if supplier_df is None or len(supplier_df) == 0: missing.append("Supplier Scorecard")
if cost_result is None: missing.append("Cost Optimization")
if missing:
    st.info(f"Some sections below are empty until you visit: {', '.join(missing)}. Everything fills in live as you use those pages.")

st.markdown("---")

# --- Top row: 4 headline numbers ---
health_score = None
if sim_result:
    health_score = round(sum(v[0] for v in sim_result["health"].values()) / len(sim_result["health"]))

savings = cost_result["total_savings"] if cost_result else None
accuracy = forecast_result["forecast_accuracy_pct"] if forecast_result else None
on_time_rate = (supplier_df["On-Time Delivery %"] * supplier_df["Monthly Orders"]).sum() / supplier_df["Monthly Orders"].sum() if supplier_df is not None and len(supplier_df) else None

st.markdown(
    cards_grid([
        metric_card_html("Overall Supply Chain Health", f"{health_score}/100" if health_score is not None else "—",
                          "From the Supply Chain Simulator" if health_score is not None else "Visit Supply Chain Simulator",
                          get_health_color(health_score) if health_score is not None else "#94A3B8"),
        metric_card_html("Monthly Savings Identified", f"${savings:,.0f}" if savings is not None else "—",
                          "From the Cost Optimization Engine" if savings is not None else "Visit Cost Optimization",
                          "#2ECC71" if savings else "#94A3B8"),
        metric_card_html("Demand Forecast Accuracy", f"{accuracy:.0f}%" if accuracy is not None else "—",
                          "In-sample fit of the headline model" if accuracy is not None else "Visit Demand Forecasting",
                          get_health_color(accuracy) if accuracy is not None else "#94A3B8"),
        metric_card_html("On-Time Delivery Rate", f"{on_time_rate:.0f}%" if on_time_rate is not None else "—",
                          "Order-weighted across suppliers" if on_time_rate is not None else "Visit Supplier Scorecard",
                          get_health_color(on_time_rate) if on_time_rate is not None else "#94A3B8"),
    ], min_width=220),
    unsafe_allow_html=True,
)

st.markdown("---")
st.markdown("### Supply Chain Snapshot")
col1, col2 = st.columns(2)

with col1:
    st.markdown("**Supply Chain Flow**")
    if sim_result:
        health = sim_result["health"]
        nodes = ["Supplier", "Manufacturing", "Warehouse", "Distribution", "Customer"]
        node_colors = [get_health_color(health[n][0]) for n in nodes]
        fig = go.Figure(go.Sankey(
            node=dict(label=nodes, color=node_colors, pad=24, thickness=24, line=dict(color="white", width=1)),
            link=dict(source=[0, 1, 2, 3], target=[1, 2, 3, 4], value=[sim_result["monthly_volume"]] * 4,
                       color="rgba(148,163,184,0.35)"),
        ))
        fig.update_layout(height=280, margin=dict(t=10, b=10, l=10, r=10), font=dict(family="Inter, sans-serif", size=12))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption("Visit the Supply Chain Simulator page to populate this.")

with col2:
    st.markdown("**Demand Forecast (Next 3 Months)**")
    if forecast_result:
        series = forecast_result["series"]
        future_dates = pd.date_range(series.index[-1] + pd.DateOffset(months=1), periods=3, freq="MS")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=series.index[-6:], y=series.values[-6:], mode="lines+markers", name="Actual", line=dict(color="#1E293B")))
        fig.add_trace(go.Scatter(x=future_dates, y=forecast_result["hw_forecast_path"].values, mode="lines+markers",
                                  name="Forecast", line=dict(color="#4F46E5", dash="dash")))
        fig.update_layout(height=280, margin=dict(t=10, b=10, l=10, r=10), font=dict(family="Inter, sans-serif", size=12),
                           legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption("Visit the Demand Forecasting page to populate this.")

st.markdown("**Supplier Performance Radar**")
if supplier_df is not None and len(supplier_df) > 0:
    categories = ["On-Time Delivery", "Quality (low defects)", "Price Consistency", "Lead Time Reliability", "Communication"]
    fig = go.Figure()
    for _, row in supplier_df.iterrows():
        values = [
            max(0, min(100, row["On-Time Delivery %"])),
            max(0, 100 - row["Defect Rate %"] * 10),
            max(0, 100 - row["Price Variance %"] * 8),
            max(0, min(100, row["Lead Time Reliability %"])),
            max(0, min(100, row["Communication (1-5)"] / 5 * 100)),
        ]
        fig.add_trace(go.Scatterpolar(r=values + [values[0]], theta=categories + [categories[0]],
                                       fill="toself", name=row["Supplier"], opacity=0.6))
    fig.update_layout(height=380, margin=dict(t=20, b=20, l=40, r=40),
                       polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                       font=dict(family="Inter, sans-serif", size=12),
                       legend=dict(orientation="h", yanchor="bottom", y=-0.15, x=0))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.caption("Visit the Supplier Scorecard page to populate this.")

st.markdown("---")
st.markdown("### Action Items")

actions = []
if supplier_df is not None and len(supplier_df) > 0:
    def _score(row):
        return (
            max(0, min(100, row["On-Time Delivery %"])) * 0.30
            + max(0, 100 - row["Defect Rate %"] * 10) * 0.25
            + max(0, 100 - row["Price Variance %"] * 8) * 0.15
            + max(0, min(100, row["Lead Time Reliability %"])) * 0.20
            + max(0, min(100, row["Communication (1-5)"] / 5 * 100)) * 0.10
        )
    scored = supplier_df.assign(_score=supplier_df.apply(_score, axis=1)).sort_values("_score")
    worst = scored.iloc[0]
    if worst["_score"] < 70:
        actions.append(("urgent", f"<b>{worst['Supplier']}</b> is your weakest supplier (score {worst['_score']:.0f}) — investigate before the next order cycle."))

if forecast_result and "days_of_stock" in forecast_result:
    dos = forecast_result["days_of_stock"]
    if dos < 30:
        actions.append(("week", f"Reorder soon — projected stockout in <b>{dos:.0f} days</b> at the current forecasted pace."))

if cost_result and cost_result["savings_breakdown"]:
    top_saving = max(cost_result["savings_breakdown"], key=lambda x: x[1])
    actions.append(("month", f"Address <b>{top_saving[0]}</b> — potential <b>${top_saving[1]:,.0f}/month</b> in savings."))

ICONS = {"urgent": "🔴 Urgent", "week": "🟡 This week", "month": "🟢 This month"}
if actions:
    for level, text in actions:
        st.markdown(f'<div class="action-item">{ICONS[level]}: {text}</div>', unsafe_allow_html=True)
else:
    st.caption("No action items yet — visit the other SupplyIQ pages to generate personalized recommendations here.")
