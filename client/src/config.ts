/** @format */

const configuredApiUrl = (import.meta.env.VITE_API_URL || "")
	.trim()
	.replace(/\/+$/, "");

// In production, default to same-origin (/api/*) so Vercel rewrites can proxy to backend.
// In local dev, default to localhost backend if no env var is provided.
export const API_URL = import.meta.env.DEV
  ? (configuredApiUrl || 'http://localhost:8000')
  : '';
export const MIN_RESPONSE_LENGTH = 50;
