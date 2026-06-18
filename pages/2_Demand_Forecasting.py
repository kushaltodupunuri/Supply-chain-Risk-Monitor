import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from statsmodels.tsa.holtwinters import SimpleExpSmoothing, ExponentialSmoothing

from src.ui_helpers import inject_shared_css, metric_card_html, cards_grid

st.set_page_config(page_title="Demand Forecasting - SupplyIQ", page_icon="📈", layout="wide")
inject_shared_css()

st.title("📈 Demand Forecasting Engine")
st.caption("Know What You'll Sell Before You Sell It")

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def generate_demo_sales():
    """A synthetic but plausible 24-month series with an upward trend and a real
    Nov/Dec seasonal spike, so the seasonal-alert and 3-model comparison logic below
    has something realistic to chew on without requiring an upload first."""
    rng = np.random.default_rng(42)
    dates = pd.date_range(end=pd.Timestamp.today().replace(day=1), periods=24, freq="MS")
    seasonal_factor = {1: 0.9, 2: 0.85, 3: 0.95, 4: 1.0, 5: 1.0, 6: 1.05,
                        7: 1.0, 8: 0.95, 9: 1.0, 10: 1.1, 11: 1.3, 12: 1.45}
    trend = np.linspace(0, 80, 24)
    values = []
    for i, d in enumerate(dates):
        val = (300 + trend[i]) * seasonal_factor[d.month] + rng.normal(0, 15)
        values.append(max(10, round(val)))
    return pd.DataFrame({"date": dates, "units": values})


def parse_uploaded_csv(file):
    df = pd.read_csv(file)
    df.columns = [c.strip().lower() for c in df.columns]
    date_col = next((c for c in df.columns if c in ("date", "month", "period")), None)
    units_col = next((c for c in df.columns if c in ("units", "sales", "quantity", "qty", "volume")), None)
    if date_col is None or units_col is None:
        raise ValueError("Couldn't find a date column and a units/sales column. Expected headers like 'date' and 'units'.")
    out = df[[date_col, units_col]].rename(columns={date_col: "date", units_col: "units"})
    out["date"] = pd.to_datetime(out["date"])
    out["units"] = pd.to_numeric(out["units"], errors="coerce")
    out = out.dropna().sort_values("date").reset_index(drop=True)
    # Resample to monthly so seasonality (period=12) and the 3 models below are
    # comparing like-for-like, regardless of whether the upload was daily or monthly.
    out = out.set_index("date").resample("MS")["units"].sum().reset_index()
    return out


st.markdown("**Step 1: Provide sales history**")
col_upload, col_demo = st.columns([2, 1])
with col_upload:
    uploaded = st.file_uploader("Upload a CSV with columns like 'date' and 'units'", type=["csv"])
with col_demo:
    st.markdown("<br>", unsafe_allow_html=True)
    use_demo = st.button("Use Demo Data Instead", width="stretch")

sales_df = None
if uploaded is not None:
    try:
        sales_df = parse_uploaded_csv(uploaded)
    except Exception as e:
        st.error(f"Couldn't read that file: {e}")
elif use_demo or "forecast_sales_df" in st.session_state:
    sales_df = st.session_state.get("forecast_sales_df", generate_demo_sales())

if sales_df is not None:
    st.session_state["forecast_sales_df"] = sales_df

if sales_df is None or len(sales_df) < 6:
    st.info("Upload at least 6 months of history, or click \"Use Demo Data Instead\" to try it now.")
    st.stop()

st.markdown("---")
st.markdown("**Step 2: Optional - current inventory, for stockout/overstock warnings**")
col_inv1, col_inv2 = st.columns(2)
with col_inv1:
    current_inventory = st.number_input("Current inventory (units)", min_value=0, value=0, step=10)
with col_inv2:
    lead_time_days = st.number_input("Average lead time to restock (days)", min_value=1, value=14, step=1)

series = sales_df.set_index("date")["units"].asfreq("MS")
n = len(series)

# Model 1: Moving Average - trailing 3-month mean projected forward
ma_window = min(3, n)
ma_forecast = series.tail(ma_window).mean()

# Model 2: Simple Exponential Smoothing - no trend/seasonality, reacts to the most recent level
ses_fit = SimpleExpSmoothing(series, initialization_method="estimated").fit()
ses_forecast = ses_fit.forecast(1).iloc[0]

# Model 3: Holt-Winters (trend + seasonality) - needs 2 full years to estimate a
# seasonal_periods=12 pattern reliably; falls back to trend-only Holt below that.
if n >= 24:
    hw_fit = ExponentialSmoothing(
        series, trend="add", seasonal="add", seasonal_periods=12, initialization_method="estimated",
    ).fit()
else:
    hw_fit = ExponentialSmoothing(series, trend="add", initialization_method="estimated").fit()
hw_forecast_path = hw_fit.forecast(3)
hw_forecast = hw_forecast_path.iloc[0]

# Confidence range from in-sample residual spread (a simple, transparent approximation
# rather than relying on statsmodels' simulation-based intervals, which behave
# inconsistently across model/version combinations).
residuals = series - hw_fit.fittedvalues
resid_std = residuals.std()
ci_low = max(0, hw_forecast - 1.44 * resid_std)   # ~85% two-tailed under a normal approximation
ci_high = hw_forecast + 1.44 * resid_std

# In-sample MAPE (mean absolute percentage error) of the headline model's fitted values vs.
# actuals - a measured number (not a guess), used as the "forecast accuracy" stat elsewhere
# (e.g. the Executive Dashboard). It reflects fit quality on history, not true out-of-sample
# accuracy, since there's no held-out future to score against yet.
nonzero = series != 0
mape = (residuals[nonzero] / series[nonzero]).abs().mean() * 100
forecast_accuracy_pct = max(0, 100 - mape)

st.session_state["forecast_result"] = {
    "series": series, "hw_forecast_path": hw_forecast_path,
    "hw_forecast": hw_forecast, "ci_low": ci_low, "ci_high": ci_high,
    "forecast_accuracy_pct": forecast_accuracy_pct,
}

st.markdown("---")
st.markdown("### Forecast")

next_month_label = (series.index[-1] + pd.DateOffset(months=1)).strftime("%B %Y")
st.markdown(
    cards_grid([
        metric_card_html(
            f"Forecast for {next_month_label}",
            f"~{hw_forecast:.0f} units",
            f"Between {ci_low:.0f} and {ci_high:.0f} units (~85% confidence)",
            "#4F46E5",
        ),
        metric_card_html("Moving Average Model", f"{ma_forecast:.0f} units", f"Trailing {ma_window}-month average", "#0EA5E9"),
        metric_card_html("Exponential Smoothing", f"{ses_forecast:.0f} units", "Reacts fastest to recent change", "#10B981"),
        metric_card_html("Holt-Winters (Trend + Seasonality)", f"{hw_forecast:.0f} units", "Used as the headline forecast above", "#F59E0B"),
    ]),
    unsafe_allow_html=True,
)
st.caption(
    "Holt-Winters models both a trend and a repeating seasonal pattern, so it's used as the "
    "headline number - the other two are shown for comparison/sanity-checking, not because "
    "they're wrong. Facebook Prophet was the originally planned 3rd model, but its build chain "
    "is heavy and fragile on Windows; Holt-Winters covers the same trend+seasonality capability "
    "with a much lighter dependency."
)

# Seasonal alert: which calendar month has historically been highest, and is it coming up
monthly_avg = sales_df.copy()
monthly_avg["month"] = monthly_avg["date"].dt.month
peak_month = monthly_avg.groupby("month")["units"].mean().idxmax()
today_month = pd.Timestamp.today().month
months_until_peak = (peak_month - today_month) % 12
if 0 < months_until_peak <= 2:
    peak_avg = monthly_avg.groupby("month")["units"].mean().max()
    overall_avg = monthly_avg["units"].mean()
    pct_above = (peak_avg / overall_avg - 1) * 100
    st.warning(
        f"📅 **Seasonal alert:** {MONTH_NAMES[peak_month - 1]} is historically your highest month "
        f"(~{pct_above:.0f}% above average) and it's {months_until_peak} month(s) away — "
        f"consider ordering extra inventory now."
    )

# Stockout / overstock warnings, only if the user gave a real inventory number
if current_inventory > 0:
    daily_run_rate = hw_forecast / 30
    if daily_run_rate > 0:
        days_of_stock = current_inventory / daily_run_rate
        st.session_state["forecast_result"]["days_of_stock"] = days_of_stock
        if days_of_stock < lead_time_days + 7:
            st.error(
                f"🔴 **Stockout warning:** at the current forecasted pace, your {current_inventory:.0f} "
                f"units on hand run out in about {days_of_stock:.0f} days — tighter than your "
                f"{lead_time_days:.0f}-day lead time. Reorder now."
            )
        elif days_of_stock > 90:
            excess_days = days_of_stock - 60
            st.warning(
                f"🟡 **Overstock warning:** at the current forecasted pace, your inventory covers "
                f"~{days_of_stock:.0f} days of demand — about {excess_days:.0f} days more than a "
                f"healthy ~60-day buffer. Consider a promotion to move excess stock."
            )
        else:
            st.success(f"✅ Inventory looks healthy: ~{days_of_stock:.0f} days of stock at the current forecasted pace.")

st.markdown("---")
st.markdown("### History + Forecast")
fig = go.Figure()
fig.add_trace(go.Scatter(x=series.index, y=series.values, mode="lines+markers", name="Actual", line=dict(color="#1E293B")))
future_dates = pd.date_range(series.index[-1] + pd.DateOffset(months=1), periods=3, freq="MS")
fig.add_trace(go.Scatter(x=future_dates, y=hw_forecast_path.values, mode="lines+markers", name="Forecast (3mo)", line=dict(color="#4F46E5", dash="dash")))
fig.add_trace(go.Scatter(
    x=[future_dates[0], future_dates[0]], y=[ci_low, ci_high], mode="markers",
    marker=dict(color="rgba(79,70,229,0.4)", size=1), showlegend=False, hoverinfo="skip",
))
fig.update_layout(
    height=380, margin=dict(t=20, b=20, l=40, r=20),
    font=dict(family="Inter, sans-serif", color="#1E293B"),
    plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
)
st.plotly_chart(fig, use_container_width=True)
