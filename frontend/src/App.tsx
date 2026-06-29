import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Navbar from "./components/Navbar";
import Jobs from "./pages/Jobs";
import Tracker from "./pages/Tracker";
import Settings from "./pages/Settings";
import ResumeReview from "./pages/ResumeReview";
import Login from "./pages/Login";
import { useAuth } from "./hooks/useAuth";
import { Toaster } from "react-hot-toast";

export default function App() {
  const { isAuthenticated, loading } = useAuth();
 
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-400">Loading...</p>
      </div>
    );
  }
 
  return (
    <BrowserRouter>
      {isAuthenticated ? (
        <div className="min-h-screen bg-gray-50">
          <Toaster
          position="bottom-right"
          toastOptions={{
            duration: 3000,
            style: { background: "#1e2a3b", color: "#fff", fontSize: "14px" },
            success: { iconTheme: { primary: "#16a34a", secondary: "#fff" } },
            error: { iconTheme: { primary: "#dc2626", secondary: "#fff" } }
            }}
            />
          <Navbar />
          <main className="max-w-7xl mx-auto py-6 px-4">
            <Routes>
              <Route path="/" element={<Jobs />} />
              <Route path="/tracker" element={<Tracker />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/review" element={<ResumeReview />} />
              <Route path="*" element={<Navigate to="/" />} />
            </Routes>
          </main>
        </div>
      ) : (
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="*" element={<Navigate to="/login" />} />
        </Routes>
      )}
    </BrowserRouter>
  );
}
