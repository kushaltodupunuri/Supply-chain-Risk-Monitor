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
1. All code working locally (`streamlit run app.py` works with no errors)
2. A GitHub account (free at github.com)
3. A Streamlit Cloud account (free at streamlit.io/cloud)
4. All API keys ready

---

## Step 1: Prepare Your Repository

### Create requirements.txt

This tells Streamlit Cloud what Python packages to install:

```bash
# Run this in your project folder
pip freeze > requirements.txt
```

Or write it manually (cleaner):

```
streamlit>=1.28.0
plotly>=5.17.0
pandas>=2.0.0
requests>=2.31.0
anthropic>=0.20.0
python-dotenv>=1.0.0
```

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
├── app.py              ← MUST be here, this is what Streamlit runs
├── requirements.txt    ← MUST be here
├── .gitignore          ← MUST be here (protects your .env)
├── .env                ← NOT committed to GitHub (in .gitignore)
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
   - **Main file path:** app.py
5. Click **"Advanced settings"** — this is where you add your secrets

---

## Step 4: Add Your Secrets (API Keys)

In Streamlit Cloud, your `.env` file doesn't work. Instead, you use Streamlit's built-in secrets system.

In the "Advanced settings" during deployment (or in your app settings later):

Click **"Secrets"** and paste this:

```toml
# Streamlit Secrets format (TOML, not .env format)
FRED_API_KEY = "your_actual_fred_key_here"
ALPHA_VANTAGE_KEY = "your_actual_alpha_key_here"
BLS_API_KEY = "your_actual_bls_key_here"
ANTHROPIC_API_KEY = "your_actual_anthropic_key_here"
```

### Update your Python code to read Streamlit secrets:

Streamlit Cloud stores secrets in `st.secrets`, not environment variables. You need to handle both cases:

```python
import os
import streamlit as st
from dotenv import load_dotenv

# Load from .env when running locally
load_dotenv()

def get_secret(key):
    # Try Streamlit secrets first (production), fall back to env vars (local)
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        return os.getenv(key)

FRED_API_KEY = get_secret("FRED_API_KEY")
ALPHA_KEY = get_secret("ALPHA_VANTAGE_KEY")
BLS_KEY = get_secret("BLS_API_KEY")
ANTHROPIC_KEY = get_secret("ANTHROPIC_API_KEY")
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
2. Test all 5 industries
3. Test on your phone — recruiters may view on mobile
4. Check that all charts render
5. Check that the AI summary generates
6. Check what happens when you type a company name

---

## Your Live URL

After deployment, your URL goes here. Update this file when you have it.

**Live App URL:** ________________________________

Put this on your resume, LinkedIn, and GitHub README.

Next: [docs/07-RESUME-AND-PITCH.md](07-RESUME-AND-PITCH.md) — How to use this project to get hired.
