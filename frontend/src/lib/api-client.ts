import axios, {
  AxiosError,
  InternalAxiosRequestConfig,
  AxiosResponse,
} from "axios";

// --- Safe storage helpers (SSR-safe) ---

function getStorageItem(key: string): string | null {
  if (typeof window === "undefined") return null;
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function setStorageItem(key: string, value: string): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(key, value);
  } catch {
    // ignore quota errors
  }
}

function removeStorageItem(key: string): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.removeItem(key);
  } catch {
    // ignore
  }
}

// --- Axios instance ---

const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const apiClient = axios.create({
  baseURL: apiBase,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000,
});

// Request interceptor: attach access token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getStorageItem("access_token");
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: handle 401 with refresh token rotation
type RetryConfig = InternalAxiosRequestConfig & { _retry?: boolean };

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: unknown) => void;
  reject: (reason?: unknown) => void;
}> = [];

function processQueue(error: unknown, token: string | null = null) {
  failedQueue.forEach((prom) => {
    if (error) prom.reject(error);
    else prom.resolve(token);
  });
  failedQueue = [];
}

apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as RetryConfig | undefined;

    // Only attempt refresh for 401 and if we haven't retried yet
    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry
    ) {
      // Avoid infinite loop on refresh endpoint itself
      if (originalRequest.url?.includes("/auth/refresh")) {
        removeStorageItem("access_token");
        removeStorageItem("refresh_token");
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            if (originalRequest.headers && token) {
              (originalRequest.headers as Record<string, string>).Authorization = `Bearer ${token}`;
            }
            return apiClient(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = getStorageItem("refresh_token");
      if (!refreshToken) {
        isRefreshing = false;
        removeStorageItem("access_token");
        removeStorageItem("refresh_token");
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        return Promise.reject(error);
      }

      try {
        // Use plain axios for refresh to avoid interceptor loops
        const response = await axios.post<{ access_token: string; refresh_token: string }>(
          `${apiBase}/auth/refresh`,
          { refresh_token: refreshToken }
        );
        const { access_token, refresh_token: newRefresh } = response.data;
        setStorageItem("access_token", access_token);
        setStorageItem("refresh_token", newRefresh);

        // Update header for original request
        if (originalRequest.headers) {
          (originalRequest.headers as Record<string, string>).Authorization = `Bearer ${access_token}`;
        }

        processQueue(null, access_token);
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        removeStorageItem("access_token");
        removeStorageItem("refresh_token");
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export { apiClient };
export default apiClient;

// --- Typed API helpers ---

type ApiPayload = Record<string, unknown> | FormData;

export const authApi = {
  register: (data: { email: string; password: string; display_name: string }) =>
    apiClient.post("/auth/register", data),
  login: (data: { email: string; password: string }) =>
    apiClient.post("/auth/login", data),
  me: () => apiClient.get("/users/me"),
  refresh: (refresh_token: string) =>
    apiClient.post("/auth/refresh", { refresh_token }),
};

export const documentsApi = {
  list: (projectId?: string) =>
    apiClient.get("/documents", { params: { project_id: projectId } }),
  create: (data: ApiPayload) => apiClient.post("/documents", data),
  get: (id: string) => apiClient.get(`/documents/${id}`),
  update: (id: string, data: ApiPayload) => apiClient.put(`/documents/${id}`, data),
  delete: (id: string) => apiClient.delete(`/documents/${id}`),
  humanize: (id: string, data: ApiPayload) =>
    apiClient.post(`/documents/${id}/humanize`, data),
  humanizeStream: (id: string) =>
    `${apiClient.defaults.baseURL}/documents/${id}/humanize/stream`,
  analyze: (id: string) => apiClient.post(`/documents/${id}/analyze`),
  summarize: (id: string, data: ApiPayload) =>
    apiClient.post(`/documents/${id}/summarize`, data),
  translate: (id: string, data: ApiPayload) =>
    apiClient.post(`/documents/${id}/translate`, data),
  grammar: (id: string) => apiClient.post(`/documents/${id}/grammar`),
  versions: {
    list: (id: string) => apiClient.get(`/documents/${id}/versions`),
    save: (id: string, data: ApiPayload) =>
      apiClient.post(`/documents/${id}/versions/save`, data),
    restore: (id: string, versionId: string) =>
      apiClient.post(`/documents/${id}/versions/${versionId}/restore`),
  },
  export: (id: string, data: ApiPayload) =>
    apiClient.post(`/documents/${id}/export`, data, { responseType: "blob" }),
};

export const websitesApi = {
  list: (projectId?: string) =>
    apiClient.get("/websites", { params: { project_id: projectId } }),
  create: (data: ApiPayload) => apiClient.post("/websites", data),
  get: (id: string) => apiClient.get(`/websites/${id}`),
  update: (id: string, data: ApiPayload) =>
    apiClient.put(`/websites/${id}`, data),
  delete: (id: string) => apiClient.delete(`/websites/${id}`),
  customize: (id: string, data: ApiPayload) =>
    apiClient.post(`/websites/${id}/customize`, data),
  generate: (id: string, data: ApiPayload) =>
    apiClient.post(`/websites/${id}/generate`, data),
  preview: (id: string) => apiClient.post(`/websites/${id}/preview`),
  publish: (id: string, data: ApiPayload) =>
    apiClient.post(`/websites/${id}/publish`, data),
  deploy: (id: string, data: ApiPayload) =>
    apiClient.post(`/websites/${id}/deploy`, data),
  templates: () => apiClient.get("/websites/templates/list"),
  branding: (data: ApiPayload) => apiClient.post("/websites/branding", data),
  export: (id: string) =>
    apiClient.post(`/websites/${id}/export`, {}, { responseType: "blob" }),
};

export const botsApi = {
  list: (projectId?: string) =>
    apiClient.get("/bots", { params: { project_id: projectId } }),
  create: (data: ApiPayload) => apiClient.post("/bots", data),
  get: (id: string) => apiClient.get(`/bots/${id}`),
  update: (id: string, data: ApiPayload) => apiClient.put(`/bots/${id}`, data),
  delete: (id: string) => apiClient.delete(`/bots/${id}`),
  test: (id: string, data: ApiPayload) =>
    apiClient.post(`/bots/${id}/test`, data),
  deploy: (id: string, data: ApiPayload) =>
    apiClient.post(`/bots/${id}/deploy`, data),
  train: (id: string, data: ApiPayload) =>
    apiClient.post(`/bots/${id}/train`, data),
  analytics: (id: string) => apiClient.get(`/bots/${id}/analytics`),
  conversations: (id: string) =>
    apiClient.get(`/bots/${id}/conversations`),
  getConversationMessages: (botId: string, convId: string) =>
    apiClient.get(`/bots/${botId}/conversations/${convId}/messages`),
  embed: (id: string, data: ApiPayload) =>
    apiClient.post(`/bots/${id}/embed`, data),
  testStreamUrl: (id: string) =>
    `${apiClient.defaults.baseURL}/bots/${id}/test/stream`,
};

export const chatApi = {
  sessions: () => apiClient.get("/chat/sessions"),
  createSession: (data: ApiPayload) =>
    apiClient.post("/chat/sessions", data),
  getSession: (id: string) => apiClient.get(`/chat/sessions/${id}`),
  deleteSession: (id: string) => apiClient.delete(`/chat/sessions/${id}`),
  messages: (sessionId: string) =>
    apiClient.get(`/chat/sessions/${sessionId}/messages`),
  sendMessage: (sessionId: string, data: ApiPayload) =>
    apiClient.post(`/chat/sessions/${sessionId}/messages`, data),
  sendMessageStreamUrl: (sessionId: string) =>
    `${apiClient.defaults.baseURL}/chat/sessions/${sessionId}/messages/stream`,
};

export const codeApi = {
  projects: (projectId?: string) =>
    apiClient.get("/code/projects", { params: { project_id: projectId } }),
  createProject: (data: ApiPayload) =>
    apiClient.post("/code/projects", data),
  getProject: (id: string) => apiClient.get(`/code/projects/${id}`),
  updateProject: (id: string, data: ApiPayload) =>
    apiClient.put(`/code/projects/${id}`, data),
  deleteProject: (id: string) => apiClient.delete(`/code/projects/${id}`),
  generate: (data: ApiPayload) => apiClient.post("/code/generate", data),
  generateForProject: (id: string, data: ApiPayload) =>
    apiClient.post(`/code/projects/${id}/generate`, data),
  explain: (data: ApiPayload) => apiClient.post("/code/explain", data),
  review: (data: ApiPayload) => apiClient.post("/code/review", data),
};

export const projectsApi = {
  list: (type?: string) => apiClient.get("/projects", { params: { type } }),
  create: (data: ApiPayload) => apiClient.post("/projects", data),
  get: (id: string) => apiClient.get(`/projects/${id}`),
  update: (id: string, data: ApiPayload) =>
    apiClient.put(`/projects/${id}`, data),
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
  create: (data: ApiPayload) => apiClient.post("/agents", data),
  get: (id: string) => apiClient.get(`/agents/${id}`),
  update: (id: string, data: ApiPayload) => apiClient.put(`/agents/${id}`, data),
  delete: (id: string) => apiClient.delete(`/agents/${id}`),
  templates: (category?: string) =>
    apiClient.get("/agents/templates", { params: { category } }),
  marketplace: (category?: string) =>
    apiClient.get("/agents/marketplace", { params: { category } }),
  clone: (id: string) => apiClient.post(`/agents/${id}/clone`),
  publish: (id: string, data?: ApiPayload) =>
    apiClient.post(`/agents/${id}/publish`, data),
  chat: (id: string, data: ApiPayload) =>
    apiClient.post(`/agents/${id}/chat`, data),
  chatStreamUrl: (id: string) =>
    `${apiClient.defaults.baseURL}/agents/${id}/chat/stream`,
  tasks: {
    list: (agentId: string, status?: string) =>
      apiClient.get(`/agents/${agentId}/tasks`, { params: { status } }),
    create: (agentId: string, data: ApiPayload) =>
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
    create: (agentId: string, data: ApiPayload) =>
      apiClient.post(`/agents/${agentId}/workflows`, data),
    update: (agentId: string, workflowId: string, data: ApiPayload) =>
      apiClient.put(`/agents/${agentId}/workflows/${workflowId}`, data),
    delete: (agentId: string, workflowId: string) =>
      apiClient.delete(`/agents/${agentId}/workflows/${workflowId}`),
  },
  skills: {
    list: (agentId: string) => apiClient.get(`/agents/${agentId}/skills`),
    add: (agentId: string, data: ApiPayload) =>
      apiClient.post(`/agents/${agentId}/skills`, data),
    delete: (agentId: string, skillId: string) =>
      apiClient.delete(`/agents/${agentId}/skills/${skillId}`),
  },
  tools: {
    list: (agentId: string) => apiClient.get(`/agents/${agentId}/tools`),
    add: (agentId: string, data: ApiPayload) =>
      apiClient.post(`/agents/${agentId}/tools`, data),
    delete: (agentId: string, toolId: string) =>
      apiClient.delete(`/agents/${agentId}/tools/${toolId}`),
  },
  memories: {
    list: (agentId: string, type?: string, category?: string) =>
      apiClient.get(`/agents/${agentId}/memories`, {
        params: { memory_type: type, category },
      }),
    add: (agentId: string, data: ApiPayload) =>
      apiClient.post(`/agents/${agentId}/memories`, data),
    delete: (agentId: string, memoryId: string) =>
      apiClient.delete(`/agents/${agentId}/memories/${memoryId}`),
    clear: (agentId: string) =>
      apiClient.delete(`/agents/${agentId}/memories`),
  },
};

// NOTE: remaining APIs keep generic Record types but with basic typing improvements
type GenericParams = Record<string, unknown>;

export const billingApi = {
  plans: () => apiClient.get("/billing/plans"),
  subscription: (orgId: string) =>
    apiClient.get(`/billing/subscriptions/${orgId}`),
  checkout: (data: GenericParams) => apiClient.post("/billing/checkout", data),
  portal: (data: GenericParams) => apiClient.post("/billing/portal", data),
  invoices: (orgId: string) =>
    apiClient.get(`/billing/invoices/${orgId}`),
  cancel: (subId: string) =>
    apiClient.post(`/billing/subscriptions/${subId}/cancel`),
};

export const adminApi = {
  overview: () => apiClient.get("/admin/overview"),
  users: (params?: GenericParams) =>
    apiClient.get("/admin/users", { params }),
  suspendUser: (userId: string) =>
    apiClient.put(`/admin/users/${userId}/suspend`),
  restoreUser: (userId: string) =>
    apiClient.put(`/admin/users/${userId}/restore`),
  dailyUsage: (days?: number) =>
    apiClient.get("/admin/usage/daily", { params: { days } }),
  marketplaceItems: (params?: GenericParams) =>
    apiClient.get("/admin/marketplace/items", { params }),
  approveItem: (itemId: string) =>
    apiClient.put(`/admin/marketplace/items/${itemId}/approve`),
  rejectItem: (itemId: string) =>
    apiClient.put(`/admin/marketplace/items/${itemId}/reject`),
  auditLogs: (params?: GenericParams) =>
    apiClient.get("/admin/audit-logs", { params }),
  settings: () => apiClient.get("/admin/settings"),
  updateSettings: (data: GenericParams) =>
    apiClient.put("/admin/settings", data),
};

export const marketplaceApi = {
  items: (params?: GenericParams) =>
    apiClient.get("/marketplace/items", { params }),
  getItem: (id: string) => apiClient.get(`/marketplace/items/${id}`),
  createItem: (data: GenericParams) =>
    apiClient.post("/marketplace/items", data),
  updateItem: (id: string, data: GenericParams) =>
    apiClient.put(`/marketplace/items/${id}`, data),
  purchase: (id: string) =>
    apiClient.post(`/marketplace/items/${id}/purchase`),
  myItems: () => apiClient.get("/marketplace/my-items"),
  myPurchases: () => apiClient.get("/marketplace/my-purchases"),
  categories: () => apiClient.get("/marketplace/categories"),
};

export const marketplaceExtendedApi = {
  dashboard: () => apiClient.get("/marketplace-extended/dashboard"),
  categories: () => apiClient.get("/marketplace-extended/categories"),
  createCategory: (data: GenericParams) =>
    apiClient.post("/marketplace-extended/categories", null, { params: data }),
  products: (params?: GenericParams) =>
    apiClient.get("/marketplace-extended/products", { params }),
  getProduct: (id: string) =>
    apiClient.get(`/marketplace-extended/products/${id}`),
  publishProduct: (data: GenericParams) =>
    apiClient.post("/marketplace-extended/products", data),
  purchaseProduct: (productId: string, orgId?: string) =>
    apiClient.post(
      `/marketplace-extended/products/${productId}/purchase`,
      null,
      { params: orgId ? { organization_id: orgId } : {} }
    ),
  createReview: (data: GenericParams) =>
    apiClient.post("/marketplace-extended/reviews", data),
  getReviews: (productId: string) =>
    apiClient.get(`/marketplace-extended/reviews/${productId}`),
  getCreatorProfile: () =>
    apiClient.get("/marketplace-extended/creator/profile"),
  updateCreatorProfile: (data: GenericParams) =>
    apiClient.put("/marketplace-extended/creator/profile", data),
  getCreatorDashboard: () =>
    apiClient.get("/marketplace-extended/creator/dashboard"),
  getProductAnalytics: (productId: string) =>
    apiClient.get(`/marketplace-extended/creator/analytics/${productId}`),
  myProducts: () => apiClient.get("/marketplace-extended/my-products"),
  registerPlugin: (data: GenericParams) =>
    apiClient.post("/marketplace-extended/plugins", null, { params: data }),
  listPlugins: (pluginType?: string) =>
    apiClient.get("/marketplace-extended/plugins", {
      params: pluginType ? { plugin_type: pluginType } : {},
    }),
  installPlugin: (pluginId: string, orgId?: string) =>
    apiClient.post(
      `/marketplace-extended/plugins/${pluginId}/install`,
      null,
      { params: orgId ? { organization_id: orgId } : {} }
    ),
  uninstallPlugin: (installationId: string) =>
    apiClient.delete(
      `/marketplace-extended/plugins/install/${installationId}`
    ),
  getInstalledPlugins: (orgId?: string) =>
    apiClient.get("/marketplace-extended/plugins/installed", {
      params: orgId ? { organization_id: orgId } : {},
    }),
  verifyProduct: (productId: string, level?: string) =>
    apiClient.post(`/marketplace-extended/verify/${productId}`, null, {
      params: { level: level || "community" },
    }),
  getVerificationHistory: (productId: string) =>
    apiClient.get(`/marketplace-extended/verify/${productId}/history`),
  createEnterpriseListing: (data: GenericParams) =>
    apiClient.post("/marketplace-extended/enterprise", data),
  getEnterpriseListing: (productId: string, orgId: string) =>
    apiClient.get(`/marketplace-extended/enterprise/${productId}`, {
      params: { organization_id: orgId },
    }),
  generateSDK: (data: GenericParams) =>
    apiClient.post("/marketplace-extended/sdk", data),
  getSDKTemplate: (language?: string) =>
    apiClient.get(`/marketplace-extended/sdk/${language || "python"}`),
  getProductVersions: (productId: string) =>
    apiClient.get(`/marketplace-extended/products/${productId}/versions`),
  createProductVersion: (
    productId: string,
    version: string,
    changelog?: string
  ) =>
    apiClient.post(
      `/marketplace-extended/products/${productId}/versions`,
      null,
      { params: { version, changelog } }
    ),
};

export const analyticsApi = {
  usage: (days?: number) =>
    apiClient.get("/analytics/usage", { params: { days } }),
  agents: () => apiClient.get("/analytics/agents"),
  revenue: () => apiClient.get("/analytics/revenue"),
  growth: () => apiClient.get("/analytics/growth"),
};

export const voiceApi = {
  sessions: () => apiClient.get("/voice/sessions"),
  createSession: (data: GenericParams) =>
    apiClient.post("/voice/sessions", data),
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
  assets: (type?: string) =>
    apiClient.get("/vision/assets", { params: { asset_type: type } }),
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
  projects: (orgId?: string) =>
    apiClient.get("/code-studio/projects", {
      params: orgId ? { organization_id: orgId } : {},
    }),
  getProject: (id: string) => apiClient.get(`/code-studio/projects/${id}`),
  createProject: (data: GenericParams) =>
    apiClient.post("/code-studio/projects", data),
  deleteProject: (id: string) =>
    apiClient.delete(`/code-studio/projects/${id}`),
  files: (projectId: string) =>
    apiClient.get(`/code-studio/projects/${projectId}/files`),
  getFile: (fileId: string) => apiClient.get(`/code-studio/files/${fileId}`),
  updateFile: (fileId: string, content: string) =>
    apiClient.put(`/code-studio/files/${fileId}`, null, {
      params: { content },
    }),
  generateApp: (data: GenericParams) =>
    apiClient.post("/code-studio/generate", data),
  generateCode: (data: GenericParams) =>
    apiClient.post("/code-studio/generate-code", data),
  debug: (data: GenericParams) => apiClient.post("/code-studio/debug", data),
  reviewCode: (code: string, language?: string) =>
    apiClient.post("/code-studio/review-code", null, {
      params: { code, language: language || "python" },
    }),
  connectRepo: (data: GenericParams) =>
    apiClient.post("/code-studio/repositories", data),
  repositories: () => apiClient.get("/code-studio/repositories"),
  analyzeRepo: (repoId: string) =>
    apiClient.post(`/code-studio/repositories/${repoId}/analyze`),
  commitMessage: (diff: string) =>
    apiClient.post("/code-studio/commit-message", null, {
      params: { diff },
    }),
  buildProject: (projectId: string) =>
    apiClient.post(`/code-studio/projects/${projectId}/build`),
  builds: (projectId: string) =>
    apiClient.get(`/code-studio/projects/${projectId}/builds`),
  deployProject: (projectId: string, data: GenericParams) =>
    apiClient.post(`/code-studio/projects/${projectId}/deploy`, data),
  deployments: (projectId: string) =>
    apiClient.get(`/code-studio/projects/${projectId}/deployments`),
  generateCICD: (projectId: string, platform?: string) =>
    apiClient.post(`/code-studio/projects/${projectId}/ci-cd`, null, {
      params: { platform: platform || "github" },
    }),
  generateTests: (projectId: string, data: GenericParams) =>
    apiClient.post(`/code-studio/projects/${projectId}/tests`, data),
  testRuns: (projectId: string) =>
    apiClient.get(`/code-studio/projects/${projectId}/tests`),
  securityScan: (projectId: string, data?: GenericParams) =>
    apiClient.post(
      `/code-studio/projects/${projectId}/security-scan`,
      data || { scan_type: "full" }
    ),
  securityScans: (projectId: string) =>
    apiClient.get(`/code-studio/projects/${projectId}/security-scans`),
  securitySummary: (projectId: string) =>
    apiClient.get(`/code-studio/projects/${projectId}/security-summary`),
  generateDoc: (projectId: string, docType?: string) =>
    apiClient.post(`/code-studio/projects/${projectId}/docs`, null, {
      params: { doc_type: docType || "readme" },
    }),
  generateAllDocs: (projectId: string) =>
    apiClient.post(`/code-studio/projects/${projectId}/docs/all`),
  docs: (projectId: string) =>
    apiClient.get(`/code-studio/projects/${projectId}/docs`),
  dashboard: (orgId: string) =>
    apiClient.get(`/code-studio/dashboard/${orgId}`),
};

export const agentNetworkApi = {
  orchestrate: (data: GenericParams) =>
    apiClient.post("/agent-network/orchestrate", data),
  autoCreateTeam: (data: GenericParams) =>
    apiClient.post("/agent-network/teams/auto-create", data),
  teams: (orgId?: string) =>
    apiClient.get("/agent-network/teams", {
      params: orgId ? { organization_id: orgId } : {},
    }),
  getTeam: (id: string) => apiClient.get(`/agent-network/teams/${id}`),
  createTeam: (data: GenericParams) =>
    apiClient.post("/agent-network/teams", data),
  addTeamMember: (teamId: string, data: GenericParams) =>
    apiClient.post(`/agent-network/teams/${teamId}/members`, data),
  removeTeamMember: (teamId: string, memberId: string) =>
    apiClient.delete(`/agent-network/teams/${teamId}/members/${memberId}`),
  deleteTeam: (id: string) =>
    apiClient.delete(`/agent-network/teams/${id}`),
  sendMessage: (
    receiverId: string,
    content: string,
    opts?: GenericParams
  ) =>
    apiClient.post("/agent-network/messages", null, {
      params: { receiver_id: receiverId, content, ...opts },
    }),
  conversation: (a1: string, a2: string) =>
    apiClient.get(`/agent-network/messages/${a1}/${a2}`),
  teamMessages: (teamId: string) =>
    apiClient.get(`/agent-network/messages/team/${teamId}`),
  createDelegation: (data: GenericParams) =>
    apiClient.post("/agent-network/delegations", data),
  delegations: (teamId?: string, status?: string) =>
    apiClient.get("/agent-network/delegations", {
      params: { team_id: teamId, status },
    }),
  completeDelegation: (id: string, data?: GenericParams) =>
    apiClient.post(`/agent-network/delegations/${id}/complete`, data),
  storeMemory: (data: GenericParams) =>
    apiClient.post("/agent-network/memory", data),
  searchMemory: (query: string, teamId?: string, orgId?: string) =>
    apiClient.get("/agent-network/memory/search", {
      params: {
        query_text: query,
        team_id: teamId,
        organization_id: orgId,
      },
    }),
  getTeamMemory: (teamId: string) =>
    apiClient.get(`/agent-network/memory/team/${teamId}`),
  deleteMemory: (id: string) =>
    apiClient.delete(`/agent-network/memory/${id}`),
  createReview: (data: GenericParams) =>
    apiClient.post("/agent-network/reviews", data),
  getReviews: (agentId: string) =>
    apiClient.get(`/agent-network/reviews/${agentId}`),
  performance: (agentId: string) =>
    apiClient.get(`/agent-network/performance/${agentId}`),
  grantPermission: (data: GenericParams) =>
    apiClient.post("/agent-network/permissions", data),
  getPermissions: (agentId: string) =>
    apiClient.get(`/agent-network/permissions/agent/${agentId}`),
  revokePermission: (id: string) =>
    apiClient.delete(`/agent-network/permissions/${id}`),
  checkPermission: (agentId: string, resource: string, action: string) =>
    apiClient.get(
      `/agent-network/permissions/check/${agentId}/${resource}/${action}`
    ),
  conductResearch: (data: GenericParams) =>
    apiClient.post("/agent-network/research", data),
  listResearch: () => apiClient.get("/agent-network/research"),
  getResearch: (id: string) =>
    apiClient.get(`/agent-network/research/${id}`),
  createDevProject: (data: GenericParams) =>
    apiClient.post("/agent-network/dev-projects", data),
  listDevProjects: (orgId?: string) =>
    apiClient.get("/agent-network/dev-projects", {
      params: orgId ? { organization_id: orgId } : {},
    }),
  getDevProject: (id: string) =>
    apiClient.get(`/agent-network/dev-projects/${id}`),
  generateCode: (projectId: string) =>
    apiClient.post(
      `/agent-network/dev-projects/${projectId}/generate-code`
    ),
  securityReview: (projectId: string) =>
    apiClient.post(
      `/agent-network/dev-projects/${projectId}/security-review`
    ),
  runTests: (projectId: string) =>
    apiClient.post(
      `/agent-network/dev-projects/${projectId}/run-tests`
    ),
  completeDevProject: (projectId: string) =>
    apiClient.post(
      `/agent-network/dev-projects/${projectId}/complete`
    ),
  dashboard: (orgId: string) =>
    apiClient.get(`/agent-network/dashboard/${orgId}`),
};

// Re-export remaining APIs with typed generics (shortened for brevity but functional)
export const infrastructureApi = {
  dashboard: () => apiClient.get("/infrastructure/dashboard"),
  regions: () => apiClient.get("/infrastructure/regions"),
  createRegion: (data: GenericParams) =>
    apiClient.post("/infrastructure/regions", null, { params: data }),
  getRegion: (id: string) =>
    apiClient.get(`/infrastructure/regions/${id}`),
  clusters: (regionId?: string) =>
    apiClient.get("/infrastructure/clusters", {
      params: regionId ? { region_id: regionId } : {},
    }),
  createCluster: (data: GenericParams) =>
    apiClient.post("/infrastructure/clusters", null, { params: data }),
  updateClusterHealth: (clusterId: string, status: string) =>
    apiClient.post(
      `/infrastructure/clusters/${clusterId}/health`,
      null,
      { params: { status } }
    ),
  services: (clusterId?: string) =>
    apiClient.get("/infrastructure/services", {
      params: clusterId ? { cluster_id: clusterId } : {},
    }),
  deployService: (data: GenericParams) =>
    apiClient.post("/infrastructure/services", null, { params: data }),
  scaleService: (serviceId: string, targetReplicas: number) =>
    apiClient.post(
      `/infrastructure/services/${serviceId}/scale`,
      null,
      { params: { target_replicas: targetReplicas } }
    ),
  models: (modelType?: string, provider?: string) =>
    apiClient.get("/infrastructure/models", {
      params: { model_type: modelType, provider },
    }),
  registerModel: (data: GenericParams) =>
    apiClient.post("/infrastructure/models", null, { params: data }),
  routeModel: (data: GenericParams) =>
    apiClient.post("/infrastructure/models/route", data),
  securityEvents: (params?: GenericParams) =>
    apiClient.get("/infrastructure/security/events", { params }),
  logSecurityEvent: (data: GenericParams) =>
    apiClient.post("/infrastructure/security/events", null, { params: data }),
  resolveSecurityEvent: (eventId: string, action?: string) =>
    apiClient.post(
      `/infrastructure/security/events/${eventId}/resolve`,
      null,
      { params: { action_taken: action } }
    ),
  securitySummary: () => apiClient.get("/infrastructure/security/summary"),
  metrics: (params?: GenericParams) =>
    apiClient.get("/infrastructure/monitoring/metrics", { params }),
  recordMetric: (data: GenericParams) =>
    apiClient.post("/infrastructure/monitoring/metrics", null, {
      params: data,
    }),
  systemHealth: () => apiClient.get("/infrastructure/monitoring/health"),
  apiUptime: (days?: number) =>
    apiClient.get("/infrastructure/monitoring/uptime", {
      params: { days },
    }),
  backups: (params?: GenericParams) =>
    apiClient.get("/infrastructure/backups", { params }),
  createBackup: (data: GenericParams) =>
    apiClient.post("/infrastructure/backups", null, { params: data }),
  getBackup: (id: string) =>
    apiClient.get(`/infrastructure/backups/${id}`),
  completeBackup: (backupId: string, sizeBytes: number, location: string) =>
    apiClient.post(
      `/infrastructure/backups/${backupId}/complete`,
      null,
      { params: { size_bytes: sizeBytes, location } }
    ),
  backupSummary: () => apiClient.get("/infrastructure/backups/summary"),
  policies: (orgId: string, policyType?: string) =>
    apiClient.get(`/infrastructure/policies/${orgId}`, {
      params: policyType ? { policy_type: policyType } : {},
    }),
  createPolicy: (orgId: string, data: GenericParams) =>
    apiClient.post(`/infrastructure/policies/${orgId}`, null, {
      params: data,
    }),
  complianceReports: (params?: GenericParams) =>
    apiClient.get("/infrastructure/compliance/reports", { params }),
  createComplianceReport: (data: GenericParams) =>
    apiClient.post("/infrastructure/compliance/reports", null, {
      params: data,
    }),
  generateComplianceReport: (reportId: string) =>
    apiClient.post(
      `/infrastructure/compliance/reports/${reportId}/generate`
    ),
  dataResidency: (orgId: string) =>
    apiClient.get(`/infrastructure/data-residency/${orgId}`),
  configureDataResidency: (orgId: string, data: GenericParams) =>
    apiClient.post(
      `/infrastructure/data-residency/${orgId}`,
      null,
      { params: data }
    ),
  apiKeys: (orgId: string) =>
    apiClient.get(`/infrastructure/api-keys/${orgId}`),
  createApiKey: (orgId: string, data: GenericParams) =>
    apiClient.post(`/infrastructure/api-keys/${orgId}`, data),
  deleteApiKey: (keyId: string) =>
    apiClient.delete(`/infrastructure/api-keys/${keyId}`),
  seed: () => apiClient.post("/infrastructure/seed"),
};

export const v3PersonalApi = {
  assistants: () => apiClient.get("/v3/personal/assistants"),
  createAssistant: (data: GenericParams) =>
    apiClient.post("/v3/personal/assistants", null, { params: data }),
  queryAssistant: (data: GenericParams) =>
    apiClient.post("/v3/personal/assistants/query", data),
  memories: (assistantId: string) =>
    apiClient.get(`/v3/personal/assistants/${assistantId}/memories`),
  storeMemory: (assistantId: string, data: GenericParams) =>
    apiClient.post(
      `/v3/personal/assistants/${assistantId}/memories`,
      null,
      { params: data }
    ),
  tasks: (status?: string) =>
    apiClient.get("/v3/personal/tasks", {
      params: status ? { status } : {},
    }),
  createTask: (data: GenericParams) =>
    apiClient.post("/v3/personal/tasks", null, { params: data }),
  completeTask: (taskId: string, result?: string) =>
    apiClient.post(
      `/v3/personal/tasks/${taskId}/complete`,
      null,
      { params: { result } }
    ),
  executives: () => apiClient.get("/v3/personal/executives"),
  createExecutive: (data: GenericParams) =>
    apiClient.post("/v3/personal/executives", null, { params: data }),
  queryExecutive: (execId: string, query: string) =>
    apiClient.post(
      `/v3/personal/executives/${execId}/query`,
      null,
      { params: { query } }
    ),
};

export const v3OrganizationApi = {
  getOS: (orgId: string) =>
    apiClient.get(`/v3/organization/os/${orgId}`),
  createOS: (orgId: string, data: GenericParams) =>
    apiClient.post(`/v3/organization/os/${orgId}`, null, { params: data }),
  departments: (orgId: string) =>
    apiClient.get(`/v3/organization/os/${orgId}/departments`),
  createDepartment: (orgId: string, data: GenericParams) =>
    apiClient.post(
      `/v3/organization/os/${orgId}/departments`,
      null,
      { params: data }
    ),
  departmentAgents: (deptId: string) =>
    apiClient.get(`/v3/organization/departments/${deptId}/agents`),
  workflows: (orgId: string) =>
    apiClient.get(`/v3/organization/os/${orgId}/workflows`),
  createWorkflow: (orgId: string, data: GenericParams) =>
    apiClient.post(
      `/v3/organization/os/${orgId}/workflows`,
      null,
      { params: data }
    ),
  executeWorkflow: (workflowId: string) =>
    apiClient.post(
      `/v3/organization/workflows/${workflowId}/execute`
    ),
  query: (data: GenericParams) =>
    apiClient.post("/v3/organization/query", data),
};

export const v3CreationApi = {
  startups: () => apiClient.get("/v3/creation/startups"),
  createStartup: (data: GenericParams) =>
    apiClient.post("/v3/creation/startups", data),
  generateBusinessPlan: (startupId: string) =>
    apiClient.post(
      `/v3/creation/startups/${startupId}/business-plan`
    ),
  generateProduct: (startupId: string, data: GenericParams) =>
    apiClient.post(
      `/v3/creation/startups/${startupId}/products`,
      null,
      { params: data }
    ),
  createIdea: (data: GenericParams) =>
    apiClient.post("/v3/creation/ideas", null, { params: data }),
  validateIdea: (ideaId: string) =>
    apiClient.post(`/v3/creation/ideas/${ideaId}/validate`),
  designs: (assetType?: string) =>
    apiClient.get("/v3/creation/designs", {
      params: assetType ? { asset_type: assetType } : {},
    }),
  generateDesign: (data: GenericParams) =>
    apiClient.post("/v3/creation/designs", data),
};

export const v3CollaborationApi = {
  analyzeMeeting: (data: GenericParams) =>
    apiClient.post("/v3/collaboration/meetings/analyze", data),
  meetings: () => apiClient.get("/v3/collaboration/meetings"),
  generateCommunication: (data: GenericParams) =>
    apiClient.post("/v3/collaboration/communications", null, {
      params: data,
    }),
  communications: (commType?: string) =>
    apiClient.get("/v3/collaboration/communications", {
      params: commType ? { communication_type: commType } : {},
    }),
  learningPaths: () => apiClient.get("/v3/collaboration/learning"),
  createLearningPath: (data: GenericParams) =>
    apiClient.post("/v3/collaboration/learning", null, { params: data }),
  devices: (deviceType?: string) =>
    apiClient.get("/v3/collaboration/devices", {
      params: deviceType ? { device_type: deviceType } : {},
    }),
  registerDevice: (data: GenericParams) =>
    apiClient.post("/v3/collaboration/devices", null, { params: data }),
  recordTelemetry: (deviceId: string, data: GenericParams) =>
    apiClient.post(
      `/v3/collaboration/devices/${deviceId}/telemetry`,
      null,
      { params: data }
    ),
};

export const industryApi = {
  list: () => apiClient.get("/industry"),
  get: (slug: string) => apiClient.get(`/industry/${slug}`),
  query: (data: GenericParams) =>
    apiClient.post("/industry/query", data),
  dashboard: (slug: string) =>
    apiClient.get(`/industry/${slug}/dashboard`),
  packages: (slug: string) =>
    apiClient.get(`/industry/${slug}/packages`),
  createPackage: (slug: string, data: GenericParams) =>
    apiClient.post(`/industry/${slug}/packages`, null, { params: data }),
  installPackage: (pkgId: string) =>
    apiClient.post(`/industry/packages/${pkgId}/install`),
  uninstallPackage: (pkgId: string) =>
    apiClient.post(`/industry/packages/${pkgId}/uninstall`),
  knowledge: (slug: string, category?: string) =>
    apiClient.get(`/industry/${slug}/knowledge`, {
      params: category ? { category } : {},
    }),
  addKnowledge: (slug: string, data: GenericParams) =>
    apiClient.post(`/industry/${slug}/knowledge`, data),
  deleteKnowledge: (id: string) =>
    apiClient.delete(`/industry/knowledge/${id}`),
  agents: (slug: string, agentType?: string) =>
    apiClient.get(`/industry/${slug}/agents`, {
      params: agentType ? { agent_type: agentType } : {},
    }),
  createAgent: (slug: string, data: GenericParams) =>
    apiClient.post(`/industry/${slug}/agents`, data),
  chatWithAgent: (slug: string, agentSlug: string, query: string) =>
    apiClient.post(
      `/industry/${slug}/agents/${agentSlug}/chat`,
      null,
      { params: { query } }
    ),
  workflows: (slug: string, workflowType?: string) =>
    apiClient.get(`/industry/${slug}/workflows`, {
      params: workflowType ? { workflow_type: workflowType } : {},
    }),
  createWorkflow: (slug: string, data: GenericParams) =>
    apiClient.post(`/industry/${slug}/workflows`, data),
  templates: (slug: string, templateType?: string) =>
    apiClient.get(`/industry/${slug}/templates`, {
      params: templateType ? { template_type: templateType } : {},
    }),
  createTemplate: (slug: string, data: GenericParams) =>
    apiClient.post(`/industry/${slug}/templates`, data),
  generateFromTemplate: (
    slug: string,
    templateType: string,
    params: GenericParams
  ) =>
    apiClient.post(
      `/industry/${slug}/templates/generate`,
      null,
      {
        params: { template_type: templateType },
        data: params,
      } as unknown as GenericParams
    ),
  compliance: (slug: string, ruleType?: string) =>
    apiClient.get(`/industry/${slug}/compliance`, {
      params: ruleType ? { rule_type: ruleType } : {},
    }),
  createComplianceRule: (slug: string, data: GenericParams) =>
    apiClient.post(`/industry/${slug}/compliance`, data),
  checkCompliance: (slug: string, data: GenericParams) =>
    apiClient.post(`/industry/${slug}/compliance/check`, data),
  analytics: (slug: string, period?: string) =>
    apiClient.get(`/industry/${slug}/analytics`, {
      params: { period: period || "monthly" },
    }),
  seed: () => apiClient.post("/industry/seed"),
};

// Remaining large APIs keep same signatures but using GenericParams for brevity
export const v4CloudApi = {
  createEnvironment: (data: GenericParams) =>
    apiClient.post("/v4/cloud/environments", null, { params: data }),
  listEnvironments: (orgId: string) =>
    apiClient.get("/v4/cloud/environments", {
      params: { organization_id: orgId },
    }),
  getEnvironment: (envId: string) =>
    apiClient.get(`/v4/cloud/environments/${envId}`),
  updateEnvironment: (envId: string, data: GenericParams) =>
    apiClient.patch(`/v4/cloud/environments/${envId}`, null, {
      params: data,
    }),
  deleteEnvironment: (envId: string) =>
    apiClient.delete(`/v4/cloud/environments/${envId}`),
  createDeployment: (tenantId: string, data: GenericParams) =>
    apiClient.post(
      `/v4/cloud/environments/${tenantId}/deployments`,
      null,
      { params: data }
    ),
  listDeployments: (tenantId: string) =>
    apiClient.get(`/v4/cloud/environments/${tenantId}/deployments`),
  createBackup: (tenantId: string, data?: GenericParams) =>
    apiClient.post(
      `/v4/cloud/environments/${tenantId}/backups`,
      null,
      { params: data }
    ),
  listBackups: (tenantId: string) =>
    apiClient.get(`/v4/cloud/environments/${tenantId}/backups`),
  createDrPlan: (tenantId: string, data: GenericParams) =>
    apiClient.post(
      `/v4/cloud/environments/${tenantId}/dr-plans`,
      null,
      { params: data }
    ),
  listDrPlans: (tenantId: string) =>
    apiClient.get(`/v4/cloud/environments/${tenantId}/dr-plans`),
  recordMetric: (tenantId: string, data: GenericParams) =>
    apiClient.post(
      `/v4/cloud/environments/${tenantId}/metrics`,
      null,
      { params: data }
    ),
  getMetrics: (tenantId: string, metricName?: string) =>
    apiClient.get(
      `/v4/cloud/environments/${tenantId}/metrics`,
      { params: metricName ? { metric_name: metricName } : {} }
    ),
  createAppCategory: (data: GenericParams) =>
    apiClient.post("/v4/cloud/apps/categories", null, { params: data }),
  listAppCategories: () => apiClient.get("/v4/cloud/apps/categories"),
  createAppListing: (data: GenericParams) =>
    apiClient.post("/v4/cloud/apps/listings", null, { params: data }),
  listApps: (categoryId?: string) =>
    apiClient.get("/v4/cloud/apps/listings", {
      params: categoryId ? { category_id: categoryId } : {},
    }),
  searchApps: (query: string) =>
    apiClient.get("/v4/cloud/apps/listings/search", {
      params: { query },
    }),
  installApp: (data: GenericParams) =>
    apiClient.post("/v4/cloud/apps/install", null, { params: data }),
  listInstallations: (orgId: string) =>
    apiClient.get("/v4/cloud/apps/installations", {
      params: { organization_id: orgId },
    }),
  purchaseApp: (data: GenericParams) =>
    apiClient.post("/v4/cloud/apps/purchase", null, { params: data }),
  createWorkflowTemplate: (data: GenericParams) =>
    apiClient.post("/v4/cloud/workflows/templates", null, { params: data }),
  listWorkflowTemplates: (category?: string) =>
    apiClient.get("/v4/cloud/workflows/templates", {
      params: category ? { category } : {},
    }),
  installWorkflow: (data: GenericParams) =>
    apiClient.post("/v4/cloud/workflows/install", null, { params: data }),
  listWorkflowInstallations: (orgId: string) =>
    apiClient.get("/v4/cloud/workflows/installations", {
      params: { organization_id: orgId },
    }),
};

export const v4EnterpriseApi = {
  createConnector: (data: GenericParams) =>
    apiClient.post("/v4/enterprise/knowledge/connectors", null, {
      params: data,
    }),
  listConnectors: (orgId: string) =>
    apiClient.get("/v4/enterprise/knowledge/connectors", {
      params: { organization_id: orgId },
    }),
  syncConnector: (connId: string) =>
    apiClient.post(
      `/v4/enterprise/knowledge/connectors/${connId}/sync`
    ),
  searchKnowledge: (data: GenericParams) =>
    apiClient.post("/v4/enterprise/knowledge/search", data),
  createPolicy: (data: GenericParams) =>
    apiClient.post("/v4/enterprise/governance/policies", null, {
      params: data,
    }),
  listPolicies: (orgId: string) =>
    apiClient.get("/v4/enterprise/governance/policies", {
      params: { organization_id: orgId },
    }),
  checkPolicy: (data: GenericParams) =>
    apiClient.post("/v4/enterprise/governance/check", data),
  createApprovalRequest: (data: GenericParams) =>
    apiClient.post("/v4/enterprise/governance/approvals", null, {
      params: data,
    }),
  reviewApproval: (reqId: string, data: GenericParams) =>
    apiClient.patch(
      `/v4/enterprise/governance/approvals/${reqId}`,
      null,
      { params: data }
    ),
  recordMonitoringEvent: (data: GenericParams) =>
    apiClient.post("/v4/enterprise/observability/events", null, {
      params: data,
    }),
  getMonitoringEvents: (orgId: string, eventType?: string) =>
    apiClient.get("/v4/enterprise/observability/events", {
      params: { organization_id: orgId, event_type: eventType },
    }),
  createObservabilityDashboard: (data: GenericParams) =>
    apiClient.post("/v4/enterprise/observability/dashboards", null, {
      params: data,
    }),
  listObservabilityDashboards: (orgId: string, dashType?: string) =>
    apiClient.get("/v4/enterprise/observability/dashboards", {
      params: { organization_id: orgId, dashboard_type: dashType },
    }),
  recordAnalytics: (data: GenericParams) =>
    apiClient.post("/v4/enterprise/analytics/records", null, {
      params: data,
    }),
  getAnalytics: (orgId: string, category?: string, period?: string) =>
    apiClient.get("/v4/enterprise/analytics/records", {
      params: {
        organization_id: orgId,
        metric_category: category,
        period,
      },
    }),
};

export const v4EcosystemApi = {
  createIntegration: (data: GenericParams) =>
    apiClient.post("/v4/ecosystem/integrations", null, { params: data }),
  listIntegrations: (orgId: string, intType?: string) =>
    apiClient.get("/v4/ecosystem/integrations", {
      params: { organization_id: orgId, integration_type: intType },
    }),
  syncIntegration: (intId: string) =>
    apiClient.post(`/v4/ecosystem/integrations/${intId}/sync`),
  getSyncHistory: (intId: string) =>
    apiClient.get(`/v4/ecosystem/integrations/${intId}/sync-history`),
  createAppDefinition: (data: GenericParams) =>
    apiClient.post("/v4/ecosystem/builder/apps", null, { params: data }),
  listAppDefinitions: (orgId: string) =>
    apiClient.get("/v4/ecosystem/builder/apps", {
      params: { organization_id: orgId },
    }),
  generateFromPrompt: (appId: string) =>
    apiClient.post(
      `/v4/ecosystem/builder/apps/${appId}/generate`
    ),
  addComponent: (appId: string, data: GenericParams) =>
    apiClient.post(
      `/v4/ecosystem/builder/apps/${appId}/components`,
      null,
      { params: data }
    ),
  publishApp: (appId: string) =>
    apiClient.post(
      `/v4/ecosystem/builder/apps/${appId}/publish`
    ),
  registerModel: (data: GenericParams) =>
    apiClient.post("/v4/ecosystem/models/register", null, { params: data }),
  listRegisteredModels: (orgId: string) =>
    apiClient.get("/v4/ecosystem/models/registered", {
      params: { organization_id: orgId },
    }),
  listSdks: (lang?: string) =>
    apiClient.get("/v4/ecosystem/sdks", {
      params: lang ? { language: lang } : {},
    }),
  createPlugin: (data: GenericParams) =>
    apiClient.post("/v4/ecosystem/plugins", null, { params: data }),
  listPlugins: (pluginType?: string) =>
    apiClient.get("/v4/ecosystem/plugins", {
      params: pluginType ? { plugin_type: pluginType } : {},
    }),
};

export const businessApi = {
  query: (data: GenericParams) => apiClient.post("/business/query", data),
  generateReport: (params: GenericParams) =>
    apiClient.post("/business/reports/generate", null, { params }),
  reports: (params: GenericParams) =>
    apiClient.get("/business/reports", { params }),
  metrics: (params: GenericParams) =>
    apiClient.get("/business/metrics", { params }),
  createMetric: (params: GenericParams) =>
    apiClient.post("/business/metrics", null, { params }),
  dashboard: (orgId: string) =>
    apiClient.get(`/business/dashboard/${orgId}`),
  createApproval: (data: GenericParams) =>
    apiClient.post("/business/approvals", data),
  pendingApprovals: (orgId: string) =>
    apiClient.get("/business/approvals/pending", {
      params: { organization_id: orgId },
    }),
  approveRequest: (id: string, notes?: string) =>
    apiClient.post(`/business/approvals/${id}/approve`, null, {
      params: { notes },
    }),
  rejectRequest: (id: string, reason: string) =>
    apiClient.post(`/business/approvals/${id}/reject`, null, {
      params: { reason },
    }),
  recordTransaction: (data: GenericParams) =>
    apiClient.post("/business/financial/records", data),
  financialSummary: (orgId: string, months?: number) =>
    apiClient.get(`/business/financial/summary/${orgId}`, {
      params: { months },
    }),
  financialForecast: (orgId: string, months?: number) =>
    apiClient.post(
      `/business/financial/forecast/${orgId}`,
      null,
      { params: { months } }
    ),
  createWorkflow: (data: GenericParams) =>
    apiClient.post("/business/workflows", data),
  workflows: (orgId: string) =>
    apiClient.get("/business/workflows", {
      params: { organization_id: orgId },
    }),
  executeWorkflow: (id: string, orgId: string) =>
    apiClient.post(`/business/workflows/${id}/execute`, null, {
      params: { organization_id: orgId },
    }),
  addKnowledge: (data: GenericParams) =>
    apiClient.post("/business/knowledge", data),
  queryKnowledge: (orgId: string, query: string) =>
    apiClient.get("/business/knowledge/query", {
      params: { organization_id: orgId, query },
    }),
  listKnowledge: (orgId: string) =>
    apiClient.get("/business/knowledge", {
      params: { organization_id: orgId },
    }),
  deleteKnowledge: (id: string) =>
    apiClient.delete(`/business/knowledge/${id}`),
  alerts: (orgId: string) =>
    apiClient.get("/business/alerts", {
      params: { organization_id: orgId },
    }),
};

// Re-export lightweight versions of remaining large API objects using GenericParams
export const v5SimulationApi = {
  createScenario: (data: GenericParams) =>
    apiClient.post("/v5/simulation/scenarios", data),
  listScenarios: (scenarioType?: string) =>
    apiClient.get("/v5/simulation/scenarios", {
      params: scenarioType ? { scenario_type: scenarioType } : {},
    }),
  runSimulation: (data: GenericParams) =>
    apiClient.post("/v5/simulation/simulations/run", data),
  listSimulations: () => apiClient.get("/v5/simulation/simulations"),
  getSimulationResults: (id: string) =>
    apiClient.get(`/v5/simulation/simulations/${id}/results`),
};

export const v5CollaborationApi = {
  createSession: (data: GenericParams) =>
    apiClient.post("/v5/collaboration/sessions", data),
  listSessions: (sessionType?: string, status?: string) =>
    apiClient.get("/v5/collaboration/sessions", {
      params: { session_type: sessionType, status },
    }),
  getSession: (id: string) =>
    apiClient.get(`/v5/collaboration/sessions/${id}`),
};

export const v5ConnectorApi = {
  listDefinitions: (category?: string, connectorType?: string) =>
    apiClient.get("/v5/connector/definitions", {
      params: { category, connector_type: connectorType },
    }),
  listIntegrations: () => apiClient.get("/v5/connector/integrations"),
  getDashboard: () => apiClient.get("/v5/connector/dashboard"),
};

export const v5ComplianceApi = {
  listPolicies: (policyType?: string) =>
    apiClient.get("/v5/compliance/policies", {
      params: policyType ? { policy_type: policyType } : {},
    }),
  getComplianceDashboard: () =>
    apiClient.get("/v5/compliance/dashboard"),
};

export const v5CopilotApi = {
  listConfigs: (industry?: string) =>
    apiClient.get("/v5/copilot/configs", {
      params: industry ? { industry } : {},
    }),
  chat: (data: GenericParams) =>
    apiClient.post("/v5/copilot/chat", data),
};

export const v5KnowledgeApi = {
  listConnectors: () => apiClient.get("/v5/knowledge/connectors"),
  search: (data: GenericParams) =>
    apiClient.post("/v5/knowledge/search", data),
};

export const v6GovernanceApi = {
  listPrompts: (params?: GenericParams) =>
    apiClient.get("/v6/governance/prompts", { params }),
  dashboard: () => apiClient.get("/v6/governance/dashboard"),
};

// ─── Active AI Agents (NEW) ──────────────────────────────────────────────────
export const activeAgentsApi = {
  list: (params?: { organization_id?: string; active_only?: boolean; status?: string }) =>
    apiClient.get("/active-agents", { params }),
  stats: (organization_id?: string) =>
    apiClient.get("/active-agents/stats", { params: { organization_id } }),
  templates: (category?: string, include_system?: boolean) =>
    apiClient.get("/active-agents/templates", { params: { category, include_system } }),
  getTemplate: (id: string) => apiClient.get(`/active-agents/templates/${id}`),
  get: (id: string) => apiClient.get(`/active-agents/${id}`),
  create: (data: { agent_id: string; name?: string; mode?: string; organization_id?: string; config?: Record<string, unknown>; cron_schedule?: string }) =>
    apiClient.post("/active-agents", data),
  createFromTemplate: (templateId: string, params?: { agent_id?: string; name?: string }) =>
    apiClient.post(`/active-agents/from-template/${templateId}`, null, { params }),
  update: (id: string, data: Record<string, unknown>) =>
    apiClient.patch(`/active-agents/${id}`, data),
  start: (id: string) => apiClient.post(`/active-agents/${id}/start`),
  stop: (id: string) => apiClient.post(`/active-agents/${id}/stop`),
  pause: (id: string) => apiClient.post(`/active-agents/${id}/pause`),
  resume: (id: string) => apiClient.post(`/active-agents/${id}/resume`),
  heartbeat: (id: string, message?: string) =>
    apiClient.post(`/active-agents/${id}/heartbeat`, null, { params: { message } }),
  assignTask: (id: string, data: { title: string; description?: string; priority?: number; input_data?: Record<string, unknown> }) =>
    apiClient.post(`/active-agents/${id}/tasks`, data),
  logs: (id: string, params?: { limit?: number; level?: string; event_type?: string }) =>
    apiClient.get(`/active-agents/${id}/logs`, { params }),
  delete: (id: string) => apiClient.delete(`/active-agents/${id}`),
  // Goals
  createGoal: (id: string, data: { title: string; description?: string; priority?: number; success_criteria?: Record<string, unknown>; deadline_at?: string }) =>
    apiClient.post(`/active-agents/${id}/goals`, data),
  listGoals: (id: string) => apiClient.get(`/active-agents/${id}/goals`),
  // Memory
  addMemory: (id: string, data: { key: string; content: string; memory_type?: string; importance?: number }) =>
    apiClient.post(`/active-agents/${id}/memory`, data),
  listMemory: (id: string, limit?: number) => apiClient.get(`/active-agents/${id}/memory`, { params: { limit } }),
};

// ─── Prebuilt Active Agent Templates ───────────────────────────────────────
export const ACTIVE_AGENT_TEMPLATES = [
  {
    id: "research-assistant",
    name: "Research Assistant",
    description: "Autonomous web research, summarization, and report generation 24/7",
    icon: "🔍",
    category: "research",
    defaultMode: "continuous" as const,
    isSystem: false,
  },
  {
    id: "code-reviewer",
    name: "Code Reviewer",
    description: "Watches GitHub repos and auto-reviews PRs for bugs, security, and style",
    icon: "👨‍💻",
    category: "engineering",
    defaultMode: "event_driven" as const,
    isSystem: false,
  },
  {
    id: "customer-support",
    name: "Customer Support Agent",
    description: "Handles support tickets 24/7, knowledge base lookup, empathy-driven",
    icon: "💬",
    category: "support",
    defaultMode: "continuous" as const,
    isSystem: false,
  },
  {
    id: "data-monitor",
    name: "Data Monitor",
    description: "Monitors KPIs, detects anomalies, creates charts and alerts",
    icon: "📊",
    category: "analytics",
    defaultMode: "scheduled" as const,
    isSystem: false,
  },
  {
    id: "content-creator",
    name: "Content Creator",
    description: "Generates blogs, social posts, marketing copy, SEO optimized",
    icon: "✍️",
    category: "marketing",
    defaultMode: "on_demand" as const,
    isSystem: false,
  },
  {
    id: "sales-assistant",
    name: "Sales Assistant",
    description: "Qualifies leads, drafts personalized outreach, updates CRM automatically",
    icon: "💼",
    category: "sales",
    defaultMode: "continuous" as const,
    isSystem: false,
  },
  {
    id: "devops-helper",
    name: "DevOps Helper",
    description: "Monitors deployments, analyzes logs, suggests fixes, auto-remediates",
    icon: "🚀",
    category: "engineering",
    defaultMode: "continuous" as const,
    isSystem: false,
  },
  {
    id: "personal-assistant",
    name: "Personal Assistant",
    description: "Manages calendar, emails, tasks, reminders – your second brain",
    icon: "🤖",
    category: "personal",
    defaultMode: "continuous" as const,
    isSystem: false,
  },
  {
    id: "security-guard",
    name: "Security Guardian",
    description: "Continuously scans for vulnerabilities, secrets, compliance issues",
    icon: "🛡️",
    category: "security",
    defaultMode: "scheduled" as const,
    isSystem: false,
  },
  {
    id: "finance-analyst",
    name: "Finance Analyst",
    description: "Tracks expenses, forecasts cash flow, budget alerts",
    icon: "💰",
    category: "finance",
    defaultMode: "scheduled" as const,
    isSystem: false,
  },
  {
    id: "legal-assistant",
    name: "Legal Assistant",
    description: "Reviews contracts, flags risks, summarizes legal docs, compliance checks",
    icon: "⚖️",
    category: "legal",
    defaultMode: "on_demand" as const,
    isSystem: false,
  },
  {
    id: "hr-recruiter",
    name: "HR Recruiter",
    description: "Screens resumes, ranks candidates, drafts outreach, schedules interviews",
    icon: "👥",
    category: "hr",
    defaultMode: "continuous" as const,
    isSystem: false,
  },
  {
    id: "market-researcher",
    name: "Market Researcher",
    description: "Deep market analysis, competitor tracking, TAM/SAM, trend reports",
    icon: "📈",
    category: "research",
    defaultMode: "scheduled" as const,
    isSystem: false,
  },
  {
    id: "social-media-manager",
    name: "Social Media Manager",
    description: "Schedules posts, monitors mentions, engages, grows audience",
    icon: "📱",
    category: "marketing",
    defaultMode: "scheduled" as const,
    isSystem: false,
  },
  {
    id: "seo-optimizer",
    name: "SEO Optimizer",
    description: "Audits SEO, suggests keywords, optimizes content, tracks rankings",
    icon: "🔎",
    category: "marketing",
    defaultMode: "scheduled" as const,
    isSystem: false,
  },
  {
    id: "product-manager",
    name: "Product Manager",
    description: "Writes PRDs, prioritizes backlog, tracks metrics, stakeholder updates",
    icon: "📦",
    category: "product",
    defaultMode: "continuous" as const,
    isSystem: false,
  },
  {
    id: "qa-tester",
    name: "QA Tester",
    description: "Auto-generates test cases, runs tests, reports bugs, tracks coverage",
    icon: "🧪",
    category: "engineering",
    defaultMode: "event_driven" as const,
    isSystem: false,
  },
  {
    id: "translation-agent",
    name: "Translation Agent",
    description: "Translates docs, preserves tone, glossary-aware, 50+ languages",
    icon: "🌐",
    category: "localization",
    defaultMode: "on_demand" as const,
    isSystem: false,
  },
  {
    id: "meeting-summarizer",
    name: "Meeting Summarizer",
    description: "Joins meetings, transcribes, extracts action items, decisions, follow-ups",
    icon: "📝",
    category: "productivity",
    defaultMode: "event_driven" as const,
    isSystem: false,
  },
  {
    id: "onboarding-coach",
    name: "Onboarding Coach",
    description: "Guides new users, tracks progress, personalized tours, reduces churn",
    icon: "🎓",
    category: "customer_success",
    defaultMode: "event_driven" as const,
    isSystem: false,
  },
  {
    id: "inventory-manager",
    name: "Inventory Manager",
    description: "Tracks stock, predicts demand, auto-reorders, supplier coordination",
    icon: "📦",
    category: "operations",
    defaultMode: "scheduled" as const,
    isSystem: false,
  },
  {
    id: "compliance-officer",
    name: "Compliance Officer",
    description: "Monitors regulatory changes, audits processes, generates compliance reports",
    icon: "📋",
    category: "compliance",
    defaultMode: "scheduled" as const,
    isSystem: false,
  },
  {
    id: "risk-analyst",
    name: "Risk Analyst",
    description: "Identifies risks, quantifies impact, proposes mitigations, risk matrix",
    icon: "⚠️",
    category: "risk",
    defaultMode: "scheduled" as const,
    isSystem: false,
  },
  {
    id: "platform-monitor",
    name: "Platform Monitor (System)",
    description: "System-level: monitors API health, DB, Redis, queues, auto-heals",
    icon: "🖥️",
    category: "system",
    defaultMode: "continuous" as const,
    isSystem: true,
  },
  {
    id: "backup-manager",
    name: "Backup Manager (System)",
    description: "System-level: ensures backups, tests restores, retention policy",
    icon: "💾",
    category: "system",
    defaultMode: "scheduled" as const,
    isSystem: true,
  }
] as const;

