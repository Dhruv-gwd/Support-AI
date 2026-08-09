import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export const api = axios.create({
  baseURL: `${API_BASE}/api`,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("supportai_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("supportai_token");
      delete api.defaults.headers.common.Authorization;
    }
    return Promise.reject(error);
  }
);

export const sendMessage = async (message, conversationId = null) => {
  const { data } = await api.post("/chat", { message, conversation_id: conversationId });
  return data;
};

export const uploadDocument = async (file) => {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post("/documents/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
};

export const listDocuments = async () => {
  const { data } = await api.get("/documents");
  return data.sources;
};

export const deleteDocument = async (filename) => {
  const { data } = await api.delete(`/documents/${encodeURIComponent(filename)}`);
  return data;
};

export const register = async (email, password, fullName) => {
  const { data } = await api.post("/auth/register", { email, password, full_name: fullName });
  return data;
};

export const login = async (email, password) => {
  const { data } = await api.post("/auth/login", { email, password });
  return data;
};

export const getCurrentUser = async () => {
  const { data } = await api.get("/auth/me");
  return data;
};

export const getConversations = async () => {
  const { data } = await api.get("/auth/conversations");
  return data;
};

export const createConversation = async () => {
  const { data } = await api.post("/auth/conversations");
  return data;
};

export const getMessages = async (conversationId) => {
  const { data } = await api.get(`/auth/conversations/${conversationId}/messages`);
  return data;
};

export const deleteConversation = async (conversationId) => {
  const { data } = await api.delete(`/auth/conversations/${conversationId}`);
  return data;
};
