# CampaignPilot

Premium multi-agent marketing campaign orchestration system powered by Claude AI.

**Design:** Gong.io energy + Meta minimalism  
**Stack:** FastAPI (backend) + Streamlit (UI) + PostgreSQL + ChromaDB  
**Agents:** Strategist, Creative, Analyst, Optimizer, A/B Testing

---

## Quick Start (Local)

### Prerequisites
- Python 3.11+
- Docker & Docker Compose (for PostgreSQL + ChromaDB)
- Anthropic API key

### Setup

1. **Clone & install**
   ```bash
   git clone <repo-url>
   cd CampaignPilot
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys:
   # - ANTHROPIC_API_KEY: Your Claude API key
   # - LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY: Optional observability
   ```

3. **Start infrastructure**
   ```bash
   docker-compose up -d
   ```

4. **Run Streamlit UI**
   ```bash
   streamlit run app.py
   ```

5. **(Optional) Start FastAPI backend**
   ```bash
   uvicorn api.main:app --reload --port 8000
   ```

The UI will be available at `http://localhost:8501`

---

## Deployment

### Streamlit Cloud (UI)

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Deploy to Streamlit Cloud"
   git push origin main
   ```

2. **Create Streamlit Cloud account**
   - Go to [streamlit.io/cloud](https://streamlit.io/cloud)
   - Sign in with GitHub
   - Click "New app" → Select this repo

3. **Configure secrets**
   - In Streamlit Cloud dashboard, go to Settings → Secrets
   - Add:
     ```toml
     ANTHROPIC_API_KEY = "sk-..."
     LANGFUSE_PUBLIC_KEY = "..."
     LANGFUSE_SECRET_KEY = "..."
     DATABASE_URL = "postgresql://..."
     CHROMA_HOST = "..."
     CHROMA_PORT = 8000
     ```

4. **Deploy**
   - Streamlit Cloud auto-deploys on every push to `main`

### FastAPI Backend (Backend)

For local development, run:
```bash
uvicorn api.main:app --reload --port 8000
```

For cloud deployment, consider:
- **Render** (free tier available): `pip install -r requirements.txt && uvicorn api.main:app --host 0.0.0.0 --port 8000`
- **Railway** (pay-as-you-go)
- **Fly.io** (generous free tier)

Update Streamlit Cloud secrets with the live backend URL if deploying to cloud.

---

## Architecture

### Agents
- **Strategist:** Campaign strategy & planning
- **Creative:** Ad copy & visual concept generation
- **Analyst:** Data analysis & insights
- **Optimizer:** Campaign optimization recommendations
- **A/B Testing:** Test design & statistical analysis

### Tech Stack
- **LLM:** Anthropic Claude (Haiku for cost efficiency)
- **UI:** Streamlit (Python-based, premium design system)
- **API:** FastAPI (async Python)
- **Database:** PostgreSQL (campaigns, results)
- **Vector DB:** ChromaDB (knowledge base search)
- **Observability:** Langfuse (token tracking, latency)
- **Orchestration:** n8n (visual workflows)

### Real-time Observability

The Streamlit UI streams agent execution in real-time via event callbacks:
- Agent initialization
- LLM calls (with token counts, latency)
- Tool execution (with duration, output preview)
- Completion with cost estimate

Events are displayed in a live timeline with elapsed timestamps and color-coded badges.

---

## Environment Variables

See `.env.example` for all required variables:

| Variable | Required | Local | Cloud |
|----------|----------|-------|-------|
| `ANTHROPIC_API_KEY` | ✓ | Local | Secrets |
| `LANGFUSE_PUBLIC_KEY` | Optional | Local | Secrets |
| `LANGFUSE_SECRET_KEY` | Optional | Local | Secrets |
| `DATABASE_URL` | Optional* | Local | Secrets |
| `CHROMA_HOST` | Optional* | Local | Secrets |

*Required if using database features (optional in Streamlit-only mode)

---

## Troubleshooting

**Streamlit Cloud: ModuleNotFoundError**
- Ensure all dependencies are in `requirements.txt`
- Check that imports are using correct package names

**Streamlit Cloud: Connection refused (DB/ChromaDB)**
- For cloud deployment, you'll need to connect to cloud versions of PostgreSQL + ChromaDB
- Update `DATABASE_URL` and `CHROMA_HOST` in Streamlit Cloud Secrets

**Local: Port already in use**
```bash
# Kill process on port 8501 (Streamlit)
lsof -ti:8501 | xargs kill -9

# Kill process on port 8000 (FastAPI)
lsof -ti:8000 | xargs kill -9
```

---

## Development

### Project Structure
```
CampaignPilot/
├── app.py                 # Streamlit UI (main entry point)
├── agents/                # Agent implementations
│   ├── base_agent.py     # Abstract base class
│   ├── strategist.py     # Strategist agent
│   ├── creative.py       # Creative agent
│   └── ...
├── api/                   # FastAPI backend
│   ├── main.py           # FastAPI app
│   └── routes/           # Endpoint definitions
├── brands/               # Brand knowledge bases
├── data/                 # Synthetic data generators
├── evals/                # Evaluation framework
├── orchestration/        # n8n workflow JSONs
├── requirements.txt      # Python dependencies
└── .streamlit/          # Streamlit config
```

### Running Tests
```bash
pytest tests/ -v
```

### Code Quality
```bash
ruff check .
black --check .
mypy agents/
```

---

## Support

For issues or feedback, open a GitHub issue.

---

**Built with ❤️ using Claude AI**
