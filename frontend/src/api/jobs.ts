import client from "./client";
import type { JobListing } from "../types";
 
export async function fetchJobs(country?: string, page = 1): Promise<JobListing[]> {
  const params: Record<string, any> = { page, limit: 20 };
  if (country) params.country = country;
 
  const response = await client.get<JobListing[]>("/jobs", { params });
  return response.data;
}
 
export async function fetchJob(jobId: string): Promise<JobListing> {
  const response = await client.get<JobListing>(`/jobs/${jobId}`);
  return response.data;
}
