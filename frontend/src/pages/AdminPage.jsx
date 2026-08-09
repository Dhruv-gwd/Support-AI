import { useCallback, useRef, useState } from "react";
import { useDocs } from "../context/DocsContext";
import Navbar from "../components/Navbar";

const NAV_ITEMS = [
  { id: "dashboard", label: "Dashboard", icon: "📊" },
  { id: "documents", label: "Documents", icon: "📁" },
  { id: "users", label: "Users", icon: "👥" },
  { id: "settings", label: "Settings", icon: "⚙️" },
];

export default function AdminPage() {
  const { sources, loading, error, refresh, handleUpload, uploading, handleDelete } = useDocs();
  const [activeTab, setActiveTab] = useState("dashboard");
  const fileRef = useRef(null);

  const onFileChange = useCallback(async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      await handleUpload(file);
    } finally {
      e.target.value = "";
    }
  }, [handleUpload]);

  const documentCount = sources.length;
  const userCount = typeof sources !== "undefined" ? 1 : 0;

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="flex">
        <aside className="w-64 bg-white border-r border-gray-200 min-h-[calc(100vh-3.5rem)] sticky top-14">
          <div className="p-4">
            <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
              Administration
            </h2>
            <nav className="space-y-1">
              {NAV_ITEMS.map((item) => (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition ${
                    activeTab === item.id
                      ? "bg-indigo-50 text-indigo-700"
                      : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                  }`}
                >
                  <span>{item.icon}</span>
                  {item.label}
                </button>
              ))}
            </nav>
          </div>
        </aside>

        <main className="flex-1 p-8">
          {activeTab === "dashboard" && (
            <div>
              <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="bg-white rounded-xl border border-gray-200 p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-500 mb-1">Total Documents</p>
                      <p className="text-3xl font-bold text-gray-900">{documentCount}</p>
                    </div>
                    <div className="w-12 h-12 bg-indigo-50 rounded-lg flex items-center justify-center text-2xl">
                      📁
                    </div>
                  </div>
                </div>

                <div className="bg-white rounded-xl border border-gray-200 p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-500 mb-1">Storage Used</p>
                      <p className="text-3xl font-bold text-gray-900">--</p>
                    </div>
                    <div className="w-12 h-12 bg-green-50 rounded-lg flex items-center justify-center text-2xl">
                      💾
                    </div>
                  </div>
                </div>

                <div className="bg-white rounded-xl border border-gray-200 p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-500 mb-1">Status</p>
                      <p className="text-lg font-semibold text-green-600">Online</p>
                    </div>
                    <div className="w-12 h-12 bg-green-50 rounded-lg flex items-center justify-center text-2xl">
                      ✅
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
                <div className="flex gap-3">
                  <button
                    onClick={() => setActiveTab("documents")}
                    className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition"
                  >
                    Upload Document
                  </button>
                  <button
                    onClick={refresh}
                    className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50 transition"
                  >
                    Refresh Data
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === "documents" && (
            <div>
              <h1 className="text-2xl font-bold text-gray-900 mb-6">Documents</h1>

              {error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
                  {error}
                </div>
              )}

              <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
                <h2 className="text-lg font-semibold mb-4">Upload Document</h2>
                <p className="text-sm text-gray-500 mb-4">
                  Supported formats: PDF, DOCX, TXT, CSV, Excel, Markdown, HTML, PNG, JPG, GIF
                </p>
                <input
                  ref={fileRef}
                  type="file"
                  accept=".pdf,.docx,.txt,.csv,.xlsx,.xls,.md,.html,.png,.jpg,.jpeg,.gif,.bmp,.webp"
                  onChange={onFileChange}
                  className="block w-full text-sm text-gray-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
                  disabled={uploading}
                />
                {uploading && <p className="mt-2 text-sm text-gray-500">Uploading and processing...</p>}
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold">All Documents</h2>
                  <button
                    onClick={refresh}
                    className="text-sm text-indigo-600 hover:text-indigo-700 font-medium"
                    disabled={loading}
                  >
                    Refresh
                  </button>
                </div>

                {loading && sources.length === 0 ? (
                  <p className="text-gray-500 text-sm">Loading documents...</p>
                ) : sources.length === 0 ? (
                  <p className="text-gray-500 text-sm">No documents uploaded yet.</p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                      <thead>
                        <tr className="border-b border-gray-200">
                          <th className="py-3 px-4 font-medium text-gray-500">Name</th>
                          <th className="py-3 px-4 font-medium text-gray-500">Type</th>
                          <th className="py-3 px-4 font-medium text-gray-500 text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {sources.map((src) => (
                          <tr key={src} className="hover:bg-gray-50">
                            <td className="py-3 px-4">
                              <div className="flex items-center gap-3">
                                <span className="text-gray-400">
                                  {src.match(/\.(png|jpg|jpeg|gif|bmp|webp)$/i) ? "🖼️" : "📄"}
                                </span>
                                <span className="font-medium text-gray-700">{src}</span>
                              </div>
                            </td>
                            <td className="py-3 px-4 text-gray-500">
                              {src.split(".").pop()?.toUpperCase()}
                            </td>
                            <td className="py-3 px-4 text-right">
                              <button
                                onClick={() => handleDelete(src)}
                                className="text-sm text-red-600 hover:text-red-700 font-medium"
                                disabled={loading}
                              >
                                Delete
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === "users" && (
            <div>
              <h1 className="text-2xl font-bold text-gray-900 mb-6">Users</h1>
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <p className="text-gray-500 text-sm">User management coming soon.</p>
              </div>
            </div>
          )}

          {activeTab === "settings" && (
            <div>
              <h1 className="text-2xl font-bold text-gray-900 mb-6">Settings</h1>
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <p className="text-gray-500 text-sm">Company settings and preferences coming soon.</p>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
