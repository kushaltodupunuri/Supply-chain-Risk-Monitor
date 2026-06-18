import os
import json
from datetime import datetime, date

# Persists one risk-score snapshot per industry per calendar day, building up a
# real trend line over time starting from whenever this code first runs - there's
# no way to back-fill genuine history for a score formula that didn't exist before
# today, so the chart intentionally starts with a single point and grows from there.
#
# Note for Streamlit Cloud: this writes to the app's local filesystem, which is
# only persistent for the lifetime of the running container - a redeploy or a
# free-tier sleep/wake cycle can reset it. Good enough to show a real local trend
# during a session, not a guaranteed permanent record.
CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "cache")


def _history_path(industry):
    safe_name = "".join(c if c.isalnum() else "_" for c in industry)
    return os.path.join(CACHE_DIR, f"score_history_{safe_name}.json")


def record_score_snapshot(industry, total_score, sub_scores):
    """Appends today's score if it hasn't already been recorded today - safe to
    call on every page load."""
    path = _history_path(industry)
    history = []
    if os.path.exists(path):
        with open(path) as f:
            history = json.load(f)

    today = date.today().isoformat()
    if history and history[-1]["date"] == today:
        history[-1] = {"date": today, "total": total_score, "sub_scores": sub_scores}
    else:
        history.append({"date": today, "total": total_score, "sub_scores": sub_scores})

    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(path, "w") as f:
        json.dump(history, f)


def get_score_history(industry, days=90):
    path = _history_path(industry)
    if not os.path.exists(path):
        return []
    with open(path) as f:
        history = json.load(f)
    cutoff = (datetime.now().date()).toordinal() - days
    return [entry for entry in history if date.fromisoformat(entry["date"]).toordinal() >= cutoff]
