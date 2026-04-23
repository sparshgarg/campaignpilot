# CampaignPilot Backend - Priority Work List

## ✅ Already Implemented

- **5 Agents**: Strategist, Creative, Analyst, Optimizer, A/B Testing
- **5 API Endpoints**: `/agents/{strategist,creative,analyst,optimizer,ab-test}/run`
- **3 Tools**: VectorSearchTool, DBQueryTool, SafetyChecker
- **Eval Framework**: Deterministic + LLM judge metrics
- **Base Infrastructure**: FastAPI app, CORS, health checks, Langfuse integration

---

## 🔴 HIGH PRIORITY (Blocking Frontend)

### 1. **Fix StrategistAgent Method Signature** (CRITICAL) ✅
   - **Status**: FIXED - BaseAgent initialization bug corrected
   - **Details**: Moved Anthropic/Langfuse init from _emit() to __init__()
   - **Verified**: Strategist agent tested successfully

### 2. **Fix CreativeAgent Method** ✅
   - **Status**: FIXED - Updated API route with SafetyChecker tool
   - **Details**: Changed CreativeAgent init to use safety_checker_tool instead of db_query_tool
   - **Verified**: Creative agent tested successfully with email channel

### 3. **Wire WebSocket for Real-Time Events** (IMPORTANT FOR UX) ✅
   - **Status**: IMPLEMENTED - Real-time event streaming working
   - **Details**: 
     - Created AgentEventManager in api/websocket.py for connection management
     - WebSocket endpoint at /ws/agent-events/{run_id}
     - Strategist and Creative agents emit events via callback
     - StrategistConsole connects to WebSocket and displays events live
   - **Verified**: 27 events captured during test run

### 4. **Add Run Storage / History** (Frontend Expects This) ✅
   - **Status**: IMPLEMENTED - Database persistence working
   - **Details**: 
     - Created AgentRun SQLAlchemy model in models/run.py
     - Created db/session.py for session management
     - Updated Strategist and Creative routes to save runs to PostgreSQL
     - GET endpoints implemented for retrieving stored runs
   - **Files**: models/run.py, db/session.py
   - **Tables**: agent_runs (run_id, agent_name, input_params, output, latency_ms, etc.)

---

## 🟡 MEDIUM PRIORITY (Quality & Testing)

### 5. **Test All Agent Endpoints** 
   - **Status**: PENDING - Next priority
   - **Action**: Write integration tests, verify JSON output
   - **Time**: ~90 min

### 6. **Add Error Handling in Tools**
   - **Status**: PENDING - Error handling can be improved
   - **Time**: ~30 min

### 7. **Implement Analyst Agent Query Validation**
   - **Status**: PENDING - SQL validation for SELECT-only
   - **Time**: ~30 min

### 8. **Build Creative Agent UI Console** ✅
   - **Status**: COMPLETED - web/pages/CreativeConsole.jsx
   - **Details**: Form with channel, product, persona, tone, key_message fields
   - **Integrated**: Wired to main.jsx and AgentShowcase

### 9. **Build Analyst Agent UI Console** ✅
   - **Status**: COMPLETED - web/pages/AnalystConsole.jsx
   - **Details**: Question input, SQL generation output, insights
   - **Integrated**: Wired to main.jsx and AgentShowcase

### 10. **Build Optimizer Agent UI Console** ✅
   - **Status**: COMPLETED - web/pages/OptimizerConsole.jsx
   - **Details**: Campaign details, remaining budget, optimization recommendations
   - **Integrated**: Wired to main.jsx and AgentShowcase

### 11. **Build A/B Testing Agent UI Console** ✅
   - **Status**: COMPLETED - web/pages/ABTestConsole.jsx
   - **Details**: Experiment design, statistical parameters, power analysis
   - **Integrated**: Wired to main.jsx and AgentShowcase

---

## 🟢 LOW PRIORITY (Polish & Optimization)

### 12. **Add Caching for Vector Search**
   - **Issue**: ChromaDB queries slow on repeated searches
   - **Status**: Not implemented
   - **Action**: Add Redis caching layer
   - **Time**: ~45 min

### 13. **Add Rate Limiting**
   - **Issue**: API has no rate limits
   - **Status**: Not implemented
   - **Action**: Add rate limit middleware
   - **Time**: ~20 min

### 14. **Add Request Logging / Audit Trail**
   - **Issue**: No audit log of who ran what
   - **Status**: Langfuse logs tokens but not full context
   - **Action**: Add middleware to log all requests
   - **Time**: ~30 min

### 15. **Optimize Agent Startup Time**
   - **Issue**: Agent initialization slow (lots of imports)
   - **Status**: Agents load on every request
   - **Action**: Consider agent pooling or lazy loading
   - **Time**: ~60 min (low ROI)

### 16. **Add Database Alembic Migrations**
   - **Issue**: Database schema changes not version controlled
   - **Status**: `db/schema.sql` exists but no migrations
   - **Action**: Generate and test Alembic migrations
   - **Time**: ~45 min

---

## 📊 Priority Score Summary

| # | Task | Blocks Frontend? | Time | Priority |
|---|------|------------------|------|----------|
| 1 | Fix Strategist method | ✅ YES | 15m | 🔴 CRITICAL |
| 2 | Fix Creative method | ✅ YES | 15m | 🔴 CRITICAL |
| 3 | WebSocket real-time | ✅ YES (UX) | 45m | 🔴 HIGH |
| 4 | Add run storage | ~ maybe | 60m | 🔴 HIGH |
| 5 | Test all agents | No | 90m | 🟡 MED |
| 6-11 | Build agent consoles | ✅ YES | 300m | 🟡 MED |
| 12+ | Caching, limits, optimization | No | varies | 🟢 LOW |

---

## Recommended Execution Order

### Phase 1: Get Strategist Working (1-2 hours)
1. Fix Strategist agent endpoint ✓
2. Test with frontend ✓
3. Fix Creative agent endpoint ✓
4. Add WebSocket for live events

### Phase 2: Complete Other Agents (3-4 hours)
5. Build Creative/Analyst/Optimizer/A/B Testing UI consoles
6. Test all endpoints

### Phase 3: Polish & Deploy (2-3 hours)
7. Add run storage
8. Fix error handling
9. Test end-to-end
10. Deploy to Render

---

## Known Issues / Blockers

- [ ] Database credentials: Need PostgreSQL + ChromaDB running for full functionality
- [ ] ANTHROPIC_API_KEY: Must be set for agents to work
- [ ] Langfuse: Optional but recommended for observability
- [ ] N8n: Integration not yet built but endpoints exist

---

## Testing Checklist

- [ ] Strategist endpoint returns valid JSON
- [ ] Creative endpoint returns ad copy variants
- [ ] Analyst endpoint returns SQL + insight
- [ ] Optimizer endpoint returns optimization recommendations  
- [ ] A/B Testing endpoint returns experiment design
- [ ] WebSocket streams events in real-time
- [ ] Run history retrievable via GET endpoint
- [ ] All agents handle errors gracefully
- [ ] Frontend consoles display results correctly
