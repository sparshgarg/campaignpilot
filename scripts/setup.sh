#!/usr/bin/env bash

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=== Starting CampaignPilot Setup ===${NC}\n"

# 1. Check for required dependencies
echo -e "${BLUE}1. Checking dependencies...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed or not in PATH.${NC}"
    exit 1
fi

if ! command -v uv &> /dev/null; then
    echo -e "${RED}Error: uv is not installed. Please install it (e.g., via 'curl -LsSf https://astral.sh/uv/install.sh | sh').${NC}"
    exit 1
fi
echo -e "${GREEN}✓ All dependencies found.${NC}\n"

# 2. Setup Environment Variables
echo -e "${BLUE}2. Setting up environment...${NC}"
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file. Please ensure you add your ANTHROPIC_API_KEY later.${NC}\n"
else
    echo -e "${GREEN}✓ .env file already exists.${NC}\n"
fi

# 3. Setup Python Virtual Environment
echo -e "${BLUE}3. Setting up Python environment...${NC}"
if [ ! -d .venv ]; then
    uv venv
fi
source .venv/bin/activate
uv pip install -r data/synthetic/requirements.txt || true
uv pip install -r evals/requirements.txt || true
uv pip install anthropic fastapi uvicorn chromadb-client psycopg2-binary sqlalchemy alembic streamlit faker python-dotenv langfuse pytest rich
echo -e "${GREEN}✓ Python dependencies installed.${NC}\n"

# 4. Start Docker Services
echo -e "${BLUE}4. Starting Docker services...${NC}"
docker compose up -d
echo "Waiting for services to be ready (giving PostgreSQL and ChromaDB a moment to start)..."
sleep 10
echo -e "${GREEN}✓ Services started.${NC}\n"

# 5. Initialize Database
echo -e "${BLUE}5. Initializing Database Schema...${NC}"
# Use docker exec to run the schema.sql against the postgres container based on the docker-compose setup
# Container name might vary, we can use docker compose exec
docker compose exec -T postgres psql -U cp_user -d campaignpilot -f /docker-entrypoint-initdb.d/schema.sql || \
docker exec -i $(docker compose ps -q postgres) psql -U cp_user -d campaignpilot < db/schema.sql || \
echo -e "${RED}Could not automatically run schema.sql. Trying python fallback...${NC}"
python -c "
import psycopg2
import os
from dotenv import load_dotenv
load_dotenv('.env')
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
conn.autocommit = True
with conn.cursor() as cur:
    with open('db/schema.sql', 'r') as f:
        cur.execute(f.read())
conn.close()
" || echo "Database might already be initialized."
echo -e "${GREEN}✓ Database initialized.${NC}\n"

# 6. Seed Database
echo -e "${BLUE}6. Generating Synthetic Data & Seeding DB...${NC}"
python data/synthetic/seed_db.py
echo -e "${GREEN}✓ Database seeded.${NC}\n"

# 7. Ingest Knowledge Base
echo -e "${BLUE}7. Ingesting Knowledge Base into ChromaDB...${NC}"
python scripts/ingest_knowledge_base.py
echo -e "${GREEN}✓ Knowledge base ingested.${NC}\n"

echo -e "${BLUE}=== Setup Complete ===${NC}"
echo -e "You can now run:"
echo -e "  ${GREEN}uvicorn api.main:app --reload${NC}          # Start the API"
echo -e "  ${GREEN}streamlit run evals/dashboard/app.py${NC} # Open the Eval Dashboard"
echo -e "  ${GREEN}python evals/runner.py ...${NC}           # Run evaluations"
echo -e "Don't forget to fill in ${GREEN}ANTHROPIC_API_KEY${NC} in your .env file!"
