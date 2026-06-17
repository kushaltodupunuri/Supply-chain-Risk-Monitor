import io
from datetime import datetime

import pandas as pd
from fpdf import FPDF

RISK_COLOR_RGB = {
    "Low Risk": (46, 204, 113),
    "Moderate Risk": (243, 156, 18),
    "High Risk": (230, 126, 34),
    "Critical Risk": (231, 76, 60),
}

CATEGORY_LABELS = {
    "supplier": "Supplier Concentration",
    "commodity": "Commodity Price",
    "logistics": "Logistics & Shipping",
    "geopolitical": "Geopolitical",
    "regulatory": "Regulatory & Trade",
}


_UNICODE_REPLACEMENTS = {
    "—": "-", "–": "-",  # em dash, en dash
    "‘": "'", "’": "'",  # curly single quotes
    "“": '"', "”": '"',  # curly double quotes
    "…": "...",  # ellipsis
    "•": "-",  # bullet
    " ": " ",  # non-breaking space
}


def _pdf_safe(text):
    """Core Helvetica only supports latin-1; AI-generated text often has
    em-dashes/smart quotes that would otherwise crash fpdf2 mid-render."""
    for char, replacement in _UNICODE_REPLACEMENTS.items():
        text = text.replace(char, replacement)
    return text.encode("latin-1", "replace").decode("latin-1")


def _risk_label(score):
    if score <= 30:
        return "Low Risk"
    elif score <= 60:
        return "Moderate Risk"
    elif score <= 80:
        return "High Risk"
    return "Critical Risk"


def generate_excel_report(industry, company_name, time_horizon, result, ai_summary, recommendations):
    """Returns the .xlsx file as bytes, ready for st.download_button."""
    overview_df = pd.DataFrame([
        {"Field": "Industry", "Value": industry},
        {"Field": "Company", "Value": company_name or "(industry-level, no company specified)"},
        {"Field": "Time Horizon", "Value": time_horizon},
        {"Field": "Report Generated", "Value": datetime.now().strftime("%Y-%m-%d %H:%M")},
        {"Field": "Overall Risk Score", "Value": result["total"]},
        {"Field": "Overall Risk Level", "Value": result["label"]},
    ])

    scores_df = pd.DataFrame([
        {
            "Category": CATEGORY_LABELS.get(key, key),
            "Score": value,
            "Risk Level": _risk_label(value),
        }
        for key, value in result["sub_scores"].items()
    ])

    recs_df = pd.DataFrame([
        {"#": i, "Recommendation": rec["title"], "Detail": rec["detail"], "Priority": rec["priority"]}
        for i, rec in enumerate(recommendations, 1)
    ])

    summary_df = pd.DataFrame([{"AI Risk Brief": ai_summary}])

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        overview_df.to_excel(writer, sheet_name="Overview", index=False)
        scores_df.to_excel(writer, sheet_name="Risk Scores", index=False)
        summary_df.to_excel(writer, sheet_name="AI Summary", index=False)
        recs_df.to_excel(writer, sheet_name="Recommendations", index=False)

        # Auto-fit column widths roughly to content length, since the default is too narrow.
        for sheet_name, df in [
            ("Overview", overview_df), ("Risk Scores", scores_df),
            ("AI Summary", summary_df), ("Recommendations", recs_df),
        ]:
            worksheet = writer.sheets[sheet_name]
            for col_idx, col_name in enumerate(df.columns, 1):
                max_len = max([len(str(col_name))] + [len(str(v)) for v in df[col_name]])
                worksheet.column_dimensions[worksheet.cell(row=1, column=col_idx).column_letter].width = min(
                    max(max_len + 2, 12), 80
                )

    return buffer.getvalue()


def generate_pdf_report(industry, company_name, time_horizon, result, ai_summary, recommendations):
    """Returns the .pdf file as bytes, ready for st.download_button.

    Deliberately doesn't embed the actual Plotly gauge chart as an image - that would
    require the `kaleido` package, which bundles its own headless-Chromium-like
    renderer and is a large, slow dependency for a free-tier Streamlit Cloud deploy.
    The score boxes are drawn directly with fpdf2's own rectangle/text primitives
    instead, which is lightweight and looks clean without the extra dependency.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    epw = pdf.epw  # effective page width, used instead of 0 to avoid fpdf2's
    # "0 = extend to right margin from current x" ambiguity, which can shrink
    # to near-zero width if x wasn't reset to the left margin beforehand.

    pdf.set_font("Helvetica", "B", 20)
    pdf.set_x(10)
    pdf.cell(epw, 10, "Supply Chain Risk Monitor", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(100, 100, 100)
    subtitle = f"{industry}"
    if company_name:
        subtitle += f"  |  {company_name}"
    subtitle += f"  |  {time_horizon} horizon  |  Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    pdf.set_x(10)
    pdf.cell(epw, 8, _pdf_safe(subtitle), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Overall score box
    color = RISK_COLOR_RGB.get(result["label"], (100, 100, 100))
    pdf.set_fill_color(*color)
    pdf.rect(10, pdf.get_y(), 190, 22, style="F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_xy(15, pdf.get_y() + 5)
    pdf.cell(epw - 5, 10, f"Overall Risk Score: {result['total']} / 100  -  {result['label']}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(10)
    pdf.ln(15)

    # Sub-score breakdown
    pdf.set_text_color(30, 41, 59)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_x(10)
    pdf.cell(epw, 8, "Risk Breakdown", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    for key, value in result["sub_scores"].items():
        label = CATEGORY_LABELS.get(key, key)
        risk_text = _risk_label(value)
        box_color = RISK_COLOR_RGB.get(risk_text, (100, 100, 100))
        y = pdf.get_y()
        pdf.set_fill_color(*box_color)
        pdf.rect(10, y, 4, 8, style="F")
        pdf.set_text_color(30, 41, 59)
        pdf.set_font("Helvetica", "", 11)
        pdf.set_xy(17, y)
        pdf.cell(90, 8, label)
        pdf.set_xy(110, y)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(30, 8, f"{value}")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*box_color)
        pdf.cell(50, 8, risk_text)
        pdf.set_text_color(30, 41, 59)
        pdf.set_x(10)
        pdf.ln(9)

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_x(10)
    pdf.cell(epw, 8, "AI Risk Brief", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_x(10)
    pdf.multi_cell(epw, 6, _pdf_safe(ai_summary), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 13)
    pdf.set_x(10)
    pdf.cell(epw, 8, "Recommended Actions", new_x="LMARGIN", new_y="NEXT")
    for i, rec in enumerate(recommendations, 1):
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_x(10)
        pdf.multi_cell(epw, 6, _pdf_safe(f"{i}. {rec['title']} (Priority: {rec['priority']})"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_x(10)
        pdf.multi_cell(epw, 6, _pdf_safe(rec["detail"]), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    return bytes(pdf.output())
