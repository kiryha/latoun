// Thin API client for the FastAPI backend. All product knowledge lives on the
// backend; this module only transports semantic codes and resolved state.

import type {
  Catalog,
  ConfigurationDetail,
  ConfigurationRequest,
  ConfigurationSummary,
  RenderState,
} from "../types";

// Empty base -> use Vite proxy ("/api"). Override with VITE_API_BASE if needed.
const API_BASE = import.meta.env.VITE_API_BASE ?? "";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...init,
    });
  } catch (cause) {
    throw new ApiError(
      "Backend unavailable. Is the FastAPI server running on port 8000?",
      0,
    );
  }

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const body = await response.json();
      if (body?.message) message = body.message;
      else if (body?.detail) message = JSON.stringify(body.detail);
    } catch {
      // Non-JSON error body; keep the default message.
    }
    throw new ApiError(message, response.status);
  }

  return (await response.json()) as T;
}

export const api = {
  health: () => request<{ status: string }>("/api/health"),

  getCatalog: () => request<Catalog>("/api/catalog"),

  resolveConfiguration: (payload: ConfigurationRequest) =>
    request<RenderState>("/api/configurations/resolve", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  saveConfiguration: (payload: ConfigurationRequest) =>
    request<ConfigurationSummary>("/api/configurations", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  listConfigurations: () =>
    request<ConfigurationSummary[]>("/api/configurations"),

  getConfiguration: (id: number) =>
    request<ConfigurationDetail>(`/api/configurations/${id}`),
};
