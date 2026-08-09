import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { listDocuments, deleteDocument, uploadDocument } from "../api/client";

const DocsContext = createContext(null);

export function DocsProvider({ children }) {
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [uploading, setUploading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listDocuments();
      setSources(data);
    } catch (e) {
      setError(e.response?.data?.detail || "Failed to load documents");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  const handleUpload = useCallback(async (file) => {
    setUploading(true);
    setError(null);
    try {
      await uploadDocument(file);
      await refresh();
    } catch (e) {
      setError(e.response?.data?.detail || "Upload failed");
      throw e;
    } finally {
      setUploading(false);
    }
  }, [refresh]);

  const handleDelete = useCallback(async (filename) => {
    setLoading(true);
    setError(null);
    try {
      await deleteDocument(filename);
      await refresh();
    } catch (e) {
      setError(e.response?.data?.detail || "Delete failed");
    } finally {
      setLoading(false);
    }
  }, [refresh]);

  return (
    <DocsContext.Provider value={{ sources, loading, error, refresh, handleUpload, uploading, handleDelete }}>
      {children}
    </DocsContext.Provider>
  );
}

export function useDocs() {
  const ctx = useContext(DocsContext);
  if (!ctx) throw new Error("useDocs must be used within DocsProvider");
  return ctx;
}