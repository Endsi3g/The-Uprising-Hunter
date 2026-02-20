import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
    console.warn(
        "⚠️ Supabase environment variables are missing. Local dashboard may not function correctly.",
    );
    console.info(
        'Run "scripts/setup-env.ps1" or set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY',
    );
}

// Provide fallback to prevent crash, but client will fail gracefully on requests
export const supabase = createClient(
    supabaseUrl || "http://localhost:54321",
    supabaseAnonKey || "missing-key",
);
