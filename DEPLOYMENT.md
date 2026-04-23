# React Frontend Deployment Guide

This guide walks you through deploying CampaignPilot's React frontend to Vercel or Netlify.

## Quick Start: Deploy to Vercel (Recommended)

### Prerequisites

- GitHub account with this repo pushed (`main` branch)
- Vercel account (free at [vercel.com](https://vercel.com))
- Anthropic API key

### Step 1: Connect GitHub to Vercel

1. Go to [vercel.com](https://vercel.com)
2. Click **Sign up** → **Sign up with GitHub**
3. Authorize Vercel to access your GitHub
4. Click **Add new** → **Project**
5. Select the `campaignpilot` repository
6. Click **Import**

### Step 2: Configure Build Settings

Vercel should auto-detect the `web` folder:

- **Framework preset:** Vite
- **Root directory:** `web`
- **Build command:** `npm run build`
- **Output directory:** `dist`

If not auto-detected, set manually.

### Step 3: Add Environment Variables

1. In project settings, go to **Settings** → **Environment Variables**
2. Add your variables:
   ```
   VITE_API_URL=https://api.campaignpilot.com
   ```
   (Replace with your actual backend URL)

3. Click **Save**

### Step 4: Deploy

Click **Deploy** button. Vercel will:
- Clone your repo
- Install dependencies (`npm install`)
- Build the app (`npm run build`)
- Deploy to a live URL (e.g., `https://campaignpilot.vercel.app`)

Deployment typically takes 1-2 minutes. Your UI is now live!

---

## Alternative: Deploy to Netlify

1. Go to [netlify.com](https://netlify.com)
2. Click **New site from Git** → Select GitHub → Select `campaignpilot`
3. Build settings:
   - **Base directory:** `web`
   - **Build command:** `npm run build`
   - **Publish directory:** `dist`
4. Add environment variables (same as above)
5. Click **Deploy site**

---

## Deploy FastAPI Backend

While the React frontend is now deployed to Vercel/Netlify, you need the FastAPI backend running somewhere.

### Option A: Render (Recommended, Free Tier)

1. Go to [render.com](https://render.com)
2. Click **New** → **Web Service**
3. Connect your GitHub account and select `campaignpilot` repo
4. Settings:
   - **Name:** `campaignpilot-api`
   - **Environment:** Python 3.11
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn api.main:app --host 0.0.0.0 --port 8000`
5. Add environment variables:
   - `ANTHROPIC_API_KEY`
   - `DATABASE_URL` (if using cloud PostgreSQL)
   - `CHROMA_HOST` (if using cloud ChromaDB)
6. Click **Create Web Service**

Render gives you a URL like `https://campaignpilot-api.onrender.com`.

### Option B: Railway

1. Go to [railway.app](https://railway.app)
2. Connect GitHub repo
3. Set start command: `uvicorn api.main:app --host 0.0.0.0`
4. Deploy

### Option C: Fly.io

```bash
flyctl auth login
flyctl launch  # Generates fly.toml
flyctl deploy
```

---

## Connect Frontend to Backend

After deploying your backend, update the frontend:

1. Get your backend URL (e.g., `https://campaignpilot-api.onrender.com`)
2. In your Vercel/Netlify project:
   - Go to Settings → Environment Variables
   - Update `VITE_API_URL` to your backend URL
   - Redeploy

The frontend will now call your deployed backend API.

---

## Testing Your Deployment

1. Go to your frontend URL (e.g., `https://campaignpilot.vercel.app`)
2. You should see the CampaignPilot home page with all components
3. Click **Launch console** button
4. Fill in campaign details and click an agent button
5. Verify the agent runs successfully and returns results

---

## Troubleshooting

### "Cannot find module 'react'"

**Cause:** Dependencies not installed or `node_modules` missing.

**Fix:** 
- Vercel/Netlify auto-run `npm install`
- Check build logs for errors
- Ensure `web/package.json` is present and valid

### API calls failing (Network error)

**Cause:** `VITE_API_URL` not set or points to wrong backend.

**Fix:**
- Set `VITE_API_URL` environment variable correctly
- Verify backend is deployed and running
- Check browser DevTools → Network tab
- Verify CORS is enabled on backend

### "Cannot GET /" after deployment

**Cause:** Build output directory wrong or build failed.

**Fix:**
- Ensure output directory is `dist` (not `build` or other)
- Check build logs in deployment provider
- Verify `vite.config.js` is correct

### Port 3000 already in use (local dev)

```bash
cd web
VITE_PORT=3001 npm run dev
```

---

## Cost Breakdown

| Service | Cost |
|---------|------|
| Vercel (Frontend) | **Free** (always) |
| Render (Backend) | **Free** (sleeps after 15 min inactivity) |
| Anthropic API (Claude Haiku) | ~$0.01-0.50/month |
| PostgreSQL (Render addon) | **$7/month** (optional) |
| ChromaDB | **$0** (use local or Render instance) |

**Minimum:** ~$0 (free tier only)  
**With database:** ~$7-10/month

---

## Monitoring & Observability

Enable Langfuse for production monitoring:

1. Set environment variables on backend:
   - `LANGFUSE_PUBLIC_KEY`
   - `LANGFUSE_SECRET_KEY`
2. Go to [langfuse.com](https://langfuse.com) dashboard
3. View token counts, latencies, error rates, and execution traces

---

## Auto-Deploy on Push

Both Vercel and Netlify automatically redeploy when you push to `main` branch.

```bash
git add .
git commit -m "Update UI"
git push origin main
# Vercel/Netlify redeploys automatically in ~2 min
```

---

## Next Steps

✅ Deploy React frontend to Vercel  
✅ Deploy FastAPI backend to Render  
🔄 Connect frontend to backend API  
📡 Test agents work end-to-end  
🎯 Iterate on features

---

## Next Steps

1. ✅ Deploy Streamlit UI to Streamlit Cloud (this guide)
2. 🔄 Test with Strategist agent
3. 📦 Deploy FastAPI backend (optional, for other agents)
4. 🔗 Connect n8n for workflow orchestration (optional)

**Done!** You now have a live, publicly accessible CampaignPilot UI. 🚀
