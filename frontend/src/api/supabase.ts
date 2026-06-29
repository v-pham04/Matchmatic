import { createClient } from "@supabase/supabase-js";

export const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY,
  {
    auth: {
      // Exchange is handled explicitly in useAuth to avoid races with onAuthStateChange
      detectSessionInUrl: false,
      persistSession: true,
      flowType: "pkce",
    },
  },
);