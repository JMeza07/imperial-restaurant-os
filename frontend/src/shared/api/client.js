/**
 * Shared API Client & HTTP Transport Layer
 * Provides high cohesion for network requests and decoupled domain callers.
 */
export const API_BASE = '/api/v1';

export async function request(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.token ? { Authorization: `Bearer ${options.token}` } : {}),
    ...(options.headers || {}),
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    const message = errorBody.detail || errorBody.message || `Error en solicitud HTTP (${response.status})`;
    throw new Error(typeof message === 'object' ? JSON.stringify(message) : message);
  }

  // Si no hay contenido (204 No Content), regresar null
  if (response.status === 204) return null;
  return response.json();
}
