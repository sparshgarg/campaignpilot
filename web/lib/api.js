// In production set VITE_API_URL to your backend (e.g. https://x.up.railway.app)
// In local dev this is empty and the Vite proxy handles /api → localhost:8001
const backendUrl = import.meta.env.VITE_API_URL || '';

// REST: use full backend URL in prod, relative /api in dev (Vite proxy)
export const API_BASE = backendUrl || '/api';

// WebSocket: derive from backendUrl so one env var covers both protocols
export const WS_BASE = backendUrl
  ? backendUrl.replace(/^https/, 'wss').replace(/^http/, 'ws')
  : (import.meta.env.VITE_WS_URL || 'ws://localhost:8001');
