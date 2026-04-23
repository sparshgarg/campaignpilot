# CampaignPilot Web Frontend

Premium React frontend for CampaignPilot multi-agent marketing orchestration system.

**Design:** Gong.io energy + Meta minimalism  
**Stack:** React 18 + Vite + CSS-in-JS  
**Deployment:** Vercel / Netlify / Node.js server

---

## Local Development

### Prerequisites
- Node.js 18+ and npm/yarn
- FastAPI backend running on `localhost:8000`

### Setup

```bash
cd web
npm install
npm run dev
```

The app will run at `http://localhost:3000` with hot module reload.

**API Proxy:** Vite automatically proxies `/api` requests to `http://localhost:8000` (see `vite.config.js`).

---

## Build

```bash
npm run build
```

Creates optimized production build in `dist/` folder.

---

## Deployment

### Vercel (Recommended)

1. Push to GitHub
2. Connect repo to [vercel.com](https://vercel.com)
3. Set environment variables:
   ```
   VITE_API_URL=https://api.campaignpilot.com
   ```
4. Deploy

### Netlify

```bash
npm run build
netlify deploy --prod --dir=dist
```

### Docker

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "preview"]
```

### Environment Variables

Create `.env.local` for development:
```
VITE_API_URL=http://localhost:8000
```

For production, set via deployment platform.

---

## Project Structure

```
web/
├── index.html           # Entry point
├── main.jsx             # React app root
├── vite.config.js       # Vite config
├── package.json         # Dependencies
├── styles.css           # Global styles
├── components/          # React components
│   ├── Nav.jsx
│   ├── Hero.jsx
│   ├── Bento.jsx
│   ├── AgentShowcase.jsx
│   ├── Workflow.jsx
│   ├── MetricBand.jsx
│   ├── Ribbon.jsx
│   └── Cta.jsx
└── README.md            # This file
```

---

## API Integration

The frontend communicates with the FastAPI backend at `/api`:

- `POST /agents/strategist/run` — Run Strategist agent
- `POST /agents/creative/run` — Run Creative agent
- `POST /agents/analyst/run` — Run Analyst agent
- `POST /agents/optimizer/run` — Run Optimizer agent
- `POST /agents/ab-test/run` — Run A/B Testing agent

### WebSocket (Real-time Events)

For live event streaming, connect to `WS /ws/agent-events`:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/agent-events');
ws.onmessage = (event) => {
  const agentEvent = JSON.parse(event.data);
  console.log(agentEvent); // {type, timestamp, ...}
};
```

---

## Styling

Global styles in `styles.css` with Gong+Meta design system:
- **Colors:** #6366F1 (indigo), #EC4899 (pink), #F59E0B (amber), #0A0A0A (text)
- **Fonts:** Plus Jakarta Sans (headlines), Inter (body)
- **Components:** Bento cards, glassmorphism nav, gradient text

---

## ESLint & Linting

```bash
npm run lint
```

---

## Troubleshooting

**Port 3000 already in use:**
```bash
VITE_PORT=3001 npm run dev
```

**API calls failing:**
- Ensure FastAPI backend is running on `http://localhost:8000`
- Check browser DevTools → Network tab
- Verify `vite.config.js` proxy is configured correctly

**Build size too large:**
```bash
npm install --save-dev vite-plugin-compression
```

---

## Next Steps

1. ✅ Set up React + Vite
2. 🔄 Wire components to FastAPI endpoints
3. 📡 Add WebSocket for real-time event streaming
4. 🚀 Deploy to Vercel/Netlify
5. 📊 Add state management (Redux/Zustand) if needed
