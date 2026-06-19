import { BrowserRouter, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Jobs from "./pages/Jobs";
import Tracker from "./pages/Tracker";
import Settings from "./pages/Settings";
import ResumeReview from "./pages/ResumeReview";
import Login from "./pages/Login";
 
export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <main className="max-w-7xl mx-auto py-6 px-4">
          <Routes>
            <Route path="/"          element={<Jobs />} />
            <Route path="/tracker"   element={<Tracker />} />
            <Route path="/settings"  element={<Settings />} />
            <Route path="/review"    element={<ResumeReview />} />
            <Route path="/login"     element={<Login />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}