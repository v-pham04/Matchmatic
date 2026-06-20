// A custom React hook that manages the auth session
import { useEffect, useState } from "react";
import { supabase } from "../api/supabase";
import client from "../api/client";
 
export function useAuth() {
  const [userId, setUserId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
 
  useEffect(() => {
    // Check if there is already a session when the app loads
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session?.user) {
        handleUser(session.user);
      }
      setLoading(false);
    });
 
    // Listen for future login/logout events
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session?.user) {
        handleUser(session.user);
      } else {
        setUserId(null);
      }
    });
 
    return () => subscription.unsubscribe();
  }, []);
 
  async function handleUser(supabaseUser: any) {
    // Create or fetch the user in our own database
    try {
      await client.post("/users/", null, {
        params: {
          email: supabaseUser.email,
          full_name: supabaseUser.user_metadata?.full_name ?? "",
        }
      });
      setUserId(supabaseUser.id);
    } catch (err) {
      console.error("Failed to sync user to backend:", err);
      setUserId(supabaseUser.id); // still set it so the app works
    }
  }
 
  const logout = () => supabase.auth.signOut();
 
  return { userId, loading, logout };
}
