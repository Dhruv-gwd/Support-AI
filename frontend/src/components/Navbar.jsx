import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { user, logout } = useAuth();
  const isAdmin = user?.role === "admin";

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-14 items-center">
          <Link to="/" className="text-xl font-bold text-indigo-600">
            SupportAI
          </Link>
          <div className="flex items-center gap-6 text-sm font-medium">
            <Link to="/" className="text-gray-700 hover:text-indigo-600 transition">
              Chat
            </Link>
            {isAdmin && (
              <Link to="/admin" className="text-gray-700 hover:text-indigo-600 transition">
                Admin
              </Link>
            )}
            {user && (
              <>
                <span className="text-gray-500">{user.full_name || user.email}</span>
                <button onClick={logout} className="text-red-600 hover:text-red-700 transition">
                  Logout
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
