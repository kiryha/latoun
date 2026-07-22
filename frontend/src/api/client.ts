// Thin API client for the FastAPI backend. All product knowledge lives on the
// backend; this module only transports semantic codes and resolved state.

import type {
  BulkAssignmentsRequest,
  Catalog,
  ConfigurationDetail,
  ConfigurationRequest,
  ConfigurationSummary,
  FinishScheme,
  FinishSchemeCreate,
  FinishSchemeUpdate,
  MaterialAdmin,
  MaterialAssignment,
  MaterialAssignmentCreate,
  MaterialAssignmentUpdate,
  MaterialCreate,
  MaterialUpdate,
  RenderState,
  ResolvedAssignments,
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

  deleteConfiguration: (id: number) =>
    request<ConfigurationSummary>(`/api/configurations/${id}`, {
      method: "DELETE",
    }),

  listMaterials: () => request<MaterialAdmin[]>("/api/materials"),

  createMaterial: (payload: MaterialCreate) =>
    request<MaterialAdmin>("/api/materials", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  updateMaterial: (code: string, payload: MaterialUpdate) =>
    request<MaterialAdmin>(`/api/materials/${code}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  deleteMaterial: (code: string) =>
    request<MaterialAdmin>(`/api/materials/${code}`, {
      method: "DELETE",
    }),

  // Finish schemes ---------------------------------------------------------- //
  listFinishSchemes: (params?: {
    isActive?: boolean;
    isCustomerVisible?: boolean;
  }) => {
    const query = new URLSearchParams();
    if (params?.isActive !== undefined)
      query.set("is_active", String(params.isActive));
    if (params?.isCustomerVisible !== undefined)
      query.set("is_customer_visible", String(params.isCustomerVisible));
    const suffix = query.toString() ? `?${query.toString()}` : "";
    return request<FinishScheme[]>(`/api/finish-schemes${suffix}`);
  },

  createFinishScheme: (payload: FinishSchemeCreate) =>
    request<FinishScheme>("/api/finish-schemes", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  updateFinishScheme: (id: number, payload: FinishSchemeUpdate) =>
    request<FinishScheme>(`/api/finish-schemes/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),

  deleteFinishScheme: (id: number) =>
    request<FinishScheme>(`/api/finish-schemes/${id}`, {
      method: "DELETE",
    }),

  resolvedAssignments: (code: string) =>
    request<ResolvedAssignments>(
      `/api/finish-schemes/${code}/resolved-assignments`,
    ),

  // Material assignments ---------------------------------------------------- //
  listAssignments: (finishSchemeId: number) =>
    request<MaterialAssignment[]>(
      `/api/finish-schemes/${finishSchemeId}/assignments`,
    ),

  createAssignment: (finishSchemeId: number, payload: MaterialAssignmentCreate) =>
    request<MaterialAssignment>(
      `/api/finish-schemes/${finishSchemeId}/assignments`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    ),

  bulkSaveAssignments: (
    finishSchemeId: number,
    payload: BulkAssignmentsRequest,
  ) =>
    request<MaterialAssignment[]>(
      `/api/finish-schemes/${finishSchemeId}/assignments`,
      {
        method: "PUT",
        body: JSON.stringify(payload),
      },
    ),

  updateAssignment: (id: number, payload: MaterialAssignmentUpdate) =>
    request<MaterialAssignment>(`/api/material-assignments/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),

  deleteAssignment: (id: number) =>
    request<MaterialAssignment>(`/api/material-assignments/${id}`, {
      method: "DELETE",
    }),
};
