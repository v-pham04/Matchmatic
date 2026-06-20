import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
 
const links = [
  { to: "/",        label: "Jobs"     },
  { to: "/tracker", label: "Tracker"  },
  { to: "/settings",label: "Settings" },
];
 
export default function Navbar() {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuth();
 
  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };
 
  return (
    <nav className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
      <div className="flex items-center gap-8">
        <span className="text-xl font-bold text-blue-700">Matchmatic</span>
        <div className="flex gap-6">
          {links.map(link => (
            <Link
              key={link.to}
              to={link.to}
              className={`text-sm font-medium ${ pathname === link.to
                ? "text-blue-700 border-b-2 border-blue-700 pb-1"
                : "text-gray-500 hover:text-gray-900"
              }`}
            >
              {link.label}
            </Link>
          ))}
        </div>
      </div>
      <button
        onClick={handleLogout}
        className="text-sm text-gray-500 hover:text-gray-900"
      >
        Sign out
      </button>
    </nav>
  );
}
