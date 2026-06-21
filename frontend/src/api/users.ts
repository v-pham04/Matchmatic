import client from "./client";

export interface UserSettings {
  id: string;
  email: string;
  full_name: string | null;
  target_market: "vietnam" | "us" | "both";
  visa_check_enabled: boolean;
  min_match_score: number;
  job_keywords: string[] | null;
  resume_url: string | null;
}

export interface UserSettingsUpdate {
  target_market?: "vietnam" | "us" | "both";
  visa_check_enabled?: boolean;
  min_match_score?: number;
  job_keywords?: string[];
}

export async function fetchUser(userId: string): Promise<UserSettings> {
  const res = await client.get<UserSettings>(`/users/${userId}`);
  return res.data;
}

export async function updateUserSettings(
  userId: string,
  settings: UserSettingsUpdate
): Promise<UserSettings> {
  const res = await client.patch<UserSettings>(`/users/${userId}/settings`, settings);
  return res.data;
}
