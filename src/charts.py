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
    fig.update_layout(
        geo=dict(showframe=False, showcoastlines=True, projection_type="equirectangular"),
        height=400,
        margin=dict(t=10, b=10, l=0, r=0),
        font=dict(family="Inter, sans-serif", color="#1E293B"),
    )
    return fig
