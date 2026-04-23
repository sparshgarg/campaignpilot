#!/bin/bash
set -e

echo "🚀 CampaignPilot External Services Setup"
echo "========================================"
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker from https://www.docker.com"
    exit 1
fi

echo "✓ Docker found"

# Check docker-compose
if ! command -v docker-compose &> /dev/null; then
    echo "⚠️  docker-compose not found. Using 'docker compose' instead..."
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Create docker-compose.yml if it doesn't exist
if [ ! -f "docker-compose.yml" ]; then
    echo "📝 Creating docker-compose.yml..."
    cat > docker-compose.yml << 'COMPOSE_EOF'
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
COMPOSE_EOF
    echo "✓ docker-compose.yml created"
else
    echo "✓ docker-compose.yml already exists"
fi

# Start services
echo ""
echo "🚀 Starting services..."
$DOCKER_COMPOSE up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check PostgreSQL
echo ""
echo "🔍 Checking PostgreSQL..."
if $DOCKER_COMPOSE exec -T postgres pg_isready -U cp_user > /dev/null 2>&1; then
    echo "✓ PostgreSQL is ready"
else
    echo "⚠️  PostgreSQL is starting, this may take a moment..."
    sleep 10
fi

# Check ChromaDB
echo ""
echo "🔍 Checking ChromaDB..."
if curl -s http://localhost:8000/api/v1/heartbeat > /dev/null; then
    echo "✓ ChromaDB is ready"
else
    echo "⚠️  ChromaDB is starting, this may take a moment..."
    sleep 5
fi

echo ""
echo "✅ Services started successfully!"
echo ""
echo "📊 Service Status:"
$DOCKER_COMPOSE ps
echo ""
echo "🎯 Next steps:"
echo "1. Verify backend connections:"
echo "   curl http://localhost:8001/health | jq ."
echo ""
echo "2. Load knowledge base (optional):"
echo "   python scripts/load_knowledge_base.py"
echo ""
echo "3. Open frontend:"
echo "   http://localhost:5174"
echo ""
echo "⏹️  To stop services:"
echo "   docker-compose down"
