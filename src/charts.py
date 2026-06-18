import plotly.graph_objects as go

# Plotly's choropleth needs ISO-3 codes; our risk data is keyed by ISO-2. A few
# countries fail to match anything under locationmode="country names" (e.g.
# South Korea, Taiwan, Malaysia), so we map through ISO-3 codes explicitly instead.
ALPHA2_TO_ALPHA3 = {
    "AD": "AND", "AE": "ARE", "AF": "AFG", "AG": "ATG", "AL": "ALB", "AM": "ARM",
    "AO": "AGO", "AR": "ARG", "AT": "AUT", "AU": "AUS", "AZ": "AZE", "BA": "BIH",
    "BD": "BGD", "BE": "BEL", "BF": "BFA", "BG": "BGR", "BH": "BHR", "BI": "BDI",
    "BJ": "BEN", "BN": "BRN", "BO": "BOL", "BR": "BRA", "BS": "BHS", "BT": "BTN",
    "BW": "BWA", "BY": "BLR", "BZ": "BLZ", "CA": "CAN", "CD": "COD", "CF": "CAF",
    "CG": "COG", "CH": "CHE", "CI": "CIV", "CL": "CHL", "CM": "CMR", "CN": "CHN",
    "CO": "COL", "CR": "CRI", "CU": "CUB", "CY": "CYP", "CZ": "CZE", "DE": "DEU",
    "DJ": "DJI", "DK": "DNK", "DO": "DOM", "DZ": "DZA", "EC": "ECU", "EE": "EST",
    "EG": "EGY", "ER": "ERI", "ES": "ESP", "ET": "ETH", "FI": "FIN", "FJ": "FJI",
    "FR": "FRA", "GA": "GAB", "GB": "GBR", "GE": "GEO", "GH": "GHA", "GM": "GMB",
    "GN": "GIN", "GQ": "GNQ", "GR": "GRC", "GT": "GTM", "GW": "GNB", "GY": "GUY",
    "HN": "HND", "HR": "HRV", "HT": "HTI", "HU": "HUN", "ID": "IDN", "IE": "IRL",
    "IL": "ISR", "IN": "IND", "IQ": "IRQ", "IR": "IRN", "IS": "ISL", "IT": "ITA",
    "JM": "JAM", "JO": "JOR", "JP": "JPN", "KE": "KEN", "KG": "KGZ", "KH": "KHM",
    "KP": "PRK", "KR": "KOR", "KW": "KWT", "KZ": "KAZ", "LA": "LAO", "LB": "LBN",
    "LK": "LKA", "LR": "LBR", "LS": "LSO", "LT": "LTU", "LU": "LUX", "LV": "LVA",
    "LY": "LBY", "MA": "MAR", "MD": "MDA", "ME": "MNE", "MG": "MDG", "MK": "MKD",
    "ML": "MLI", "MM": "MMR", "MN": "MNG", "MR": "MRT", "MT": "MLT", "MU": "MUS",
    "MW": "MWI", "MX": "MEX", "MY": "MYS", "MZ": "MOZ", "NA": "NAM", "NE": "NER",
    "NG": "NGA", "NI": "NIC", "NL": "NLD", "NO": "NOR", "NP": "NPL", "NZ": "NZL",
    "OM": "OMN", "PA": "PAN", "PE": "PER", "PG": "PNG", "PH": "PHL", "PK": "PAK",
    "PL": "POL", "PT": "PRT", "PY": "PRY", "QA": "QAT", "RO": "ROU", "RS": "SRB",
    "RU": "RUS", "RW": "RWA", "SA": "SAU", "SD": "SDN", "SE": "SWE", "SG": "SGP",
    "SI": "SVN", "SK": "SVK", "SL": "SLE", "SN": "SEN", "SO": "SOM", "SS": "SSD",
    "SV": "SLV", "SY": "SYR", "SZ": "SWZ", "TD": "TCD", "TG": "TGO", "TH": "THA",
    "TJ": "TJK", "TL": "TLS", "TM": "TKM", "TN": "TUN", "TR": "TUR", "TT": "TTO",
    "TW": "TWN", "TZ": "TZA", "UA": "UKR", "UG": "UGA", "US": "USA", "UY": "URY",
    "UZ": "UZB", "VE": "VEN", "VN": "VNM", "YE": "YEM", "ZA": "ZAF", "ZM": "ZMB",
    "ZW": "ZWE",
}


def hex_to_rgba(hex_color, alpha=0.13):
    """Plotly's fillcolor needs rgba(), not CSS-style 8-digit hex-with-alpha."""
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def build_commodity_chart(commodity_name, history):
    dates = [item["date"] for item in history]
    values = [item["value"] for item in history]
    pct_change = (values[-1] - values[0]) / values[0]
    line_color = "#E74C3C" if pct_change > 0 else "#2ECC71"

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=values,
            mode="lines",
            line=dict(color=line_color, width=2),
            fill="tozeroy",
            fillcolor=hex_to_rgba(line_color),
        )
    )
    fig.update_layout(
        title=f"{commodity_name} — {pct_change:+.1%} over shown period",
        height=220,
        margin=dict(t=40, b=20, l=40, r=20),
        showlegend=False,
        hovermode="x unified",
        font=dict(family="Inter, sans-serif", color="#1E293B"),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
    )
    return fig


# Approximate country centroids (lat, lon) for the countries that actually show up
# in our sourcing data - used to place a supplier-location marker on the map.
# These are geographic centroids, not factory addresses - we don't have real
# city/factory-level coordinates for named suppliers, so a precise-looking pin at a
# specific street address would be fabricated. A country-level dot is honest about
# what we actually know: which countries sourcing comes from, not which buildings.
COUNTRY_CENTROIDS = {
    "CN": (35.0, 103.0), "TW": (23.7, 121.0), "KR": (36.5, 127.8),
    "VN": (16.0, 108.0), "MY": (4.2, 102.0), "IN": (22.0, 79.0),
    "MX": (23.6, -102.5), "JP": (36.2, 138.3), "DE": (51.2, 10.4),
    "BD": (23.7, 90.4), "US": (39.8, -98.6), "BR": (-10.3, -53.2),
    "AR": (-34.0, -64.0), "AU": (-25.3, 133.8), "UA": (48.4, 31.2),
    "IE": (53.4, -8.0), "SG": (1.35, 103.8),
    "SA": (24.0, 45.0), "RU": (61.5, 105.3), "CA": (56.1, -106.3),
    "FR": (46.6, 2.2), "GB": (54.0, -2.0),
}


def build_geo_choropleth(by_country):
    mappable = {code: data for code, data in by_country.items() if code in ALPHA2_TO_ALPHA3}

    fig = go.Figure(
        data=go.Choropleth(
            locations=[ALPHA2_TO_ALPHA3[code] for code in mappable],
            locationmode="ISO-3",
            z=[data["final"] for data in mappable.values()],
            zmin=0,
            zmax=100,
            colorscale=[[0, "#2ECC71"], [0.3, "#F39C12"], [0.6, "#E67E22"], [1.0, "#E74C3C"]],
            marker_line_color="white",
            marker_line_width=0.5,
            colorbar_title="Risk Score",
        )
    )

    markers = {code: data for code, data in by_country.items() if code in COUNTRY_CENTROIDS}
    if markers:
        lats = [COUNTRY_CENTROIDS[code][0] for code in markers]
        lons = [COUNTRY_CENTROIDS[code][1] for code in markers]
        labels = [f"{data['name']} - {data['weight']:.0%} of sourcing" for data in markers.values()]
        fig.add_trace(
            go.Scattergeo(
                lat=lats,
                lon=lons,
                text=labels,
                hoverinfo="text",
                mode="markers",
                marker=dict(
                    size=[8 + data["weight"] * 35 for data in markers.values()],
                    color="#1E293B",
                    line=dict(width=1.5, color="white"),
                    opacity=0.85,
                ),
                showlegend=False,
            )
        )

    fig.update_layout(
        geo=dict(showframe=False, showcoastlines=True, projection_type="equirectangular"),
        height=400,
        margin=dict(t=10, b=10, l=0, r=0),
        font=dict(family="Inter, sans-serif", color="#1E293B"),
    )
    return fig


RISK_CATEGORY_LABELS = {
    "supplier": "Supplier Concentration",
    "commodity": "Commodity Price",
    "logistics": "Logistics & Shipping",
    "geopolitical": "Geopolitical",
    "regulatory": "Regulatory & Trade",
}


def build_risk_heatmap(industry_scores):
    """industry_scores: {industry_name: {category_key: score}}. Renders all
    industries against all 5 categories so risk can be compared across the whole
    portfolio at once, instead of one industry at a time."""
    industries = list(industry_scores.keys())
    category_keys = list(RISK_CATEGORY_LABELS.keys())
    z = [[industry_scores[industry][key] for key in category_keys] for industry in industries]

    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=[RISK_CATEGORY_LABELS[key] for key in category_keys],
            y=industries,
            zmin=0,
            zmax=100,
            colorscale=[[0, "#2ECC71"], [0.3, "#F39C12"], [0.6, "#E67E22"], [1.0, "#E74C3C"]],
            colorbar_title="Risk Score",
            text=z,
            texttemplate="%{text:.0f}",
            textfont=dict(size=11),
        )
    )
    fig.update_layout(
        height=420,
        margin=dict(t=20, b=20, l=10, r=10),
        font=dict(family="Inter, sans-serif", color="#1E293B"),
        xaxis=dict(side="top"),
    )
    return fig


def build_score_trend_chart(history):
    """history: list of {date, total, sub_scores} from score_history.get_score_history.
    Starts with whatever real history has accumulated since tracking began - a
    single point is rendered as a marker rather than a broken line."""
    dates = [entry["date"] for entry in history]
    totals = [entry["total"] for entry in history]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=totals,
            mode="lines+markers" if len(dates) > 1 else "markers",
            line=dict(color="#4F46E5", width=2),
            marker=dict(size=8, color="#4F46E5"),
            fill="tozeroy",
            fillcolor="rgba(79,70,229,0.13)",
        )
    )
    fig.update_layout(
        height=260,
        margin=dict(t=20, b=20, l=40, r=20),
        yaxis=dict(range=[0, 100], title="Overall Risk Score"),
        # type="category" instead of the implicit date axis - with very few points
        # (especially just one, when tracking has just started) Plotly's date axis
        # auto-ticking falls back to absurd microsecond-precision labels since it
        # has no real interval to infer from.
        xaxis=dict(type="category"),
        font=dict(family="Inter, sans-serif", color="#1E293B"),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
    )
    return fig
