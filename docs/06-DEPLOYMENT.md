# Deployment — Putting It Live for Free

This explains how to get your app from running on your laptop to having a public URL that anyone can open.

---

## The Goal

You want a URL like:
```
https://supply-chain-risk-monitor.streamlit.app
```

Anyone in the world can open this. Recruiters can click it from your resume. You don't need to pay for servers. It's free forever for public apps.

---

## Platform: Streamlit Community Cloud

Streamlit (the company) offers free hosting for Streamlit apps. You connect your GitHub repo and they host it. When you push code updates to GitHub, the app redeploys automatically.

**Free tier includes:**
- Public URL
- Automatic deployment from GitHub
- Secret management (for your API keys)
- Unlimited usage (within reasonable limits)
- Custom app name (your-name.streamlit.app)

---

## Prerequisites

Before you can deploy, you need:
1. All code working locally (`streamlit run Risk_Monitor.py` works with no errors)
2. A GitHub account (free at github.com)
3. A Streamlit Cloud account (free at streamlit.io/cloud)
4. All API keys ready

---

## Step 1: Prepare Your Repository

### requirements.txt (already in the repo, shown here for reference)

```
streamlit>=1.50.0
plotly>=5.17.0
pandas>=2.0.0
requests>=2.31.0
python-dotenv>=1.0.0
ollama>=0.6.0
groq>=1.4.0
openpyxl>=3.1.0
fpdf2>=2.8.0
kaleido>=1.0.0
pillow>=10.0.0
```

`anthropic` was in the original plan but is never imported — the AI layer runs on Groq/Ollama instead (see [docs/05-AI-SUMMARY.md](05-AI-SUMMARY.md)). `openpyxl`/`fpdf2` build the Excel/PDF export, `kaleido` renders the Plotly charts/map as static images for those exports, and `pillow` is kaleido's transitive image-handling dependency.

### Create packages.txt (already in the repo)

Streamlit Cloud's base container doesn't have the system libraries `kaleido` needs to launch a headless Chrome for chart rendering. `packages.txt` at the repo root tells Streamlit Cloud's apt layer what to install alongside the Python packages:

```
libnss3
libatk1.0-0
libatk-bridge2.0-0
libcups2
libdbus-1-3
libdrm2
libxkbcommon0
libxcomposite1
libxdamage1
libxfixes3
libxrandr2
libgbm1
libasound2
libpango-1.0-0
libcairo2
```

If a chart still fails to render after this, it's not catastrophic — `src/export.py` wraps every chart-render call so it returns `None` and the export continues without that one image, rather than crashing the whole report.

### Create .gitignore

Prevent secrets and cache from being uploaded:

```
# .gitignore
.env
cache/
__pycache__/
*.pyc
*.pyo
.DS_Store
```

### Verify your folder structure

```
Supply-Chain-Risk-Monitor/
├── Risk_Monitor.py     ← MUST be here, this is what Streamlit runs
├── requirements.txt    ← MUST be here
├── packages.txt        ← MUST be here (apt deps kaleido needs for chart export)
├── .gitignore          ← MUST be here (protects your .env)
├── .env                ← NOT committed to GitHub (in .gitignore)
├── pages/              ← The 6 SupplyIQ modules - Streamlit auto-discovers these
├── docs/
└── src/
    ├── data/
    ├── models/
    └── ai/
```

---

## Step 2: Push to GitHub

### First time setup:

1. Go to github.com → click "New repository"
2. Name it: `supply-chain-risk-monitor`
3. Set to **Public** (required for free Streamlit hosting)
4. Don't add README (you already have one)
5. Click "Create repository"

### Push your code:

```bash
cd "C:\Users\kusha\OneDrive\Desktop\Supply Chain Risk Monitor"

# Initialize git
git init
git add .
git commit -m "Initial commit: Supply Chain Risk Monitor"

# Connect to your GitHub repo (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/supply-chain-risk-monitor.git
git branch -M main
git push -u origin main
```

### Verify on GitHub:
- Open github.com/YOUR_USERNAME/supply-chain-risk-monitor
- You should see all your files
- Confirm `.env` is NOT there (that would expose your API keys)

---

## Step 3: Deploy on Streamlit Cloud

1. Go to **share.streamlit.io** (or streamlit.io/cloud)
2. Click "Sign in with GitHub" and authorize Streamlit
3. Click **"New app"**
4. Fill in the form:
   - **Repository:** YOUR_USERNAME/supply-chain-risk-monitor
   - **Branch:** main
   - **Main file path:** Risk_Monitor.py
5. Click **"Advanced settings"** — this is where you add your secrets

> **Already deployed under the old `app.py` name?** Renaming the file in the repo doesn't update an existing Streamlit Cloud app automatically - go to your app → ⋮ menu → **Settings** → **General** and change **Main file path** to `Risk_Monitor.py`, then save (this triggers a redeploy).

---

## Step 4: Add Your Secrets (API Keys)

In Streamlit Cloud, your `.env` file doesn't work. Instead, you use Streamlit's built-in secrets system.

In the "Advanced settings" during deployment (or in your app settings later):

Click **"Secrets"** and paste this:

```toml
# Streamlit Secrets format (TOML, not .env format)
FRED_API_KEY = "your_actual_fred_key_here"
ALPHA_VANTAGE_KEY = "your_actual_alpha_vantage_key_here"
NEWS_API_KEY = "your_actual_newsapi_key_here"
GROQ_API_KEY = "your_actual_groq_key_here"
TRADE_GOV_API_KEY = "your_actual_trade_gov_key_here"
```

`GROQ_API_KEY` and `TRADE_GOV_API_KEY` are optional — without `GROQ_API_KEY` the app would try to call Ollama, which doesn't exist on Streamlit Cloud, so set it for the deployed app even though it's optional locally. Without `TRADE_GOV_API_KEY`, Supplier Compliance Status just shows "Not checked" rather than failing.

### Update your Python code to read Streamlit secrets:

Streamlit Cloud stores secrets in `st.secrets`, not environment variables. The actual implementation, `src/config.py`:

```python
import os
from dotenv import load_dotenv

load_dotenv()  # reads .env when running locally; harmless no-op on Streamlit Cloud

def get_secret(key):
    # Try Streamlit secrets first (production), fall back to env vars (local).
    # st.secrets isn't available (or raises) outside a Streamlit run context,
    # hence importing it inside the try and catching broadly.
    try:
        import streamlit as st
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key)

FRED_API_KEY = get_secret("FRED_API_KEY")
ALPHA_VANTAGE_KEY = get_secret("ALPHA_VANTAGE_KEY")
NEWS_API_KEY = get_secret("NEWS_API_KEY")
GROQ_API_KEY = get_secret("GROQ_API_KEY")
TRADE_GOV_API_KEY = get_secret("TRADE_GOV_API_KEY")
```

This means the same code works both locally (reads from `.env`) and on Streamlit Cloud (reads from secrets).

---

## Step 5: Deploy

Click **"Deploy!"** on Streamlit Cloud.

The first deployment takes 2-5 minutes while it installs all your packages. You'll see a log showing the process.

When it finishes, you'll see your app at:
```
https://[your-app-name].streamlit.app
```

---

## Updating the App After Deployment

Any time you push code to GitHub, Streamlit Cloud automatically redeploys:

```bash
# Make changes to your code, then:
git add .
git commit -m "Add commodity price caching"
git push
```

Streamlit Cloud detects the push and redeploys in about 1-2 minutes. You'll see a "Rerunning" indicator in the app while it updates.

---

## Customizing Your App URL

By default, your URL will be something like:
```
https://supply-chain-risk.streamlit.app
```

You can customize the subdomain in your app settings. Aim for something professional:
- `supply-chain-risk-monitor.streamlit.app`
- `scm-risk-dashboard.streamlit.app`
- `yourlastname-risk-monitor.streamlit.app`

---

## Common Deployment Issues and Fixes

**"ModuleNotFoundError: No module named X"**
- Your `requirements.txt` is missing a package
- Add it to requirements.txt and push again

**"Error: invalid API key"**
- Your secrets aren't saved correctly in Streamlit Cloud
- Go to your app settings → Secrets → verify the keys are there exactly as they appear in your `.env`

**"Connection error" for APIs**
- Some API endpoints occasionally go down. Add error handling (see [docs/05-AI-SUMMARY.md](05-AI-SUMMARY.md) → Error Handling)
- Your app should still show something even if one API is down

**App is slow (takes 10+ seconds to load)**
- You're calling APIs on every page load without caching
- Add `@st.cache_data(ttl=3600)` to your data-fetching functions

```python
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_commodity_prices_cached(industry):
    return get_commodity_prices(industry)  # Your actual function
```

**Free tier app "goes to sleep"**
- Streamlit free tier apps go to sleep after 7 days without traffic
- They wake up again when someone opens the URL (takes 30-60 seconds)
- This is fine for a portfolio project
- If you want it always-on, you can set up a free uptime monitor (like UptimeRobot) to ping it every hour

---

## Security Checklist Before Deploying

- [ ] `.env` is in `.gitignore` and NOT in your GitHub repo
- [ ] API keys are only in Streamlit Secrets, not hardcoded in any Python file
- [ ] No personal information is stored or logged
- [ ] GitHub repo is public (Streamlit free hosting requires this)
- [ ] README doesn't contain any API keys

---

## After Deployment: Test Everything

1. Open the live URL on a fresh browser (incognito) where you're not logged in
2. Test a few of the 11 industries
3. Test on your phone — recruiters may view on mobile
4. Check that all charts render, including the Geopolitical Map and the Dashboard Visualization charts
5. Check that the AI summary generates (confirms `GROQ_API_KEY` is set correctly)
6. Check what happens when you type a company name (both a real one and a made-up one — it should say "not known" for the fake one, not invent details)
7. Download both the PDF and Excel exports and confirm the charts/map embedded inside them actually rendered (this is the one thing most likely to silently fail if `packages.txt` didn't take effect — see "Common Deployment Issues" if a chart is missing)

---

## Your Live URL

After deployment, your URL goes here. Update this file when you have it.

**Live App URL:** ________________________________

Put this on your resume, LinkedIn, and GitHub README.

Next: [docs/07-RESUME-AND-PITCH.md](07-RESUME-AND-PITCH.md) — How to use this project to get hired.
