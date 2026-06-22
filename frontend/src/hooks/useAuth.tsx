import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
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
  // Pass the token directly — calling getSession() from inside onAuthStateChange
  // (via the axios interceptor) deadlocks Supabase auth initialization.
  const { data } = await client.post("/users/", null, {
    params: {
      email: session.user.email,
      full_name: session.user.user_metadata?.full_name ?? "",
    },
    headers: {
      Authorization: `Bearer ${session.access_token}`,
    },
  });
  return data.id;
}

function clearOAuthParamsFromUrl(): void {
  const url = new URL(window.location.href);
  if (!url.searchParams.has("code")) return;
  url.searchParams.delete("code");
  const clean = url.pathname + (url.searchParams.toString() ? `?${url.searchParams}` : "");
  window.history.replaceState({}, document.title, clean);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [userId, setUserId] = useState<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const initDoneRef = useRef(false);

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

    async function initAuth() {
      setLoading(true);

      const params = new URLSearchParams(window.location.search);
      const code = params.get("code");

      if (code) {
        const { error } = await supabase.auth.exchangeCodeForSession(code);
        if (error) {
          console.error("OAuth code exchange failed:", error);
        } else {
          clearOAuthParamsFromUrl();
        }
      }

      const { data: { session } } = await supabase.auth.getSession();
      await applySession(session);

      initDoneRef.current = true;
      if (active) setLoading(false);
    }

    initAuth();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (event, session) => {
      // Ignore events fired during init — handling them here while exchangeCodeForSession
      // is in progress causes a getSession() deadlock inside the axios interceptor.
      if (!active || !initDoneRef.current) return;

      if (event === "SIGNED_OUT") {
        setIsAuthenticated(false);
        setUserId(null);
        return;
      }

      if (event === "SIGNED_IN" || event === "TOKEN_REFRESHED") {
        await applySession(session);
      }
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
