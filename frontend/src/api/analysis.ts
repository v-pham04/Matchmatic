import client from "./client";
import type { JobAnalysis, JobListing } from "../types";
 
// Fetch the AI analysis for a specific job
export async function fetchJobAnalysis(
  jobId: string,
  userId: string
): Promise<JobAnalysis | null> {
  try {
    const res = await client.get<JobAnalysis>(`/jobs/${jobId}/analysis`, {
      params: { user_id: userId },
    });
    return res.data;
  } catch (err: any) {
    // 404 means analysis not done yet — return null, not an error
    if (err.response?.status === 404) return null;
    throw err;
  }
}
 
// Fetch the scored job feed — only jobs above user minimum score (from DB)
export async function fetchJobFeed(
  userId: string,
  options?: { country?: string; matchLevel?: string; page?: number }
): Promise<JobListing[]> {
  const params: Record<string, any> = {
    user_id: userId,
    page: options?.page ?? 1,
    limit: 20,
  };
  if (options?.country) params.country = options.country;
  if (options?.matchLevel) params.match_level = options.matchLevel;

  const res = await client.get<JobListing[]>("/jobs/feed", { params });
  return res.data;
}

export async function dismissJob(jobId: string, userId: string): Promise<void> {
  await client.post(`/jobs/${jobId}/dismiss`, null, {
    params: { user_id: userId },
  });
}

