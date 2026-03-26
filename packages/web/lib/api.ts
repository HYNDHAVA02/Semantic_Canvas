const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function fetchApi<T = any>(endpoint: string, options?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
    });
  } catch {
    throw new Error("Network error — is the API server running?");
  }

  if (!response.ok) {
    if (response.status === 404) throw new Error("Not found — this resource may have been deleted.");
    if (response.status >= 500) throw new Error("Server error — please try again later.");
    const body = await response.text().catch(() => "");
    throw new Error(body || `Request failed (${response.status})`);
  }

  return response.json();
}

export const api = {
  getProjects: (limit = 50, offset = 0) => fetchApi(`/projects?limit=${limit}&offset=${offset}`),
  createProject: (data: { name: string; slug: string; description?: string; repo_url?: string; default_branch?: string }) =>
    fetchApi(`/projects`, { method: "POST", body: JSON.stringify(data) }),
  getProject: (id: string) => fetchApi(`/projects/${id}`),
  updateProject: (id: string, data: any) => fetchApi(`/projects/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  getProjectEntities: (id: string, limit = 100) => fetchApi(`/projects/${id}/entities?limit=${limit}`),
  getProjectEntity: (projectId: string, entityId: string) => fetchApi(`/projects/${projectId}/entities/${entityId}`),
  getProjectActivity: (id: string, limit = 10, offset = 0) => fetchApi(`/projects/${id}/activity?limit=${limit}&offset=${offset}`),
  getProjectDecisions: (id: string, limit = 100) => fetchApi(`/projects/${id}/decisions?limit=${limit}`),
  createDecision: (projectId: string, data: any) => fetchApi(`/projects/${projectId}/decisions`, { method: "POST", body: JSON.stringify(data) }),
  getProjectConventions: (projectId: string) => fetchApi(`/projects/${projectId}/conventions`),
  createConvention: (projectId: string, data: any) => fetchApi(`/projects/${projectId}/conventions`, { method: "POST", body: JSON.stringify(data) }),
  updateConvention: (projectId: string, conventionId: string, data: any) => fetchApi(`/projects/${projectId}/conventions/${conventionId}`, { method: "PATCH", body: JSON.stringify(data) }),
  searchProject: (id: string, query: string) => fetchApi(`/projects/${id}/search?q=${encodeURIComponent(query)}`),
  getRelationships: (projectId: string, entityId: string) => fetchApi(`/projects/${projectId}/relationships?entity_id=${encodeURIComponent(entityId)}`),
  getProjectRelationships: (projectId: string, limit = 200) => fetchApi(`/projects/${projectId}/relationships?limit=${limit}`),
  createRelationship: (projectId: string, data: any) => fetchApi(`/projects/${projectId}/relationships`, { method: "POST", body: JSON.stringify(data) }),
  getBlastRadius: (projectId: string, entityId: string, depth = 3) => fetchApi(`/projects/${projectId}/blast-radius/${encodeURIComponent(entityId)}?direction=both&depth=${depth}`),
  getMcpConfig: (projectId: string) => fetchApi(`/projects/${projectId}/mcp-config`),
  getTokens: (projectId: string) => fetchApi(`/projects/${projectId}/tokens`),
  createToken: (projectId: string, label: string) => fetchApi(`/projects/${projectId}/tokens`, { method: "POST", body: JSON.stringify({ label }) }),
  revokeToken: (projectId: string, tokenId: string) => fetchApi(`/projects/${projectId}/tokens/${tokenId}`, { method: "DELETE" })
};
