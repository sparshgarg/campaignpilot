# External Services Setup Guide

## Overview
CampaignPilot requires two external services:
1. **PostgreSQL** - Database for run history, campaigns, and performance data
2. **ChromaDB** - Vector database for knowledge base (RAG - Retrieval Augmented Generation)

This guide covers local setup (easiest for development) and cloud deployment options.

---

## Quick Start (Docker - Recommended for Development)

### Prerequisites
- Docker installed and running
- Docker Compose (optional, simplifies setup)

### Option 1: Using Docker Compose (Easiest)

Create a file `docker-compose.yml` in your project root:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: campaignpilot_db
    environment:
      POSTGRES_USER: cp_user
      POSTGRES_PASSWORD: cp_password
      POSTGRES_DB: campaignpilot
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./db/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U cp_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  chromadb:
    image: ghcr.io/chroma-core/chroma:latest
    container_name: campaignpilot_chromadb
    environment:
      CHROMA_HOST: 0.0.0.0
      CHROMA_PORT: 8000
    ports:
      - "8000:8000"
    volumes:
      - chromadb_data:/chroma/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/heartbeat"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  chromadb_data:
```

**Start services:**
```bash
docker-compose up -d
```

**Verify services are running:**
```bash
docker-compose ps
# Should show both postgres and chromadb as "running"
```

**Check backend logs to confirm connections:**
```bash
tail -20 /tmp/backend.log
# Should show: "PostgreSQL connection: OK" and "ChromaDB connection: OK"
```

**Stop services:**
```bash
docker-compose down
```

---

## Option 2: Local Installation (macOS)

### PostgreSQL Setup

**Install via Homebrew:**
```bash
brew install postgresql@15
```

**Start PostgreSQL service:**
```bash
brew services start postgresql@15
```

**Create database and user:**
```bash
# Connect to PostgreSQL
psql postgres

# In psql prompt:
CREATE USER cp_user WITH PASSWORD 'cp_password';
CREATE DATABASE campaignpilot OWNER cp_user;
GRANT ALL PRIVILEGES ON DATABASE campaignpilot TO cp_user;
\q
```

**Load schema:**
```bash
psql -U cp_user -d campaignpilot -f db/schema.sql
```

**Verify connection:**
```bash
psql -U cp_user -d campaignpilot -c "SELECT version();"
```

### ChromaDB Setup

**Install via pip:**
```bash
pip install chromadb
```

**Start ChromaDB server:**
```bash
chroma run --host localhost --port 8000
```

This will run in foreground. Open a new terminal to continue.

**Verify ChromaDB is accessible:**
```bash
curl http://localhost:8000/api/v1/heartbeat
# Should return: {"status": "ok"}
```

---

## Option 3: Cloud Deployment

### PostgreSQL on AWS RDS

**Create RDS instance:**
1. Go to AWS RDS console
2. Click "Create database"
3. Select "PostgreSQL" → Version 15
4. Select "Burstable classes" (db.t3.micro for dev)
5. Set:
   - DB instance identifier: `campaignpilot-db`
   - Master username: `cp_user`
   - Master password: `<secure-password>`
6. Create publicly accessible parameter set
7. Create DB security group allowing port 5432
8. Click "Create database"

**Get connection details:**
```bash
# From RDS console, get endpoint like:
# campaignpilot-db.xxxxx.us-east-1.rds.amazonaws.com:5432

# Update .env:
DATABASE_URL=postgresql://cp_user:PASSWORD@campaignpilot-db.xxxxx.us-east-1.rds.amazonaws.com:5432/campaignpilot
```

**Initialize database:**
```bash
# From your local machine:
psql -h campaignpilot-db.xxxxx.us-east-1.rds.amazonaws.com \
     -U cp_user \
     -d campaignpilot \
     -f db/schema.sql
```

### ChromaDB Deployment Options

#### Option A: Self-Hosted on EC2
```bash
# On EC2 instance:
sudo apt update
sudo apt install python3-pip
pip install chromadb
chroma run --host 0.0.0.0 --port 8000

# Update security group to allow port 8000
# Update .env:
CHROMA_HOST=<ec2-instance-ip>
CHROMA_PORT=8000
```

#### Option B: Using Chroma Cloud (Managed)
1. Sign up at https://www.trychroma.com
2. Create cluster
3. Get API key
4. Install Chroma client:
```bash
pip install chromadb[cloud]
```

#### Option C: Docker on AWS ECS
Push Docker image and deploy as ECS service with persistent storage.

---

## Database Schema Initialization

The schema is automatically loaded if using `docker-compose` with the volume mount. 

If using local PostgreSQL, manually initialize:

```bash
psql -U cp_user -d campaignpilot -f db/schema.sql
```

**Verify schema:**
```bash
psql -U cp_user -d campaignpilot -c "\dt"
# Should show: agent_runs table
```

---

## Loading Knowledge Base into ChromaDB

After ChromaDB is running, you need to populate it with knowledge base documents.

**Create load script** `scripts/load_knowledge_base.py`:

```python
import chromadb
import os
import json
from datetime import datetime

# Initialize Chroma client
client = chromadb.HttpClient(
    host=os.getenv("CHROMA_HOST", "localhost"),
    port=int(os.getenv("CHROMA_PORT", "8000"))
)

# Create collections
collections = {
    "brand_guidelines": client.get_or_create_collection(
        name="brand_guidelines",
        metadata={"description": "Brand voice, tone, messaging guidelines"}
    ),
    "campaign_history": client.get_or_create_collection(
        name="campaign_history",
        metadata={"description": "Past campaign performance and results"}
    ),
    "benchmarks": client.get_or_create_collection(
        name="benchmarks",
        metadata={"description": "Industry benchmarks by channel"}
    ),
    "creative_examples": client.get_or_create_collection(
        name="creative_examples",
        metadata={"description": "Successful ad copy examples"}
    )
}

# Sample data - replace with real data from your knowledge base
sample_documents = {
    "brand_guidelines": [
        {
            "id": "bg_001",
            "document": "Brand Voice: Professional yet approachable. Tone should be conversational, avoiding corporate jargon. Use active voice, short sentences. Avoid: All caps (except acronyms), exclamation marks, hyperbole.",
            "metadata": {"type": "voice"}
        },
        {
            "id": "bg_002",
            "document": "Key Messaging Pillars: 1. Reduce complexity in cloud operations. 2. Save money without sacrificing performance. 3. Empower engineers with better tools.",
            "metadata": {"type": "messaging"}
        },
        {
            "id": "bg_003",
            "document": "Prohibited Phrases: 'Best-in-class', 'synergy', 'leverage', 'paradigm shift', 'game-changer', 'moving forward'",
            "metadata": {"type": "prohibited"}
        }
    ],
    "benchmarks": [
        {
            "id": "bench_linkedin_001",
            "document": "LinkedIn Performance Benchmarks (B2B): Average CTR: 0.5-1.5%, Average CPC: $3-15, Conversion Rate: 1-3%, Typical ROAS: 2-5x for lead gen campaigns",
            "metadata": {"channel": "LinkedIn"}
        },
        {
            "id": "bench_email_001",
            "document": "Email Performance Benchmarks: Open Rate: 20-30% (B2B), Click Rate: 2-5%, Conversion Rate: 0.5-2%, Cost per recipient: $0.001-0.01",
            "metadata": {"channel": "Email"}
        }
    ],
    "creative_examples": [
        {
            "id": "creative_001",
            "document": "Example LinkedIn headline: 'Reduce cloud costs by 40% — without the complexity'",
            "metadata": {"channel": "LinkedIn", "tone": "professional"}
        }
    ]
}

# Load documents into collections
for collection_name, documents in sample_documents.items():
    if collection_name in collections:
        collection = collections[collection_name]
        for doc in documents:
            collection.add(
                ids=[doc["id"]],
                documents=[doc["document"]],
                metadatas=[doc["metadata"]]
            )
        print(f"✓ Loaded {len(documents)} documents to {collection_name}")

print("✓ Knowledge base loaded successfully!")
```

**Run the script:**
```bash
cd /Users/sparshgarg/Desktop/AI\ Projects/CampaignPilot
python scripts/load_knowledge_base.py
```

**Verify data was loaded:**
```bash
curl http://localhost:8000/api/v1/collections | jq .
# Should show collections with data counts > 0
```

---

## Environment Configuration

Update `.env` file with actual connection strings:

### Local Development
```env
# PostgreSQL
DATABASE_URL=postgresql://cp_user:cp_password@localhost:5432/campaignpilot

# ChromaDB
CHROMA_HOST=localhost
CHROMA_PORT=8000

# API
ANTHROPIC_API_KEY=sk-ant-...
ACTIVE_BRAND=meta

# Optional
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
N8N_HOST=http://localhost:5678
```

### Docker Compose
```env
DATABASE_URL=postgresql://cp_user:cp_password@postgres:5432/campaignpilot
CHROMA_HOST=chromadb
CHROMA_PORT=8000
```

### Cloud (AWS RDS + EC2)
```env
DATABASE_URL=postgresql://cp_user:PASSWORD@campaignpilot-db.xxxxx.us-east-1.rds.amazonaws.com:5432/campaignpilot
CHROMA_HOST=<ec2-instance-public-ip>
CHROMA_PORT=8000
```

**Restart backend for changes to take effect:**
```bash
pkill -f "uvicorn api.main:app"
cd /Users/sparshgarg/Desktop/AI\ Projects/CampaignPilot
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload
```

---

## Verification Checklist

### PostgreSQL
- [ ] Service is running
- [ ] Can connect with: `psql -U cp_user -d campaignpilot`
- [ ] Schema loaded: `\dt` shows `agent_runs` table
- [ ] Backend logs show: "PostgreSQL connection: OK"

### ChromaDB
- [ ] Service is running
- [ ] Can reach heartbeat: `curl http://localhost:8000/api/v1/heartbeat`
- [ ] Collections exist: `curl http://localhost:8000/api/v1/collections`
- [ ] Knowledge base documents loaded (>0 items per collection)
- [ ] Backend logs show: "ChromaDB connection: OK"

### Backend
```bash
curl http://localhost:8001/health | jq .
# Should show:
# {
#   "status": "ok",
#   "services": {
#     "postgres": true,
#     "chromadb": true
#   }
# }
```

---

## Troubleshooting

### PostgreSQL Connection Fails
```bash
# Check PostgreSQL is running
docker-compose ps
# or
brew services list | grep postgres

# Test connection
psql -U cp_user -d campaignpilot -c "SELECT 1;"

# Check .env DATABASE_URL is correct
cat .env | grep DATABASE_URL
```

### ChromaDB Connection Fails
```bash
# Check ChromaDB is running
curl http://localhost:8000/api/v1/heartbeat

# Check CHROMA_HOST and CHROMA_PORT in .env
cat .env | grep CHROMA

# If using Docker:
docker-compose logs chromadb
```

### "Connection refused" on Mac
```bash
# PostgreSQL might need manual start
brew services start postgresql@15

# ChromaDB might be running on different port
netstat -an | grep 8000
```

### Schema errors when loading
```bash
# Drop and recreate database
psql -U cp_user -d postgres -c "DROP DATABASE campaignpilot;"
psql -U cp_user -d postgres -c "CREATE DATABASE campaignpilot;"
psql -U cp_user -d campaignpilot -f db/schema.sql
```

---

## Next Steps After Setup

1. **Verify all services are connected:**
   ```bash
   curl http://localhost:8001/health
   ```

2. **Run end-to-end tests:**
   - Open http://localhost:5174
   - Test all 5 agent consoles
   - Verify WebSocket event streaming works
   - Check that runs are persisted to database

3. **Load more knowledge base data:**
   - Add your actual brand guidelines
   - Add historical campaign data
   - Add industry benchmarks for your verticals

4. **Set up backups:**
   - PostgreSQL: Enable automated backups in RDS or set up pg_dump
   - ChromaDB: Set up periodic exports

5. **Configure monitoring:**
   - Set up CloudWatch (AWS) or equivalent
   - Monitor database performance
   - Set up alerts for connection failures

---

## Production Deployment Recommendations

### Database
- Use **AWS RDS** (PostgreSQL managed service) for reliability
- Enable **Multi-AZ** for high availability
- Set up **automated backups** (30 days retention)
- Use **VPC** for security isolation
- Enable **encryption at rest** and **in transit**

### Vector Database
- Use **Chroma Cloud** (managed) for simplicity
- Or self-host on **ECS/Kubernetes** with persistent storage
- Enable **replication** for high availability
- Set up **backup schedule**

### Overall
- Use **secrets manager** (AWS Secrets Manager, HashiCorp Vault) for credentials
- Never commit `.env` file to git
- Implement **database connection pooling**
- Set up **monitoring and alerting**
- Enable **read replicas** for scaling reads

---

## Quick Reference Commands

```bash
# Docker Compose
docker-compose up -d              # Start services
docker-compose down               # Stop services
docker-compose logs postgres      # View PostgreSQL logs
docker-compose logs chromadb      # View ChromaDB logs
docker-compose ps                 # Check status

# PostgreSQL
psql -U cp_user -d campaignpilot -c "SELECT COUNT(*) FROM agent_runs;"
psql -U cp_user -d campaignpilot -f db/schema.sql

# ChromaDB
curl http://localhost:8000/api/v1/heartbeat
curl http://localhost:8000/api/v1/collections

# Backend Health
curl http://localhost:8001/health | jq .

# Frontend
open http://localhost:5174
```

