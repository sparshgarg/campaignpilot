// REST calls go through the Vite proxy (/api → http://localhost:8001)
// This works in dev and on Vercel (via rewrites to the backend).
export const API_BASE = '/api';

// WebSocket connects directly to the backend (can't be proxied without ws:true in vite.config).
// Override VITE_WS_URL for production deployments.
export const WS_BASE = import.meta.env.VITE_WS_URL || 'ws://localhost:8001';
