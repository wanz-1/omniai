import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000,
});

apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("access_token");
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const refreshToken = localStorage.getItem("refresh_token");
        if (refreshToken) {
          const response = await axios.post(
            `${apiClient.defaults.baseURL}/auth/refresh`,
            { refresh_token: refreshToken }
          );
          const { access_token, refresh_token: newRefresh } = response.data;
          localStorage.setItem("access_token", access_token);
          localStorage.setItem("refresh_token", newRefresh);
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${access_token}`;
          }
          return apiClient(originalRequest);
        }
      } catch {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(error);
  }
);

export { apiClient };
export default apiClient;

export const authApi = {
  register: (data: { email: string; password: string; display_name: string }) =>
    apiClient.post("/auth/register", data),
  login: (data: { email: string; password: string }) =>
    apiClient.post("/auth/login", data),
  me: () => apiClient.get("/users/me"),
};

export const documentsApi = {
  list: (projectId?: string) =>
    apiClient.get("/documents", { params: { project_id: projectId } }),
  create: (data: any) => apiClient.post("/documents", data),
  get: (id: string) => apiClient.get(`/documents/${id}`),
  update: (id: string, data: any) => apiClient.put(`/documents/${id}`, data),
  delete: (id: string) => apiClient.delete(`/documents/${id}`),
  humanize: (id: string, data: any) => apiClient.post(`/documents/${id}/humanize`, data),
  humanizeStream: (id: string) => `${apiClient.defaults.baseURL}/documents/${id}/humanize/stream`,
  analyze: (id: string) => apiClient.post(`/documents/${id}/analyze`),
  summarize: (id: string, data: any) => apiClient.post(`/documents/${id}/summarize`, data),
  translate: (id: string, data: any) => apiClient.post(`/documents/${id}/translate`, data),
  grammar: (id: string) => apiClient.post(`/documents/${id}/grammar`),
  versions: {
    list: (id: string) => apiClient.get(`/documents/${id}/versions`),
    save: (id: string, data: any) => apiClient.post(`/documents/${id}/versions/save`, data),
    restore: (id: string, versionId: string) =>
      apiClient.post(`/documents/${id}/versions/${versionId}/restore`),
  },
  export: (id: string, data: any) => apiClient.post(`/documents/${id}/export`, data, { responseType: "blob" }),
};

export const websitesApi = {
  list: (projectId?: string) =>
    apiClient.get("/websites", { params: { project_id: projectId } }),
  create: (data: any) => apiClient.post("/websites", data),
  get: (id: string) => apiClient.get(`/websites/${id}`),
  update: (id: string, data: any) => apiClient.put(`/websites/${id}`, data),
  delete: (id: string) => apiClient.delete(`/websites/${id}`),
  customize: (id: string, data: any) => apiClient.post(`/websites/${id}/customize`, data),
  generate: (id: string, data: any) => apiClient.post(`/websites/${id}/generate`, data),
  preview: (id: string) => apiClient.post(`/websites/${id}/preview`),
  publish: (id: string, data: any) => apiClient.post(`/websites/${id}/publish`, data),
  deploy: (id: string, data: any) => apiClient.post(`/websites/${id}/deploy`, data),
  templates: () => apiClient.get("/websites/templates/list"),
  branding: (data: any) => apiClient.post("/websites/branding", data),
  export: (id: string) => apiClient.post(`/websites/${id}/export`, {}, { responseType: "blob" }),
};

export const botsApi = {
  list: (projectId?: string) =>
    apiClient.get("/bots", { params: { project_id: projectId } }),
  create: (data: any) => apiClient.post("/bots", data),
  get: (id: string) => apiClient.get(`/bots/${id}`),
  update: (id: string, data: any) => apiClient.put(`/bots/${id}`, data),
  delete: (id: string) => apiClient.delete(`/bots/${id}`),
  test: (id: string, data: any) => apiClient.post(`/bots/${id}/test`, data),
  deploy: (id: string, data: any) => apiClient.post(`/bots/${id}/deploy`, data),
  train: (id: string, data: any) => apiClient.post(`/bots/${id}/train`, data),
  analytics: (id: string) => apiClient.get(`/bots/${id}/analytics`),
  conversations: (id: string) => apiClient.get(`/bots/${id}/conversations`),
  getConversationMessages: (botId: string, convId: string) =>
    apiClient.get(`/bots/${botId}/conversations/${convId}/messages`),
  embed: (id: string, data: any) => apiClient.post(`/bots/${id}/embed`, data),
  testStreamUrl: (id: string) =>
    `${apiClient.defaults.baseURL}/bots/${id}/test/stream`,
};

export const chatApi = {
  sessions: () => apiClient.get("/chat/sessions"),
  createSession: (data: any) => apiClient.post("/chat/sessions", data),
  getSession: (id: string) => apiClient.get(`/chat/sessions/${id}`),
  deleteSession: (id: string) => apiClient.delete(`/chat/sessions/${id}`),
  messages: (sessionId: string) =>
    apiClient.get(`/chat/sessions/${sessionId}/messages`),
  sendMessage: (sessionId: string, data: any) =>
    apiClient.post(`/chat/sessions/${sessionId}/messages`, data),
  sendMessageStreamUrl: (sessionId: string) =>
    `${apiClient.defaults.baseURL}/chat/sessions/${sessionId}/messages/stream`,
};

export const codeApi = {
  projects: (projectId?: string) =>
    apiClient.get("/code/projects", { params: { project_id: projectId } }),
  createProject: (data: any) => apiClient.post("/code/projects", data),
  getProject: (id: string) => apiClient.get(`/code/projects/${id}`),
  updateProject: (id: string, data: any) => apiClient.put(`/code/projects/${id}`, data),
  deleteProject: (id: string) => apiClient.delete(`/code/projects/${id}`),
  generate: (data: any) => apiClient.post("/code/generate", data),
  generateForProject: (id: string, data: any) =>
    apiClient.post(`/code/projects/${id}/generate`, data),
  explain: (data: any) => apiClient.post("/code/explain", data),
  review: (data: any) => apiClient.post("/code/review", data),
};

export const projectsApi = {
  list: (type?: string) =>
    apiClient.get("/projects", { params: { type } }),
  create: (data: any) => apiClient.post("/projects", data),
  get: (id: string) => apiClient.get(`/projects/${id}`),
  update: (id: string, data: any) => apiClient.put(`/projects/${id}`, data),
  delete: (id: string) => apiClient.delete(`/projects/${id}`),
};

export const notificationsApi = {
  list: (unreadOnly?: boolean) =>
    apiClient.get("/notifications", { params: { unread_only: unreadOnly } }),
  unreadCount: () => apiClient.get("/notifications/unread-count"),
  markRead: (id: string) => apiClient.put(`/notifications/${id}/read`),
  markAllRead: () => apiClient.put("/notifications/read-all"),
};

export const agentsApi = {
  list: () => apiClient.get("/agents"),
  create: (data: any) => apiClient.post("/agents", data),
  get: (id: string) => apiClient.get(`/agents/${id}`),
  update: (id: string, data: any) => apiClient.put(`/agents/${id}`, data),
  delete: (id: string) => apiClient.delete(`/agents/${id}`),
  templates: (category?: string) =>
    apiClient.get("/agents/templates", { params: { category } }),
  marketplace: (category?: string) =>
    apiClient.get("/agents/marketplace", { params: { category } }),
  clone: (id: string) => apiClient.post(`/agents/${id}/clone`),
  publish: (id: string, data?: any) =>
    apiClient.post(`/agents/${id}/publish`, data),
  chat: (id: string, data: any) =>
    apiClient.post(`/agents/${id}/chat`, data),
  chatStreamUrl: (id: string) =>
    `${apiClient.defaults.baseURL}/agents/${id}/chat/stream`,
  tasks: {
    list: (agentId: string, status?: string) =>
      apiClient.get(`/agents/${agentId}/tasks`, { params: { status } }),
    create: (agentId: string, data: any) =>
      apiClient.post(`/agents/${agentId}/tasks`, data),
    execute: (agentId: string, taskId: string) =>
      apiClient.post(`/agents/${agentId}/tasks/${taskId}/execute`),
  },
  executions: (agentId: string) =>
    apiClient.get(`/agents/${agentId}/executions`),
  analytics: (agentId: string) =>
    apiClient.get(`/agents/${agentId}/analytics`),
  workflows: {
    list: (agentId: string) =>
      apiClient.get(`/agents/${agentId}/workflows`),
    create: (agentId: string, data: any) =>
      apiClient.post(`/agents/${agentId}/workflows`, data),
    update: (agentId: string, workflowId: string, data: any) =>
      apiClient.put(`/agents/${agentId}/workflows/${workflowId}`, data),
    delete: (agentId: string, workflowId: string) =>
      apiClient.delete(`/agents/${agentId}/workflows/${workflowId}`),
  },
  skills: {
    list: (agentId: string) => apiClient.get(`/agents/${agentId}/skills`),
    add: (agentId: string, data: any) =>
      apiClient.post(`/agents/${agentId}/skills`, data),
    delete: (agentId: string, skillId: string) =>
      apiClient.delete(`/agents/${agentId}/skills/${skillId}`),
  },
  tools: {
    list: (agentId: string) => apiClient.get(`/agents/${agentId}/tools`),
    add: (agentId: string, data: any) =>
      apiClient.post(`/agents/${agentId}/tools`, data),
    delete: (agentId: string, toolId: string) =>
      apiClient.delete(`/agents/${agentId}/tools/${toolId}`),
  },
  memories: {
    list: (agentId: string, type?: string, category?: string) =>
      apiClient.get(`/agents/${agentId}/memories`, { params: { memory_type: type, category } }),
    add: (agentId: string, data: any) =>
      apiClient.post(`/agents/${agentId}/memories`, data),
    delete: (agentId: string, memoryId: string) =>
      apiClient.delete(`/agents/${agentId}/memories/${memoryId}`),
    clear: (agentId: string) =>
      apiClient.delete(`/agents/${agentId}/memories`),
  },
};

export const billingApi = {
  plans: () => apiClient.get("/billing/plans"),
  subscription: (orgId: string) => apiClient.get(`/billing/subscriptions/${orgId}`),
  checkout: (data: any) => apiClient.post("/billing/checkout", data),
  portal: (data: any) => apiClient.post("/billing/portal", data),
  invoices: (orgId: string) => apiClient.get(`/billing/invoices/${orgId}`),
  cancel: (subId: string) => apiClient.post(`/billing/subscriptions/${subId}/cancel`),
};

export const adminApi = {
  overview: () => apiClient.get("/admin/overview"),
  users: (params?: any) => apiClient.get("/admin/users", { params }),
  suspendUser: (userId: string) => apiClient.put(`/admin/users/${userId}/suspend`),
  restoreUser: (userId: string) => apiClient.put(`/admin/users/${userId}/restore`),
  dailyUsage: (days?: number) => apiClient.get("/admin/usage/daily", { params: { days } }),
  marketplaceItems: (params?: any) => apiClient.get("/admin/marketplace/items", { params }),
  approveItem: (itemId: string) => apiClient.put(`/admin/marketplace/items/${itemId}/approve`),
  rejectItem: (itemId: string) => apiClient.put(`/admin/marketplace/items/${itemId}/reject`),
  auditLogs: (params?: any) => apiClient.get("/admin/audit-logs", { params }),
  settings: () => apiClient.get("/admin/settings"),
  updateSettings: (data: any) => apiClient.put("/admin/settings", data),
};

export const marketplaceApi = {
  items: (params?: any) => apiClient.get("/marketplace/items", { params }),
  getItem: (id: string) => apiClient.get(`/marketplace/items/${id}`),
  createItem: (data: any) => apiClient.post("/marketplace/items", data),
  updateItem: (id: string, data: any) => apiClient.put(`/marketplace/items/${id}`, data),
  purchase: (id: string) => apiClient.post(`/marketplace/items/${id}/purchase`),
  myItems: () => apiClient.get("/marketplace/my-items"),
  myPurchases: () => apiClient.get("/marketplace/my-purchases"),
  categories: () => apiClient.get("/marketplace/categories"),
};

export const marketplaceExtendedApi = {
  dashboard: () => apiClient.get("/marketplace-extended/dashboard"),
  categories: () => apiClient.get("/marketplace-extended/categories"),
  createCategory: (data: any) => apiClient.post("/marketplace-extended/categories", null, { params: data }),
  products: (params?: any) => apiClient.get("/marketplace-extended/products", { params }),
  getProduct: (id: string) => apiClient.get(`/marketplace-extended/products/${id}`),
  publishProduct: (data: any) => apiClient.post("/marketplace-extended/products", data),
  purchaseProduct: (productId: string, orgId?: string) => apiClient.post(`/marketplace-extended/products/${productId}/purchase`, null, { params: orgId ? { organization_id: orgId } : {} }),
  createReview: (data: any) => apiClient.post("/marketplace-extended/reviews", data),
  getReviews: (productId: string) => apiClient.get(`/marketplace-extended/reviews/${productId}`),
  getCreatorProfile: () => apiClient.get("/marketplace-extended/creator/profile"),
  updateCreatorProfile: (data: any) => apiClient.put("/marketplace-extended/creator/profile", data),
  getCreatorDashboard: () => apiClient.get("/marketplace-extended/creator/dashboard"),
  getProductAnalytics: (productId: string) => apiClient.get(`/marketplace-extended/creator/analytics/${productId}`),
  myProducts: () => apiClient.get("/marketplace-extended/my-products"),
  registerPlugin: (data: any) => apiClient.post("/marketplace-extended/plugins", null, { params: data }),
  listPlugins: (pluginType?: string) => apiClient.get("/marketplace-extended/plugins", { params: pluginType ? { plugin_type: pluginType } : {} }),
  installPlugin: (pluginId: string, orgId?: string) => apiClient.post(`/marketplace-extended/plugins/${pluginId}/install`, null, { params: orgId ? { organization_id: orgId } : {} }),
  uninstallPlugin: (installationId: string) => apiClient.delete(`/marketplace-extended/plugins/install/${installationId}`),
  getInstalledPlugins: (orgId?: string) => apiClient.get("/marketplace-extended/plugins/installed", { params: orgId ? { organization_id: orgId } : {} }),
  verifyProduct: (productId: string, level?: string) => apiClient.post(`/marketplace-extended/verify/${productId}`, null, { params: { level: level || "community" } }),
  getVerificationHistory: (productId: string) => apiClient.get(`/marketplace-extended/verify/${productId}/history`),
  createEnterpriseListing: (data: any) => apiClient.post("/marketplace-extended/enterprise", data),
  getEnterpriseListing: (productId: string, orgId: string) => apiClient.get(`/marketplace-extended/enterprise/${productId}`, { params: { organization_id: orgId } }),
  generateSDK: (data: any) => apiClient.post("/marketplace-extended/sdk", data),
  getSDKTemplate: (language?: string) => apiClient.get(`/marketplace-extended/sdk/${language || "python"}`),
  getProductVersions: (productId: string) => apiClient.get(`/marketplace-extended/products/${productId}/versions`),
  createProductVersion: (productId: string, version: string, changelog?: string) => apiClient.post(`/marketplace-extended/products/${productId}/versions`, null, { params: { version, changelog } }),
};

export const analyticsApi = {
  usage: (days?: number) => apiClient.get("/analytics/usage", { params: { days } }),
  agents: () => apiClient.get("/analytics/agents"),
  revenue: () => apiClient.get("/analytics/revenue"),
  growth: () => apiClient.get("/analytics/growth"),
};

export const voiceApi = {
  sessions: () => apiClient.get("/voice/sessions"),
  createSession: (data: any) => apiClient.post("/voice/sessions", data),
  getSession: (id: string) => apiClient.get(`/voice/sessions/${id}`),
  endSession: (id: string) => apiClient.post(`/voice/sessions/${id}/end`),
  messages: (id: string) => apiClient.get(`/voice/sessions/${id}/messages`),
  transcribe: (file: File, language?: string) => {
    const fd = new FormData();
    fd.append("file", file);
    if (language) fd.append("language", language);
    return apiClient.post("/voice/transcribe", fd);
  },
  synthesize: (text: string, voice?: string, language?: string) => {
    const fd = new FormData();
    fd.append("text", text);
    if (voice) fd.append("voice", voice);
    if (language) fd.append("language", language);
    return apiClient.post("/voice/synthesize", fd, { responseType: "blob" });
  },
  processMessage: (sessionId: string, file: File, language?: string) => {
    const fd = new FormData();
    fd.append("file", file);
    if (language) fd.append("language", language);
    return apiClient.post(`/voice/sessions/${sessionId}/process`, fd);
  },
  providers: () => apiClient.get("/voice/providers"),
};

export const visionApi = {
  analyze: (file: File, prompt?: string) => {
    const fd = new FormData();
    fd.append("file", file);
    if (prompt) fd.append("prompt", prompt);
    return apiClient.post("/vision/analyze", fd);
  },
  ocr: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return apiClient.post("/vision/ocr", fd);
  },
  scan: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return apiClient.post("/vision/scan", fd);
  },
  assets: (type?: string) => apiClient.get("/vision/assets", { params: { asset_type: type } }),
  getAsset: (id: string) => apiClient.get(`/vision/assets/${id}`),
  deleteAsset: (id: string) => apiClient.delete(`/vision/assets/${id}`),
};

export const videoApi = {
  process: (file: File, jobType?: string) => {
    const fd = new FormData();
    fd.append("file", file);
    if (jobType) fd.append("job_type", jobType);
    return apiClient.post("/video/process", fd);
  },
  jobs: () => apiClient.get("/video/jobs"),
  getJob: (id: string) => apiClient.get(`/video/jobs/${id}`),
};

export const codeStudioApi = {
  projects: (orgId?: string) => apiClient.get("/code-studio/projects", { params: orgId ? { organization_id: orgId } : {} }),
  getProject: (id: string) => apiClient.get(`/code-studio/projects/${id}`),
  createProject: (data: any) => apiClient.post("/code-studio/projects", data),
  deleteProject: (id: string) => apiClient.delete(`/code-studio/projects/${id}`),
  files: (projectId: string) => apiClient.get(`/code-studio/projects/${projectId}/files`),
  getFile: (fileId: string) => apiClient.get(`/code-studio/files/${fileId}`),
  updateFile: (fileId: string, content: string) => apiClient.put(`/code-studio/files/${fileId}`, null, { params: { content } }),
  generateApp: (data: any) => apiClient.post("/code-studio/generate", data),
  generateCode: (data: any) => apiClient.post("/code-studio/generate-code", data),
  debug: (data: any) => apiClient.post("/code-studio/debug", data),
  reviewCode: (code: string, language?: string) => apiClient.post("/code-studio/review-code", null, { params: { code, language: language || "python" } }),
  connectRepo: (data: any) => apiClient.post("/code-studio/repositories", data),
  repositories: () => apiClient.get("/code-studio/repositories"),
  analyzeRepo: (repoId: string) => apiClient.post(`/code-studio/repositories/${repoId}/analyze`),
  commitMessage: (diff: string) => apiClient.post("/code-studio/commit-message", null, { params: { diff } }),
  buildProject: (projectId: string) => apiClient.post(`/code-studio/projects/${projectId}/build`),
  builds: (projectId: string) => apiClient.get(`/code-studio/projects/${projectId}/builds`),
  deployProject: (projectId: string, data: any) => apiClient.post(`/code-studio/projects/${projectId}/deploy`, data),
  deployments: (projectId: string) => apiClient.get(`/code-studio/projects/${projectId}/deployments`),
  generateCICD: (projectId: string, platform?: string) => apiClient.post(`/code-studio/projects/${projectId}/ci-cd`, null, { params: { platform: platform || "github" } }),
  generateTests: (projectId: string, data: any) => apiClient.post(`/code-studio/projects/${projectId}/tests`, data),
  testRuns: (projectId: string) => apiClient.get(`/code-studio/projects/${projectId}/tests`),
  securityScan: (projectId: string, data?: any) => apiClient.post(`/code-studio/projects/${projectId}/security-scan`, data || { scan_type: "full" }),
  securityScans: (projectId: string) => apiClient.get(`/code-studio/projects/${projectId}/security-scans`),
  securitySummary: (projectId: string) => apiClient.get(`/code-studio/projects/${projectId}/security-summary`),
  generateDoc: (projectId: string, docType?: string) => apiClient.post(`/code-studio/projects/${projectId}/docs`, null, { params: { doc_type: docType || "readme" } }),
  generateAllDocs: (projectId: string) => apiClient.post(`/code-studio/projects/${projectId}/docs/all`),
  docs: (projectId: string) => apiClient.get(`/code-studio/projects/${projectId}/docs`),
  dashboard: (orgId: string) => apiClient.get(`/code-studio/dashboard/${orgId}`),
};

export const agentNetworkApi = {
  orchestrate: (data: any) => apiClient.post("/agent-network/orchestrate", data),
  autoCreateTeam: (data: any) => apiClient.post("/agent-network/teams/auto-create", data),
  teams: (orgId?: string) => apiClient.get("/agent-network/teams", { params: orgId ? { organization_id: orgId } : {} }),
  getTeam: (id: string) => apiClient.get(`/agent-network/teams/${id}`),
  createTeam: (data: any) => apiClient.post("/agent-network/teams", data),
  addTeamMember: (teamId: string, data: any) => apiClient.post(`/agent-network/teams/${teamId}/members`, data),
  removeTeamMember: (teamId: string, memberId: string) => apiClient.delete(`/agent-network/teams/${teamId}/members/${memberId}`),
  deleteTeam: (id: string) => apiClient.delete(`/agent-network/teams/${id}`),
  sendMessage: (receiverId: string, content: string, opts?: any) => apiClient.post("/agent-network/messages", null, { params: { receiver_id: receiverId, content, ...opts } }),
  conversation: (a1: string, a2: string) => apiClient.get(`/agent-network/messages/${a1}/${a2}`),
  teamMessages: (teamId: string) => apiClient.get(`/agent-network/messages/team/${teamId}`),
  createDelegation: (data: any) => apiClient.post("/agent-network/delegations", data),
  delegations: (teamId?: string, status?: string) => apiClient.get("/agent-network/delegations", { params: { team_id: teamId, status } }),
  completeDelegation: (id: string, data?: any) => apiClient.post(`/agent-network/delegations/${id}/complete`, data),
  storeMemory: (data: any) => apiClient.post("/agent-network/memory", data),
  searchMemory: (query: string, teamId?: string, orgId?: string) => apiClient.get("/agent-network/memory/search", { params: { query_text: query, team_id: teamId, organization_id: orgId } }),
  getTeamMemory: (teamId: string) => apiClient.get(`/agent-network/memory/team/${teamId}`),
  deleteMemory: (id: string) => apiClient.delete(`/agent-network/memory/${id}`),
  createReview: (data: any) => apiClient.post("/agent-network/reviews", data),
  getReviews: (agentId: string) => apiClient.get(`/agent-network/reviews/${agentId}`),
  performance: (agentId: string) => apiClient.get(`/agent-network/performance/${agentId}`),
  grantPermission: (data: any) => apiClient.post("/agent-network/permissions", data),
  getPermissions: (agentId: string) => apiClient.get(`/agent-network/permissions/agent/${agentId}`),
  revokePermission: (id: string) => apiClient.delete(`/agent-network/permissions/${id}`),
  checkPermission: (agentId: string, resource: string, action: string) => apiClient.get(`/agent-network/permissions/check/${agentId}/${resource}/${action}`),
  conductResearch: (data: any) => apiClient.post("/agent-network/research", data),
  listResearch: () => apiClient.get("/agent-network/research"),
  getResearch: (id: string) => apiClient.get(`/agent-network/research/${id}`),
  createDevProject: (data: any) => apiClient.post("/agent-network/dev-projects", data),
  listDevProjects: (orgId?: string) => apiClient.get("/agent-network/dev-projects", { params: orgId ? { organization_id: orgId } : {} }),
  getDevProject: (id: string) => apiClient.get(`/agent-network/dev-projects/${id}`),
  generateCode: (projectId: string) => apiClient.post(`/agent-network/dev-projects/${projectId}/generate-code`),
  securityReview: (projectId: string) => apiClient.post(`/agent-network/dev-projects/${projectId}/security-review`),
  runTests: (projectId: string) => apiClient.post(`/agent-network/dev-projects/${projectId}/run-tests`),
  completeDevProject: (projectId: string) => apiClient.post(`/agent-network/dev-projects/${projectId}/complete`),
  dashboard: (orgId: string) => apiClient.get(`/agent-network/dashboard/${orgId}`),
};

export const infrastructureApi = {
  dashboard: () => apiClient.get("/infrastructure/dashboard"),
  regions: () => apiClient.get("/infrastructure/regions"),
  createRegion: (data: any) => apiClient.post("/infrastructure/regions", null, { params: data }),
  getRegion: (id: string) => apiClient.get(`/infrastructure/regions/${id}`),
  clusters: (regionId?: string) => apiClient.get("/infrastructure/clusters", { params: regionId ? { region_id: regionId } : {} }),
  createCluster: (data: any) => apiClient.post("/infrastructure/clusters", null, { params: data }),
  updateClusterHealth: (clusterId: string, status: string) => apiClient.post(`/infrastructure/clusters/${clusterId}/health`, null, { params: { status } }),
  services: (clusterId?: string) => apiClient.get("/infrastructure/services", { params: clusterId ? { cluster_id: clusterId } : {} }),
  deployService: (data: any) => apiClient.post("/infrastructure/services", null, { params: data }),
  scaleService: (serviceId: string, targetReplicas: number) => apiClient.post(`/infrastructure/services/${serviceId}/scale`, null, { params: { target_replicas: targetReplicas } }),
  models: (modelType?: string, provider?: string) => apiClient.get("/infrastructure/models", { params: { model_type: modelType, provider } }),
  registerModel: (data: any) => apiClient.post("/infrastructure/models", null, { params: data }),
  routeModel: (data: any) => apiClient.post("/infrastructure/models/route", data),
  securityEvents: (params?: any) => apiClient.get("/infrastructure/security/events", { params }),
  logSecurityEvent: (data: any) => apiClient.post("/infrastructure/security/events", null, { params: data }),
  resolveSecurityEvent: (eventId: string, action?: string) => apiClient.post(`/infrastructure/security/events/${eventId}/resolve`, null, { params: { action_taken: action } }),
  securitySummary: () => apiClient.get("/infrastructure/security/summary"),
  metrics: (params?: any) => apiClient.get("/infrastructure/monitoring/metrics", { params }),
  recordMetric: (data: any) => apiClient.post("/infrastructure/monitoring/metrics", null, { params: data }),
  systemHealth: () => apiClient.get("/infrastructure/monitoring/health"),
  apiUptime: (days?: number) => apiClient.get("/infrastructure/monitoring/uptime", { params: { days } }),
  backups: (params?: any) => apiClient.get("/infrastructure/backups", { params }),
  createBackup: (data: any) => apiClient.post("/infrastructure/backups", null, { params: data }),
  getBackup: (id: string) => apiClient.get(`/infrastructure/backups/${id}`),
  completeBackup: (backupId: string, sizeBytes: number, location: string) => apiClient.post(`/infrastructure/backups/${backupId}/complete`, null, { params: { size_bytes: sizeBytes, location } }),
  backupSummary: () => apiClient.get("/infrastructure/backups/summary"),
  policies: (orgId: string, policyType?: string) => apiClient.get(`/infrastructure/policies/${orgId}`, { params: policyType ? { policy_type: policyType } : {} }),
  createPolicy: (orgId: string, data: any) => apiClient.post(`/infrastructure/policies/${orgId}`, null, { params: data }),
  complianceReports: (params?: any) => apiClient.get("/infrastructure/compliance/reports", { params }),
  createComplianceReport: (data: any) => apiClient.post("/infrastructure/compliance/reports", null, { params: data }),
  generateComplianceReport: (reportId: string) => apiClient.post(`/infrastructure/compliance/reports/${reportId}/generate`),
  dataResidency: (orgId: string) => apiClient.get(`/infrastructure/data-residency/${orgId}`),
  configureDataResidency: (orgId: string, data: any) => apiClient.post(`/infrastructure/data-residency/${orgId}`, null, { params: data }),
  apiKeys: (orgId: string) => apiClient.get(`/infrastructure/api-keys/${orgId}`),
  createApiKey: (orgId: string, data: any) => apiClient.post(`/infrastructure/api-keys/${orgId}`, data),
  deleteApiKey: (keyId: string) => apiClient.delete(`/infrastructure/api-keys/${keyId}`),
  seed: () => apiClient.post("/infrastructure/seed"),
};

export const v3PersonalApi = {
  assistants: () => apiClient.get("/v3/personal/assistants"),
  createAssistant: (data: any) => apiClient.post("/v3/personal/assistants", null, { params: data }),
  queryAssistant: (data: any) => apiClient.post("/v3/personal/assistants/query", data),
  memories: (assistantId: string) => apiClient.get(`/v3/personal/assistants/${assistantId}/memories`),
  storeMemory: (assistantId: string, data: any) => apiClient.post(`/v3/personal/assistants/${assistantId}/memories`, null, { params: data }),
  tasks: (status?: string) => apiClient.get("/v3/personal/tasks", { params: status ? { status } : {} }),
  createTask: (data: any) => apiClient.post("/v3/personal/tasks", null, { params: data }),
  completeTask: (taskId: string, result?: string) => apiClient.post(`/v3/personal/tasks/${taskId}/complete`, null, { params: { result } }),
  executives: () => apiClient.get("/v3/personal/executives"),
  createExecutive: (data: any) => apiClient.post("/v3/personal/executives", null, { params: data }),
  queryExecutive: (execId: string, query: string) => apiClient.post(`/v3/personal/executives/${execId}/query`, null, { params: { query } }),
};

export const v3OrganizationApi = {
  getOS: (orgId: string) => apiClient.get(`/v3/organization/os/${orgId}`),
  createOS: (orgId: string, data: any) => apiClient.post(`/v3/organization/os/${orgId}`, null, { params: data }),
  departments: (orgId: string) => apiClient.get(`/v3/organization/os/${orgId}/departments`),
  createDepartment: (orgId: string, data: any) => apiClient.post(`/v3/organization/os/${orgId}/departments`, null, { params: data }),
  departmentAgents: (deptId: string) => apiClient.get(`/v3/organization/departments/${deptId}/agents`),
  workflows: (orgId: string) => apiClient.get(`/v3/organization/os/${orgId}/workflows`),
  createWorkflow: (orgId: string, data: any) => apiClient.post(`/v3/organization/os/${orgId}/workflows`, null, { params: data }),
  executeWorkflow: (workflowId: string) => apiClient.post(`/v3/organization/workflows/${workflowId}/execute`),
  query: (data: any) => apiClient.post("/v3/organization/query", data),
};

export const v3CreationApi = {
  startups: () => apiClient.get("/v3/creation/startups"),
  createStartup: (data: any) => apiClient.post("/v3/creation/startups", data),
  generateBusinessPlan: (startupId: string) => apiClient.post(`/v3/creation/startups/${startupId}/business-plan`),
  generateProduct: (startupId: string, data: any) => apiClient.post(`/v3/creation/startups/${startupId}/products`, null, { params: data }),
  createIdea: (data: any) => apiClient.post("/v3/creation/ideas", null, { params: data }),
  validateIdea: (ideaId: string) => apiClient.post(`/v3/creation/ideas/${ideaId}/validate`),
  designs: (assetType?: string) => apiClient.get("/v3/creation/designs", { params: assetType ? { asset_type: assetType } : {} }),
  generateDesign: (data: any) => apiClient.post("/v3/creation/designs", data),
};

export const v3CollaborationApi = {
  analyzeMeeting: (data: any) => apiClient.post("/v3/collaboration/meetings/analyze", data),
  meetings: () => apiClient.get("/v3/collaboration/meetings"),
  generateCommunication: (data: any) => apiClient.post("/v3/collaboration/communications", null, { params: data }),
  communications: (commType?: string) => apiClient.get("/v3/collaboration/communications", { params: commType ? { communication_type: commType } : {} }),
  learningPaths: () => apiClient.get("/v3/collaboration/learning"),
  createLearningPath: (data: any) => apiClient.post("/v3/collaboration/learning", null, { params: data }),
  devices: (deviceType?: string) => apiClient.get("/v3/collaboration/devices", { params: deviceType ? { device_type: deviceType } : {} }),
  registerDevice: (data: any) => apiClient.post("/v3/collaboration/devices", null, { params: data }),
  recordTelemetry: (deviceId: string, data: any) => apiClient.post(`/v3/collaboration/devices/${deviceId}/telemetry`, null, { params: data }),
};

export const industryApi = {
  list: () => apiClient.get("/industry"),
  get: (slug: string) => apiClient.get(`/industry/${slug}`),
  query: (data: any) => apiClient.post("/industry/query", data),
  dashboard: (slug: string) => apiClient.get(`/industry/${slug}/dashboard`),
  packages: (slug: string) => apiClient.get(`/industry/${slug}/packages`),
  createPackage: (slug: string, data: any) => apiClient.post(`/industry/${slug}/packages`, null, { params: data }),
  installPackage: (pkgId: string) => apiClient.post(`/industry/packages/${pkgId}/install`),
  uninstallPackage: (pkgId: string) => apiClient.post(`/industry/packages/${pkgId}/uninstall`),
  knowledge: (slug: string, category?: string) => apiClient.get(`/industry/${slug}/knowledge`, { params: category ? { category } : {} }),
  addKnowledge: (slug: string, data: any) => apiClient.post(`/industry/${slug}/knowledge`, data),
  deleteKnowledge: (id: string) => apiClient.delete(`/industry/knowledge/${id}`),
  agents: (slug: string, agentType?: string) => apiClient.get(`/industry/${slug}/agents`, { params: agentType ? { agent_type: agentType } : {} }),
  createAgent: (slug: string, data: any) => apiClient.post(`/industry/${slug}/agents`, data),
  chatWithAgent: (slug: string, agentSlug: string, query: string) => apiClient.post(`/industry/${slug}/agents/${agentSlug}/chat`, null, { params: { query } }),
  workflows: (slug: string, workflowType?: string) => apiClient.get(`/industry/${slug}/workflows`, { params: workflowType ? { workflow_type: workflowType } : {} }),
  createWorkflow: (slug: string, data: any) => apiClient.post(`/industry/${slug}/workflows`, data),
  templates: (slug: string, templateType?: string) => apiClient.get(`/industry/${slug}/templates`, { params: templateType ? { template_type: templateType } : {} }),
  createTemplate: (slug: string, data: any) => apiClient.post(`/industry/${slug}/templates`, data),
  generateFromTemplate: (slug: string, templateType: string, params: any) => apiClient.post(`/industry/${slug}/templates/generate`, null, { params: { template_type: templateType }, data: params }),
  compliance: (slug: string, ruleType?: string) => apiClient.get(`/industry/${slug}/compliance`, { params: ruleType ? { rule_type: ruleType } : {} }),
  createComplianceRule: (slug: string, data: any) => apiClient.post(`/industry/${slug}/compliance`, data),
  checkCompliance: (slug: string, data: any) => apiClient.post(`/industry/${slug}/compliance/check`, data),
  analytics: (slug: string, period?: string) => apiClient.get(`/industry/${slug}/analytics`, { params: { period: period || "monthly" } }),
  seed: () => apiClient.post("/industry/seed"),
};

export const v4CloudApi = {
  createEnvironment: (data: any) => apiClient.post("/v4/cloud/environments", null, { params: data }),
  listEnvironments: (orgId: string) => apiClient.get("/v4/cloud/environments", { params: { organization_id: orgId } }),
  getEnvironment: (envId: string) => apiClient.get(`/v4/cloud/environments/${envId}`),
  updateEnvironment: (envId: string, data: any) => apiClient.patch(`/v4/cloud/environments/${envId}`, null, { params: data }),
  deleteEnvironment: (envId: string) => apiClient.delete(`/v4/cloud/environments/${envId}`),
  createDeployment: (tenantId: string, data: any) => apiClient.post(`/v4/cloud/environments/${tenantId}/deployments`, null, { params: data }),
  listDeployments: (tenantId: string) => apiClient.get(`/v4/cloud/environments/${tenantId}/deployments`),
  createBackup: (tenantId: string, data?: any) => apiClient.post(`/v4/cloud/environments/${tenantId}/backups`, null, { params: data }),
  listBackups: (tenantId: string) => apiClient.get(`/v4/cloud/environments/${tenantId}/backups`),
  createDrPlan: (tenantId: string, data: any) => apiClient.post(`/v4/cloud/environments/${tenantId}/dr-plans`, null, { params: data }),
  listDrPlans: (tenantId: string) => apiClient.get(`/v4/cloud/environments/${tenantId}/dr-plans`),
  recordMetric: (tenantId: string, data: any) => apiClient.post(`/v4/cloud/environments/${tenantId}/metrics`, null, { params: data }),
  getMetrics: (tenantId: string, metricName?: string) => apiClient.get(`/v4/cloud/environments/${tenantId}/metrics`, { params: metricName ? { metric_name: metricName } : {} }),
  createAppCategory: (data: any) => apiClient.post("/v4/cloud/apps/categories", null, { params: data }),
  listAppCategories: () => apiClient.get("/v4/cloud/apps/categories"),
  createAppListing: (data: any) => apiClient.post("/v4/cloud/apps/listings", null, { params: data }),
  listApps: (categoryId?: string) => apiClient.get("/v4/cloud/apps/listings", { params: categoryId ? { category_id: categoryId } : {} }),
  searchApps: (query: string) => apiClient.get("/v4/cloud/apps/listings/search", { params: { query } }),
  installApp: (data: any) => apiClient.post("/v4/cloud/apps/install", null, { params: data }),
  listInstallations: (orgId: string) => apiClient.get("/v4/cloud/apps/installations", { params: { organization_id: orgId } }),
  purchaseApp: (data: any) => apiClient.post("/v4/cloud/apps/purchase", null, { params: data }),
  createWorkflowTemplate: (data: any) => apiClient.post("/v4/cloud/workflows/templates", null, { params: data }),
  listWorkflowTemplates: (category?: string) => apiClient.get("/v4/cloud/workflows/templates", { params: category ? { category } : {} }),
  installWorkflow: (data: any) => apiClient.post("/v4/cloud/workflows/install", null, { params: data }),
  listWorkflowInstallations: (orgId: string) => apiClient.get("/v4/cloud/workflows/installations", { params: { organization_id: orgId } }),
};

export const v4EnterpriseApi = {
  createConnector: (data: any) => apiClient.post("/v4/enterprise/knowledge/connectors", null, { params: data }),
  listConnectors: (orgId: string) => apiClient.get("/v4/enterprise/knowledge/connectors", { params: { organization_id: orgId } }),
  syncConnector: (connId: string) => apiClient.post(`/v4/enterprise/knowledge/connectors/${connId}/sync`),
  searchKnowledge: (data: any) => apiClient.post("/v4/enterprise/knowledge/search", data),
  createPolicy: (data: any) => apiClient.post("/v4/enterprise/governance/policies", null, { params: data }),
  listPolicies: (orgId: string) => apiClient.get("/v4/enterprise/governance/policies", { params: { organization_id: orgId } }),
  checkPolicy: (data: any) => apiClient.post("/v4/enterprise/governance/check", data),
  createApprovalRequest: (data: any) => apiClient.post("/v4/enterprise/governance/approvals", null, { params: data }),
  reviewApproval: (reqId: string, data: any) => apiClient.patch(`/v4/enterprise/governance/approvals/${reqId}`, null, { params: data }),
  recordMonitoringEvent: (data: any) => apiClient.post("/v4/enterprise/observability/events", null, { params: data }),
  getMonitoringEvents: (orgId: string, eventType?: string) => apiClient.get("/v4/enterprise/observability/events", { params: { organization_id: orgId, event_type: eventType } }),
  createObservabilityDashboard: (data: any) => apiClient.post("/v4/enterprise/observability/dashboards", null, { params: data }),
  listObservabilityDashboards: (orgId: string, dashType?: string) => apiClient.get("/v4/enterprise/observability/dashboards", { params: { organization_id: orgId, dashboard_type: dashType } }),
  recordAnalytics: (data: any) => apiClient.post("/v4/enterprise/analytics/records", null, { params: data }),
  getAnalytics: (orgId: string, category?: string, period?: string) => apiClient.get("/v4/enterprise/analytics/records", { params: { organization_id: orgId, metric_category: category, period } }),
};

export const v4EcosystemApi = {
  createIntegration: (data: any) => apiClient.post("/v4/ecosystem/integrations", null, { params: data }),
  listIntegrations: (orgId: string, intType?: string) => apiClient.get("/v4/ecosystem/integrations", { params: { organization_id: orgId, integration_type: intType } }),
  syncIntegration: (intId: string) => apiClient.post(`/v4/ecosystem/integrations/${intId}/sync`),
  getSyncHistory: (intId: string) => apiClient.get(`/v4/ecosystem/integrations/${intId}/sync-history`),
  createAppDefinition: (data: any) => apiClient.post("/v4/ecosystem/builder/apps", null, { params: data }),
  listAppDefinitions: (orgId: string) => apiClient.get("/v4/ecosystem/builder/apps", { params: { organization_id: orgId } }),
  generateFromPrompt: (appId: string) => apiClient.post(`/v4/ecosystem/builder/apps/${appId}/generate`),
  addComponent: (appId: string, data: any) => apiClient.post(`/v4/ecosystem/builder/apps/${appId}/components`, null, { params: data }),
  publishApp: (appId: string) => apiClient.post(`/v4/ecosystem/builder/apps/${appId}/publish`),
  registerModel: (data: any) => apiClient.post("/v4/ecosystem/models/register", null, { params: data }),
  listRegisteredModels: (orgId: string) => apiClient.get("/v4/ecosystem/models/registered", { params: { organization_id: orgId } }),
  listSdks: (lang?: string) => apiClient.get("/v4/ecosystem/sdks", { params: lang ? { language: lang } : {} }),
  createPlugin: (data: any) => apiClient.post("/v4/ecosystem/plugins", null, { params: data }),
  listPlugins: (pluginType?: string) => apiClient.get("/v4/ecosystem/plugins", { params: pluginType ? { plugin_type: pluginType } : {} }),
};

export const v5SimulationApi = {
  createScenario: (data: any) => apiClient.post("/v5/simulation/scenarios", data),
  listScenarios: (scenarioType?: string) =>
    apiClient.get("/v5/simulation/scenarios", { params: scenarioType ? { scenario_type: scenarioType } : {} }),
  runSimulation: (data: any) => apiClient.post("/v5/simulation/simulations/run", data),
  listSimulations: () => apiClient.get("/v5/simulation/simulations"),
  getSimulationResults: (id: string) => apiClient.get(`/v5/simulation/simulations/${id}/results`),
  compareScenarios: (data: any) => apiClient.post("/v5/simulation/scenarios/compare", data),
  createDigitalTwin: (data: any) => apiClient.post("/v5/simulation/digital-twins", data),
  listDigitalTwins: () => apiClient.get("/v5/simulation/digital-twins"),
  addTwinEntity: (twinId: string, data: any) => apiClient.post(`/v5/simulation/digital-twins/${twinId}/entities`, data),
  getTwinEntities: (twinId: string) => apiClient.get(`/v5/simulation/digital-twins/${twinId}/entities`),
  analyzeTwin: (twinId: string) => apiClient.post(`/v5/simulation/digital-twins/${twinId}/analyze`),
  budgetScenario: (currentBudget: number, scenarioDescription: string) =>
    apiClient.post("/v5/simulation/financial/budget-scenario", null, { params: { current_budget: currentBudget, scenario_description: scenarioDescription } }),
  cashflowProjection: (inflows: string, outflows: string, periodMonths?: number) =>
    apiClient.post("/v5/simulation/financial/cashflow", null, { params: { inflows, outflows, period_months: periodMonths || 12 } }),
  revenueForecast: (historicalRevenue: string, growthAssumptions: string) =>
    apiClient.post("/v5/simulation/financial/revenue-forecast", null, { params: { historical_revenue: historicalRevenue, growth_assumptions: growthAssumptions } }),
  costImpactAnalysis: (currentCosts: string, changeScenario: string) =>
    apiClient.post("/v5/simulation/financial/cost-impact", null, { params: { current_costs: currentCosts, change_scenario: changeScenario } }),
  simulateProject: (projectData: string, scenario: string) =>
    apiClient.post("/v5/simulation/project/simulate", null, { params: { project_data: projectData, scenario } }),
  resourceImpact: (projectData: string, resourceChange: string) =>
    apiClient.post("/v5/simulation/project/resource-impact", null, { params: { project_data: projectData, resource_change: resourceChange } }),
  timelineWhatIf: (projectPlan: string, delayScenario: string) =>
    apiClient.post("/v5/simulation/project/timeline-what-if", null, { params: { project_plan: projectPlan, delay_scenario: delayScenario } }),
  analyzeRisks: (simulationId: string) =>
    apiClient.post("/v5/simulation/risks/analyze", null, { params: { simulation_id: simulationId } }),
  getRiskMatrix: () => apiClient.get("/v5/simulation/risks/matrix"),
  optimizeResources: (data: any) => apiClient.post("/v5/simulation/optimize", data),
  forecast: (simulationId: string, metricName: string, predictionType: string) =>
    apiClient.post("/v5/simulation/forecast", null, { params: { simulation_id: simulationId, metric_name: metricName, prediction_type: predictionType } }),
  generateReport: (simulationId: string, reportType?: string) =>
    apiClient.post("/v5/simulation/reports/generate", null, { params: { simulation_id: simulationId, report_type: reportType || "summary" } }),
  getAnalyticsDashboard: () => apiClient.get("/v5/simulation/analytics/dashboard"),
};

export const v5CollaborationApi = {
  createSession: (data: any) => apiClient.post("/v5/collaboration/sessions", data),
  listSessions: (sessionType?: string, status?: string) =>
    apiClient.get("/v5/collaboration/sessions", { params: { session_type: sessionType, status } }),
  getSession: (id: string) => apiClient.get(`/v5/collaboration/sessions/${id}`),
  startSession: (id: string) => apiClient.post(`/v5/collaboration/sessions/${id}/start`),
  endSession: (id: string) => apiClient.post(`/v5/collaboration/sessions/${id}/end`),
  joinSession: (sessionId: string, role?: string) =>
    apiClient.post(`/v5/collaboration/sessions/${sessionId}/join`, null, { params: { role: role || "participant" } }),
  leaveSession: (sessionId: string) =>
    apiClient.post(`/v5/collaboration/sessions/${sessionId}/leave`),
  getParticipants: (sessionId: string) =>
    apiClient.get(`/v5/collaboration/sessions/${sessionId}/participants`),
  sendMessage: (data: any) => apiClient.post("/v5/collaboration/messages", data),
  getMessages: (sessionId: string, limit?: number) =>
    apiClient.get(`/v5/collaboration/sessions/${sessionId}/messages`, { params: { limit } }),
  createWhiteboard: (data: any) => apiClient.post("/v5/collaboration/whiteboards", data),
  getWhiteboard: (id: string) => apiClient.get(`/v5/collaboration/whiteboards/${id}`),
  updateWhiteboard: (id: string, data: any) =>
    apiClient.patch(`/v5/collaboration/whiteboards/${id}`, data),
  listWhiteboards: (sessionId: string) =>
    apiClient.get(`/v5/collaboration/sessions/${sessionId}/whiteboards`),
  lockWhiteboard: (id: string, locked?: boolean) =>
    apiClient.post(`/v5/collaboration/whiteboards/${id}/lock`, null, { params: { locked: locked !== false } }),
  aiWhiteboardSuggest: (id: string, prompt: string) =>
    apiClient.post(`/v5/collaboration/whiteboards/${id}/ai-suggest`, null, { params: { prompt } }),
  generateInsights: (sessionId: string) =>
    apiClient.post(`/v5/collaboration/sessions/${sessionId}/insights`),
  getInsights: (sessionId: string) =>
    apiClient.get(`/v5/collaboration/sessions/${sessionId}/insights`),
  startRecording: (sessionId: string, recordingType?: string) =>
    apiClient.post("/v5/collaboration/recordings/start", null, { params: { session_id: sessionId, recording_type: recordingType || "video" } }),
  stopRecording: (recordingId: string, fileUrl?: string, duration?: number, fileSize?: number) =>
    apiClient.post(`/v5/collaboration/recordings/${recordingId}/stop`, null, { params: { file_url: fileUrl, duration, file_size: fileSize } }),
  transcribeRecording: (recordingId: string) =>
    apiClient.post(`/v5/collaboration/recordings/${recordingId}/transcribe`),
  listRecordings: (sessionId: string) =>
    apiClient.get(`/v5/collaboration/sessions/${sessionId}/recordings`),
  startScreenShare: (sessionId: string, streamUrl?: string) =>
    apiClient.post("/v5/collaboration/screen-share/start", null, { params: { session_id: sessionId, stream_url: streamUrl } }),
  stopScreenShare: (shareId: string) =>
    apiClient.post(`/v5/collaboration/screen-share/${shareId}/stop`),
  listScreenShares: (sessionId: string) =>
    apiClient.get(`/v5/collaboration/sessions/${sessionId}/screen-shares`),
  createAgent: (data: any) => apiClient.post("/v5/collaboration/agents", data),
  listAgents: () => apiClient.get("/v5/collaboration/agents"),
  joinAgentToSession: (data: any) => apiClient.post("/v5/collaboration/agents/join", data),
  chatWithAgent: (agentId: string, sessionId: string, message: string) =>
    apiClient.post(`/v5/collaboration/agents/${agentId}/chat`, null, { params: { session_id: sessionId, message } }),
  createDocumentCollab: (sessionId: string, documentId: string, documentType: string, title: string) =>
    apiClient.post("/v5/collaboration/documents", null, { params: { session_id: sessionId, document_id: documentId, document_type: documentType, title } }),
  updateDocumentCollab: (docId: string, content: any) =>
    apiClient.patch(`/v5/collaboration/documents/${docId}`, content),
  lockDocument: (docId: string) =>
    apiClient.post(`/v5/collaboration/documents/${docId}/lock`),
  unlockDocument: (docId: string) =>
    apiClient.post(`/v5/collaboration/documents/${docId}/unlock`),
  listDocumentCollabs: (sessionId: string) =>
    apiClient.get(`/v5/collaboration/sessions/${sessionId}/documents`),
  aiEditDocument: (docId: string, instruction: string) =>
    apiClient.post(`/v5/collaboration/documents/${docId}/ai-edit`, null, { params: { instruction } }),
  getPresence: (sessionId: string) =>
    apiClient.get(`/v5/collaboration/sessions/${sessionId}/presence`),
  broadcastEvent: (sessionId: string, eventType: string, payload: any) =>
    apiClient.post(`/v5/collaboration/sessions/${sessionId}/broadcast`, null, { params: { event_type: eventType }, data: payload }),
  getRecentActivity: (sessionId: string, since?: string, limit?: number) =>
    apiClient.get(`/v5/collaboration/sessions/${sessionId}/activity`, { params: { since, limit } }),
  getDashboard: () => apiClient.get("/v5/collaboration/dashboard"),
};

export const v5ConnectorApi = {
  listDefinitions: (category?: string, connectorType?: string) =>
    apiClient.get("/v5/connector/definitions", { params: { category, connector_type: connectorType } }),
  install: (data: any) => apiClient.post("/v5/connector/install", data),
  listIntegrations: () => apiClient.get("/v5/connector/integrations"),
  getIntegration: (id: string) => apiClient.get(`/v5/connector/integrations/${id}`),
  uninstall: (id: string) => apiClient.delete(`/v5/connector/integrations/${id}`),
  authenticate: (data: any) => apiClient.post("/v5/connector/authenticate", data),
  rotateCredentials: (credentialId: string) =>
    apiClient.post(`/v5/connector/credentials/rotate/${credentialId}`),
  createApiKey: (data: any) => apiClient.post("/v5/connector/api-keys", data),
  listApiKeys: () => apiClient.get("/v5/connector/api-keys"),
  revokeApiKey: (keyId: string) => apiClient.delete(`/v5/connector/api-keys/${keyId}`),
  startSync: (data: any) => apiClient.post("/v5/connector/sync", data),
  completeSync: (jobId: string, stats?: any) =>
    apiClient.post(`/v5/connector/sync/${jobId}/complete`, stats || {}),
  listSyncJobs: (integrationId?: string) =>
    apiClient.get("/v5/connector/sync/jobs", { params: integrationId ? { integration_id: integrationId } : {} }),
  runAiSync: (integrationId: string) =>
    apiClient.post(`/v5/connector/sync/ai/${integrationId}`),
  getSyncSummary: () => apiClient.get("/v5/connector/sync/summary"),
  registerWebhook: (data: any) => apiClient.post("/v5/connector/webhooks/register", data),
  listWebhookEvents: (status?: string) =>
    apiClient.get("/v5/connector/webhooks/events", { params: status ? { status } : {} }),
  processWebhookEvent: (eventId: string) =>
    apiClient.post(`/v5/connector/webhooks/${eventId}/process`),
  createCustomConnector: (data: any) => apiClient.post("/v5/connector/custom/create", data),
  listCustomConnectors: () => apiClient.get("/v5/connector/custom"),
  deleteCustomConnector: (endpointId: string) =>
    apiClient.delete(`/v5/connector/custom/${endpointId}`),
  executeCustomApi: (endpointId: string, action: string, params?: any) =>
    apiClient.post(`/v5/connector/custom/${endpointId}/execute`, null, { params: { action, ...(params ? { params: JSON.stringify(params) } : {}) } }),
  queryConnector: (data: any) => apiClient.post("/v5/connector/query", data),
  generateConnectorCode: (spec: any) => apiClient.post("/v5/connector/sdk/generate", spec),
  validateConnector: (connectorId: string) =>
    apiClient.post(`/v5/connector/sdk/validate/${connectorId}`),
  testConnection: (integrationId: string) =>
    apiClient.post(`/v5/connector/sdk/test/${integrationId}`),
  listMarketplace: (category?: string, search?: string) =>
    apiClient.get("/v5/connector/marketplace", { params: { category, search } }),
  getMarketplaceItem: (itemId: string) =>
    apiClient.get(`/v5/connector/marketplace/${itemId}`),
  getLogs: (integrationId?: string, level?: string, limit?: number) =>
    apiClient.get("/v5/connector/logs", { params: { integration_id: integrationId, level, limit } }),
  grantPermission: (integrationId: string, principalType: string, principalId: string, permission: string) =>
    apiClient.post("/v5/connector/permissions/grant", null, { params: { integration_id: integrationId, principal_type: principalType, principal_id: principalId, permission } }),
  revokePermission: (permissionId: string) =>
    apiClient.delete(`/v5/connector/permissions/${permissionId}`),
  listPermissions: (integrationId: string) =>
    apiClient.get(`/v5/connector/permissions/${integrationId}`),
  getAnalytics: () => apiClient.get("/v5/connector/analytics"),
  analyzeLogs: () => apiClient.post("/v5/connector/analytics/logs/analyze"),
  getDashboard: () => apiClient.get("/v5/connector/dashboard"),
};

export const v5ComplianceApi = {
  analyzePolicy: (data: any) => apiClient.post("/v5/compliance/policies/analyze", data),
  checkPolicy: (data: any) => apiClient.post("/v5/compliance/policies/check", data),
  listPolicies: (policyType?: string) =>
    apiClient.get("/v5/compliance/policies", { params: policyType ? { policy_type: policyType } : {} }),
  reviewDocument: (data: any) => apiClient.post("/v5/compliance/documents/review", data),
  createAudit: (data: any) => apiClient.post("/v5/compliance/audits", data),
  listAudits: (auditType?: string) =>
    apiClient.get("/v5/compliance/audits", { params: auditType ? { audit_type: auditType } : {} }),
  generateAuditChecklist: (auditId: string) =>
    apiClient.post(`/v5/compliance/audits/${auditId}/checklist`),
  generateAuditPackage: (auditId: string) =>
    apiClient.post(`/v5/compliance/audits/${auditId}/package`),
  createFinding: (data: any) => apiClient.post("/v5/compliance/findings", data),
  listFindings: (severity?: string, status?: string) =>
    apiClient.get("/v5/compliance/findings", { params: { severity, status } }),
  createCorrectiveAction: (data: any) => apiClient.post("/v5/compliance/corrective-actions", data),
  listCorrectiveActions: (status?: string) =>
    apiClient.get("/v5/compliance/corrective-actions", { params: status ? { status } : {} }),
  updateActionStatus: (actionId: string, status: string, verificationNotes?: string) =>
    apiClient.patch(`/v5/compliance/corrective-actions/${actionId}/status`, null, { params: { status, verification_notes: verificationNotes } }),
  registerRegulation: (name: string, jurisdiction: string, category: string, description: string) =>
    apiClient.post("/v5/compliance/regulations", null, { params: { name, jurisdiction, category, description } }),
  listRegulations: (category?: string) =>
    apiClient.get("/v5/compliance/regulations", { params: category ? { category } : {} }),
  analyzeRegulationImpact: (regulationId: string) =>
    apiClient.post(`/v5/compliance/regulations/${regulationId}/analyze`),
  assessRisks: () => apiClient.post("/v5/compliance/risk/assess"),
  getRiskDashboard: () => apiClient.get("/v5/compliance/risk/dashboard"),
  generateComplianceReport: (reportType?: string) =>
    apiClient.post("/v5/compliance/reports/generate", null, { params: { report_type: reportType || "summary" } }),
  getComplianceDashboard: () => apiClient.get("/v5/compliance/dashboard"),
  queryCompliance: (query: string) =>
    apiClient.post("/v5/compliance/query", null, { params: { query } }),
  getIndustryPacks: (industry: string) =>
    apiClient.get("/v5/compliance/industry-packs", { params: { industry } }),
};

export const v5CopilotApi = {
  listConfigs: (industry?: string) =>
    apiClient.get("/v5/copilot/configs", { params: industry ? { industry } : {} }),
  createConfig: (industry: string, name?: string) =>
    apiClient.post("/v5/copilot/configs", null, { params: { industry, name } }),
  chat: (data: any) => apiClient.post("/v5/copilot/chat", data),
  listSessions: (copilotId?: string) =>
    apiClient.get("/v5/copilot/sessions", { params: copilotId ? { copilot_id: copilotId } : {} }),
  getSessionMessages: (sessionId: string) =>
    apiClient.get(`/v5/copilot/sessions/${sessionId}/messages`),
  ngoAnalyzeGrant: (grantDescription: string) =>
    apiClient.post("/v5/copilot/industry/ngo/analyze-grant", null, { params: { grant_description: grantDescription } }),
  ngoDraftProposal: (orgInfo: string, grantInfo: string) =>
    apiClient.post("/v5/copilot/industry/ngo/draft-proposal", null, { params: { org_info: orgInfo, grant_info: grantInfo } }),
  financeAnalyzeBudget: (budgetData: string) =>
    apiClient.post("/v5/copilot/industry/finance/analyze-budget", null, { params: { budget_data: budgetData } }),
  financeForecast: (historicalData: string, period?: string) =>
    apiClient.post("/v5/copilot/industry/finance/forecast", null, { params: { historical_data: historicalData, period: period || "quarterly" } }),
  financeDetectAnomalies: (transactions: string) =>
    apiClient.post("/v5/copilot/industry/finance/detect-anomalies", null, { params: { transactions } }),
  hospitalityAnalyzeOccupancy: (occupancyData: string) =>
    apiClient.post("/v5/copilot/industry/hospitality/analyze-occupancy", null, { params: { occupancy_data: occupancyData } }),
  hospitalityOptimizePricing: (propertyData: string, marketData: string) =>
    apiClient.post("/v5/copilot/industry/hospitality/optimize-pricing", null, { params: { property_data: propertyData, market_data: marketData } }),
  educationPlanLesson: (subject: string, grade: string, topic: string, duration: number) =>
    apiClient.post("/v5/copilot/industry/education/plan-lesson", null, { params: { subject, grade, topic, duration } }),
  educationCreateAssessment: (subject: string, grade: string, topic: string, questionCount: number) =>
    apiClient.post("/v5/copilot/industry/education/create-assessment", null, { params: { subject, grade, topic, question_count: questionCount } }),
  agriculturePlanFarming: (farmData: string) =>
    apiClient.post("/v5/copilot/industry/agriculture/plan-farming", null, { params: { farm_data: farmData } }),
  agricultureMarketInsights: (cropType: string, region: string) =>
    apiClient.post("/v5/copilot/industry/agriculture/market-insights", null, { params: { crop_type: cropType, region } }),
  businessAnalyzeStrategy: (companyData: string, marketData: string) =>
    apiClient.post("/v5/copilot/industry/business/analyze-strategy", null, { params: { company_data: companyData, market_data: marketData } }),
  businessAnalyzeKpis: (kpiData: string) =>
    apiClient.post("/v5/copilot/industry/business/analyze-kpis", null, { params: { kpi_data: kpiData } }),
  businessCustomerInsights: (customerData: string) =>
    apiClient.post("/v5/copilot/industry/business/customer-insights", null, { params: { customer_data: customerData } }),
  createWorkflow: (name: string, description: string, workflowType: string, steps: string) =>
    apiClient.post("/v5/copilot/workflows", null, { params: { name, description, workflow_type: workflowType, steps } }),
  listWorkflows: () => apiClient.get("/v5/copilot/workflows"),
  executeWorkflow: (data: any) => apiClient.post("/v5/copilot/workflows/execute", data),
  generateRecommendations: (sessionId: string) =>
    apiClient.post(`/v5/copilot/recommendations/generate`, null, { params: { session_id: sessionId } }),
  createApproval: (data: any) => apiClient.post("/v5/copilot/approvals", data),
  listPendingApprovals: () => apiClient.get("/v5/copilot/approvals/pending"),
  reviewApproval: (id: string, data: any) => apiClient.post(`/v5/copilot/approvals/${id}/review`, data),
  getAnalyticsDashboard: () => apiClient.get("/v5/copilot/analytics/dashboard"),
};

export const v5KnowledgeApi = {
  connectSource: (data: any) => apiClient.post("/v5/knowledge/connectors", data),
  listConnectors: () => apiClient.get("/v5/knowledge/connectors"),
  syncConnector: (id: string) => apiClient.post(`/v5/knowledge/connectors/${id}/sync`),
  disconnectSource: (id: string) => apiClient.delete(`/v5/knowledge/connectors/${id}`),
  indexDocument: (connectorId: string, title: string, content?: string, fileType?: string) =>
    apiClient.post("/v5/knowledge/documents/index", null, { params: { connector_id: connectorId, title, content, file_type: fileType } }),
  listDocuments: (connectorId?: string) =>
    apiClient.get("/v5/knowledge/documents", { params: connectorId ? { connector_id: connectorId } : {} }),
  search: (data: any) => apiClient.post("/v5/knowledge/search", data),
  queryWithReasoning: (query: string) =>
    apiClient.post("/v5/knowledge/query", null, { params: { query } }),
  queryKnowledgeGraph: (data: any) => apiClient.post("/v5/knowledge/graph/query", data),
};

export const v6GovernanceApi = {
  listPrompts: (params?: any) => apiClient.get("/v6/governance/prompts", { params }),
  getPrompt: (id: number) => apiClient.get(`/v6/governance/prompts/${id}`),
  createPrompt: (data: any) => apiClient.post("/v6/governance/prompts", data),
  listPromptVersions: (promptId: number) => apiClient.get(`/v6/governance/prompts/${promptId}/versions`),
  createPromptVersion: (promptId: number, data: any) => apiClient.post(`/v6/governance/prompts/${promptId}/versions`, data),
  evaluate: (data: any) => apiClient.post("/v6/governance/evaluate", data),
  hallucinationCheck: (data: any) => apiClient.post("/v6/governance/hallucination-check", data),
  qualityReport: (model: string) => apiClient.get(`/v6/governance/quality/${model}`),
  listModels: () => apiClient.get("/v6/governance/models"),
  getModel: (model: string) => apiClient.get(`/v6/governance/models/${model}`),
  createReview: (data: any) => apiClient.post("/v6/governance/reviews", data),
  getReview: (id: number) => apiClient.get(`/v6/governance/reviews/${id}`),
  approveReview: (id: number, data?: any) => apiClient.post(`/v6/governance/reviews/${id}/approve`, data),
  rejectReview: (id: number, data?: any) => apiClient.post(`/v6/governance/reviews/${id}/reject`, data),
  logDecision: (data: any) => apiClient.post("/v6/governance/decisions", data),
  listDecisions: (limit?: number) => apiClient.get("/v6/governance/decisions", { params: { limit } }),
  submitFeedback: (data: any) => apiClient.post("/v6/governance/feedback", data),
  dashboard: () => apiClient.get("/v6/governance/dashboard"),
};

export const businessApi = {
  query: (data: any) => apiClient.post("/business/query", data),
  generateReport: (params: any) => apiClient.post("/business/reports/generate", null, { params }),
  reports: (params: any) => apiClient.get("/business/reports", { params }),
  metrics: (params: any) => apiClient.get("/business/metrics", { params }),
  createMetric: (params: any) => apiClient.post("/business/metrics", null, { params }),
  dashboard: (orgId: string) => apiClient.get(`/business/dashboard/${orgId}`),
  createApproval: (data: any) => apiClient.post("/business/approvals", data),
  pendingApprovals: (orgId: string) => apiClient.get("/business/approvals/pending", { params: { organization_id: orgId } }),
  approveRequest: (id: string, notes?: string) => apiClient.post(`/business/approvals/${id}/approve`, null, { params: { notes } }),
  rejectRequest: (id: string, reason: string) => apiClient.post(`/business/approvals/${id}/reject`, null, { params: { reason } }),
  recordTransaction: (data: any) => apiClient.post("/business/financial/records", data),
  financialSummary: (orgId: string, months?: number) => apiClient.get(`/business/financial/summary/${orgId}`, { params: { months } }),
  financialForecast: (orgId: string, months?: number) => apiClient.post(`/business/financial/forecast/${orgId}`, null, { params: { months } }),
  createWorkflow: (data: any) => apiClient.post("/business/workflows", data),
  workflows: (orgId: string) => apiClient.get("/business/workflows", { params: { organization_id: orgId } }),
  executeWorkflow: (id: string, orgId: string) => apiClient.post(`/business/workflows/${id}/execute`, null, { params: { organization_id: orgId } }),
  addKnowledge: (data: any) => apiClient.post("/business/knowledge", data),
  queryKnowledge: (orgId: string, query: string) => apiClient.get("/business/knowledge/query", { params: { organization_id: orgId, query } }),
  listKnowledge: (orgId: string) => apiClient.get("/business/knowledge", { params: { organization_id: orgId } }),
  deleteKnowledge: (id: string) => apiClient.delete(`/business/knowledge/${id}`),
  alerts: (orgId: string) => apiClient.get("/business/alerts", { params: { organization_id: orgId } }),
};
