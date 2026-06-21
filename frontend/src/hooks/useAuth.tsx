import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import type { Session } from "@supabase/supabase-js";
import { supabase } from "../api/supabase";
import client from "../api/client";

type AuthContextValue = {
  userId: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

async function syncBackendUser(session: Session): Promise<string> {
  const { data } = await client.post("/users/", null, {
    params: {
      email: session.user.email,
      full_name: session.user.user_metadata?.full_name ?? "",
    },
  });
  return data.id;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [userId, setUserId] = useState<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function applySession(session: Session | null) {
      if (!active) return;

      if (!session?.user) {
        setIsAuthenticated(false);
        setUserId(null);
        return;
      }

      setIsAuthenticated(true);

      try {
        const backendUserId = await syncBackendUser(session);
        if (active) setUserId(backendUserId);
      } catch (err) {
        console.error("Failed to sync user to backend:", err);
        if (active) setUserId(null);
      }
    }

    supabase.auth.getSession().then(async ({ data: { session } }) => {
      await applySession(session);
      if (active) setLoading(false);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (_event, session) => {
      if (!active) return;
      setLoading(true);
      await applySession(session);
      if (active) setLoading(false);
    });

    return () => {
      active = false;
      subscription.unsubscribe();
    };
  }, []);

  const value = useMemo(
    () => ({
      userId,
      isAuthenticated,
      loading,
      logout: async () => {
        await supabase.auth.signOut();
      },
    }),
    [userId, isAuthenticated, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
