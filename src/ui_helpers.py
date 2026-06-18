import streamlit as st

# Shared styling for the SupplyIQ modules (pages/*.py) - each Streamlit page runs as
# its own script, so CSS injected in app.py doesn't carry over; this gets imported
# and called once at the top of every page instead of repeating the same <style>
# block six times.


def inject_shared_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        html, body, .stApp, .stMarkdown, p {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        h1, h2, h3 { font-weight: 800 !important; letter-spacing: -0.01em !important; }

        .metric-card {
            background: #FFFFFF;
            border-radius: 14px;
            padding: 18px 20px;
            margin: 6px 0;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08), 0 1px 2px rgba(15, 23, 42, 0.04);
            border-left: 5px solid var(--card-color, #94A3B8);
            height: 100%;
        }
        .metric-card .metric-label {
            font-weight: 600; font-size: 12.5px; color: #64748B;
            text-transform: uppercase; letter-spacing: 0.02em;
        }
        .metric-card .metric-value { font-size: 30px; font-weight: 800; margin-top: 6px; line-height: 1.15; }
        .metric-card .metric-caption { font-size: 12.5px; color: #94A3B8; margin-top: 6px; line-height: 1.4; }

        .note-card {
            border-radius: 14px;
            padding: 18px 20px;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
            line-height: 1.65;
            font-size: 15px;
        }

        .action-item {
            background: #FFFFFF;
            border-radius: 10px;
            padding: 12px 16px;
            margin: 6px 0;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
            border: 1px solid #EEF2F7;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_health_color(score):
    """0-100, higher = healthier (opposite sense from the risk scores elsewhere in
    this app, which use higher = riskier) - SupplyIQ's modules talk in terms of
    health/performance, matching how a small business owner thinks about it."""
    if score >= 70:
        return "#2ECC71"
    elif score >= 40:
        return "#F39C12"
    return "#E74C3C"


def get_health_label(score):
    if score >= 70:
        return "Healthy"
    elif score >= 40:
        return "Watch"
    return "Problem"


def metric_card_html(label, value_html, caption=None, color="#4F46E5"):
    caption_html = f'<div class="metric-caption">{caption}</div>' if caption else ""
    return (
        f'<div class="metric-card" style="--card-color: {color};">'
        f'<div class="metric-label">{label}</div>'
        f'<div class="metric-value" style="color: {color};">{value_html}</div>'
        f'{caption_html}'
        f'</div>'
    )


def cards_grid(cards_html_list, min_width=200):
    return (
        f'<div style="display:grid; grid-template-columns:repeat(auto-fit, minmax({min_width}px, 1fr)); '
        f'gap:12px; margin-bottom:12px;">' + "".join(cards_html_list) + "</div>"
    )
