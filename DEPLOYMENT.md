# Streamlit Cloud Deployment Guide

This guide walks you through deploying CampaignPilot's Streamlit UI to Streamlit Cloud in 5 minutes.

## Prerequisites

- GitHub account with this repo pushed (`main` branch)
- Anthropic API key with available credits
- Optional: Langfuse keys for observability

## Step 1: Create Streamlit Cloud Account

1. Go to **[streamlit.io/cloud](https://streamlit.io/cloud)**
2. Click **Sign in** → **Sign in with GitHub**
3. Authorize Streamlit to access your GitHub account
4. You should be taken to the Streamlit Cloud dashboard

## Step 2: Deploy Your App

1. Click **"New app"** button
2. **Repository:** Select `sparshgarg/campaignpilot` (or your fork)
3. **Branch:** Select `main`
4. **Main file path:** Enter `app.py`
5. Click **"Deploy"**

Streamlit Cloud will now:
- Clone your repo
- Install dependencies from `requirements.txt`
- Run `streamlit run app.py`
- Give you a live URL (e.g., `https://campaignpilot-xxx.streamlit.app`)

This typically takes 1-2 minutes. You'll see a build log in the browser.

## Step 3: Configure Secrets

Your app needs API keys to work. Streamlit Cloud keeps these secure via the Secrets manager.

1. In Streamlit Cloud dashboard, click your app
2. Click **Settings** (gear icon in top right)
3. Click **Secrets**
4. Paste the following, replacing with your actual keys:

```toml
ANTHROPIC_API_KEY = "sk-ant-..."
```

Optional (for observability):
```toml
LANGFUSE_PUBLIC_KEY = "pk-..."
LANGFUSE_SECRET_KEY = "sk-..."
```

5. Click **Save**
6. Streamlit will automatically reboot your app

**Security note:** Secrets are encrypted and never exposed in logs or code. Each app has its own secrets.

## Step 4: Test Your Deployment

1. Go to your app URL
2. You should see the CampaignPilot home page
3. Click **Strategist** agent
4. Fill in:
   - Campaign Goal: "Increase SaaS signups"
   - Budget: 5000
   - Timeline: 30 days
   - Target Segment: "B2B marketing teams"
5. Click **Generate Strategic Brief**
6. Watch the real-time event timeline stream live! ✨

If you see the live events streaming with tokens, latencies, and tool calls—**deployment successful!**

## Troubleshooting

### "ModuleNotFoundError: No module named 'agents'"

**Cause:** The app can't find local modules.

**Fix:** Ensure `app.py` is at the root of your repo (not in a subdirectory). Streamlit Cloud uses the repo root as the working directory.

### "ANTHROPIC_API_KEY not set"

**Cause:** Secrets not configured.

**Fix:** Go to Settings → Secrets and add your key. Restart the app (click the 3 dots → Reboot app).

### "Connection refused" for database/ChromaDB

**Cause:** Your local database isn't accessible from Streamlit Cloud.

**Why it happens:** The Strategist agent works without a database, but other agents may need one.

**Fix:** For now, just use the Strategist agent. If you want other agents working, you'll need to:
- Deploy a cloud PostgreSQL (e.g., AWS RDS, Heroku Postgres, Supabase)
- Update `DATABASE_URL` in Secrets
- Or deploy the FastAPI backend separately (see below)

### App is slow or times out

**Cause:** Streamlit Cloud has limited resources (1 CPU, 1GB RAM).

**Fix:**
- This is normal for complex agentic workflows. Agent execution takes 10-30 seconds.
- Consider deploying FastAPI as a separate service for heavier operations (see below)

## Optional: Deploy FastAPI Backend Separately

The Streamlit UI can also call FastAPI endpoints instead of running agents directly.

### Deploy to Render (Free Tier)

1. Go to [render.com](https://render.com)
2. Sign in with GitHub
3. Click **New** → **Web Service**
4. Select this repository
5. Configure:
   - **Name:** `campaignpilot-api`
   - **Runtime:** Python 3.11
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn api.main:app --host 0.0.0.0 --port 8000`
   - **Environment variables:** Add `ANTHROPIC_API_KEY=...`
6. Click **Create Web Service**

Once deployed, you'll get a URL like `https://campaignpilot-api.onrender.com`.

Update your Streamlit Secrets to use this endpoint:
```toml
FASTAPI_URL = "https://campaignpilot-api.onrender.com"
```

Then modify `app.py` to call the API instead of running agents locally (currently it runs agents directly).

## Alternative Cloud Platforms

| Platform | Free Tier | Setup Time | Cold Start | Best For |
|----------|-----------|------------|-----------|----------|
| **Render** | ✅ Yes (1GB RAM) | 2 min | ~10s | Budget-conscious |
| **Railway** | ✅ $5/month credit | 2 min | ~5s | Balanced |
| **Fly.io** | ✅ 3 shared CPUs | 5 min | ~2s | Performance |
| **AWS Lambda** | ✅ Free tier (1M invokes) | 10 min | ~1s (cold) | Serverless |

## Monitoring & Logs

In Streamlit Cloud:
1. Click your app
2. View **Logs** tab at the top

For production monitoring:
- Enable Langfuse (set `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY`)
- Go to [langfuse.com](https://langfuse.com) to see token counts, latencies, and traces

## Updates & Redeployment

**Automatic redeployment:** Every time you push to `main` branch, Streamlit Cloud automatically redeploys (no action needed).

```bash
git add .
git commit -m "Fix bug"
git push origin main
# Streamlit Cloud will redeploy automatically in ~1 min
```

**Manual redeploy:** Click the 3 dots menu → **Reboot app**.

## Cost Breakdown

| Service | Cost |
|---------|------|
| Streamlit Cloud (UI) | **Free** (always) |
| Anthropic API (Claude Haiku) | ~$0.01-0.50/month (depends on usage) |
| FastAPI (Render free tier) | **Free** (sleeps after 15 min inactivity) |
| PostgreSQL (local only) | **Free** (included in docker-compose) |

**Total monthly cost:** ~$0-1 (Anthropic only, if you use it a lot)

---

## Next Steps

1. ✅ Deploy Streamlit UI to Streamlit Cloud (this guide)
2. 🔄 Test with Strategist agent
3. 📦 Deploy FastAPI backend (optional, for other agents)
4. 🔗 Connect n8n for workflow orchestration (optional)

**Done!** You now have a live, publicly accessible CampaignPilot UI. 🚀
