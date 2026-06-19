import { supabase } from "../api/supabase";
 
export default function Login() {
  const handleLogin = async () => {
    await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: "http://localhost:5173" }
    });
  };
 
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white p-10 rounded-xl shadow-sm border border-gray-200 text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Matchmatic</h1>
        <p className="text-gray-500 mb-8">AI-powered job application automation</p>
        <button
          onClick={handleLogin}
          className="bg-blue-600 text-white px-8 py-3 rounded-lg font-medium hover:bg-blue-700"
        >
          Sign in with Google
        </button>
      </div>
    </div>
  );
}