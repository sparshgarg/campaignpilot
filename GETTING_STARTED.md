# Getting Started with CampaignPilot

## ✅ What's Already Running

1. **Frontend**: http://localhost:5174 (React + Vite)
2. **Backend API**: http://localhost:8001 (FastAPI)
3. **All 5 Agent Consoles**: Strategist, Creative, Analyst, Optimizer, A/B Testing

## ⏳ What You Need to Set Up

1. **PostgreSQL** - Database for run history
2. **ChromaDB** - Vector database for knowledge base (RAG)

---

## 🚀 Quick Start (Docker - 2 minutes)

The easiest way to get everything running is with Docker Compose.

### Step 1: Start Services
```bash
cd /Users/sparshgarg/Desktop/AI\ Projects/CampaignPilot
bash scripts/setup_services.sh
```

This script will:
- Create `docker-compose.yml` (if needed)
- Start PostgreSQL container
- Start ChromaDB container
- Verify both services are healthy
- Show you the next steps

### Step 2: Verify Connection
```bash
curl http://localhost:8001/health | jq .
```

Expected output:
```json
{
  "status": "ok",
  "services": {
    "postgres": true,
    "chromadb": true
  }
}
```

✅ **Done!** Your system is fully configured.

---

## 📚 Documentation Files

Read these files for more details:

| File | Purpose |
|------|---------|
| `EXTERNAL_SERVICES_SETUP.md` | Complete setup guide (Docker, local, cloud options) |
| `web/public/SYSTEM_DOCUMENTATION.html` | Interactive system architecture & testing guide |
| `db/schema.sql` | Database schema with all tables |
| `scripts/setup_services.sh` | Automated setup script (Docker Compose) |

---

## 🔍 Verification Steps

After setup, verify everything is working:

### 1. Check Services Running
```bash
docker-compose ps
# Should show both postgres and chromadb as "Up"
```

### 2. Check Backend Health
```bash
curl http://localhost:8001/health | jq .
# Should show both services as "true"
```

### 3. Open Frontend
```bash
open http://localhost:5174
# Or manually navigate to http://localhost:5174
```

### 4. Test an Agent
- Click "Strategist" button
- Fill in form:
  - Campaign Goal: "Generate 100 MQLs for VP of Infrastructure"
  - Budget: 50000
  - Timeline: 90
  - Target Segment: "Mid-market tech companies"
- Click "Generate Campaign Strategy"
- Watch real-time events stream in the timeline

---

## 🎯 What Happens After Setup

Once services are configured, the system works like this:

```
Frontend Submit Form
         ↓
   POST /agents/{agent}/run
         ↓
Backend Receives Request
         ↓
Returns run_id immediately
         ↓
Frontend Opens WebSocket
         ↓
Agent Executes in Background
         ↓
Real-Time Events Stream
         ↓
Agent Completes
         ↓
Data Persisted to PostgreSQL
         ↓
Results Available in Frontend
```

---

## 🛠️ Troubleshooting

### Docker not found
```bash
# Install Docker from https://www.docker.com/products/docker-desktop
```

### Port already in use
```bash
# Kill existing process on port 5432 (PostgreSQL)
lsof -ti:5432 | xargs kill -9

# Kill existing process on port 8000 (ChromaDB)
lsof -ti:8000 | xargs kill -9
```

### Services won't start
```bash
# Check logs
docker-compose logs postgres
docker-compose logs chromadb

# Restart
docker-compose restart
```

### Backend can't connect to database
```bash
# Verify .env has correct values
cat .env | grep DATABASE_URL
cat .env | grep CHROMA

# Should be:
# DATABASE_URL=postgresql://cp_user:cp_password@localhost:5432/campaignpilot
# CHROMA_HOST=localhost
# CHROMA_PORT=8000
```

---

## 📋 Complete Setup Checklist

- [ ] Docker installed (`docker --version`)
- [ ] Run `bash scripts/setup_services.sh`
- [ ] Both services show as running in `docker-compose ps`
- [ ] Backend health check passes (`curl http://localhost:8001/health`)
- [ ] Frontend loads (`http://localhost:5174`)
- [ ] Test one agent end-to-end
- [ ] Verify run appears in database

---

## 🚀 Next Steps After Full Setup

1. **Load Knowledge Base** (optional but recommended)
   ```bash
   python scripts/load_knowledge_base.py
   ```

2. **Run All Agents**
   - Test all 5 agent consoles
   - Verify WebSocket event streaming works
   - Check database persistence

3. **Read System Documentation**
   - Open `web/public/SYSTEM_DOCUMENTATION.html` in browser
   - Review architecture diagrams
   - Understand data flows

4. **Deploy to Production** (when ready)
   - Follow instructions in `EXTERNAL_SERVICES_SETUP.md`
   - Set up AWS RDS + ChromaDB Cloud
   - Deploy frontend to Vercel/Netlify
   - Deploy backend to Cloud Run/ECS

---

## 📞 Support

For questions about:
- **Services Setup**: See `EXTERNAL_SERVICES_SETUP.md`
- **System Architecture**: See `web/public/SYSTEM_DOCUMENTATION.html`
- **Agent Details**: See backend agent classes in `agents/`
- **API Endpoints**: See `api/routes/agents.py`

---

## 🎉 You're All Set!

Your CampaignPilot system is now configured and ready to use. Start with:

```bash
# 1. Make sure services are running
docker-compose ps

# 2. Open the frontend
open http://localhost:5174

# 3. Test an agent
# Click any agent button and fill in the form
```

Enjoy! 🚀
