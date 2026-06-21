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
            background: linear-gradient(150deg, #FFFFFF 0%, #FAFBFF 100%);
            border-radius: 16px;
            padding: 18px 20px 16px;
            margin: 6px 0;
            box-shadow: 0 10px 26px rgba(15, 23, 42, 0.15), 0 3px 8px rgba(15, 23, 42, 0.10);
            border: 1px solid #F1F5F9;
            border-top: 4px solid var(--card-color, #94A3B8);
            height: 100%;
            position: relative;
            overflow: hidden;
            transition: box-shadow 0.2s ease, transform 0.2s ease;
        }
        .metric-card:hover {
            box-shadow: 0 18px 38px rgba(15, 23, 42, 0.22), 0 6px 12px rgba(15, 23, 42, 0.12);
            transform: translateY(-4px);
        }
        .metric-card::before {
            content: "";
            position: absolute;
            top: -30px; right: -30px;
            width: 90px; height: 90px;
            border-radius: 50%;
            background: var(--card-color, #94A3B8);
            opacity: 0.07;
        }
        .metric-card .metric-label {
            font-weight: 700; font-size: 11.5px; color: #64748B;
            text-transform: uppercase; letter-spacing: 0.06em;
            position: relative; z-index: 1;
        }
        .metric-card .metric-value {
            font-size: 30px; font-weight: 800; margin-top: 8px; line-height: 1.1;
            position: relative; z-index: 1;
        }
        .metric-card .metric-caption {
            font-size: 12.5px; color: #94A3B8; margin-top: 8px; line-height: 1.45;
            position: relative; z-index: 1;
        }

        .note-card {
            border-radius: 14px;
            padding: 18px 20px;
            box-shadow: 0 10px 26px rgba(15, 23, 42, 0.12), 0 3px 8px rgba(15, 23, 42, 0.08);
            line-height: 1.65;
            font-size: 15px;
        }

        .action-item {
            background: #FFFFFF;
            border-radius: 10px;
            padding: 12px 16px;
            margin: 6px 0;
            box-shadow: 0 8px 22px rgba(15, 23, 42, 0.10), 0 2px 6px rgba(15, 23, 42, 0.06);
            border: 1px solid #EEF2F7;
            transition: box-shadow 0.2s ease, transform 0.2s ease;
        }
        .action-item:hover {
            box-shadow: 0 14px 32px rgba(15, 23, 42, 0.16), 0 4px 10px rgba(15, 23, 42, 0.10);
            transform: translateY(-3px);
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
