export type MatchLevel = "HIGH" | "MEDIUM" | "LOW";
export type VisaSignal = "open" | "citizen_only" | "unclear" | null;
export type AppStatus = "applied" | "interview" | "pending" | "closed";
 
export interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  country: string;
  source: string;
  posted_at: string;
  url: string;
}
 
export interface JobAnalysis {
  id: string;
  job_id: string;
  ats_score: number;
  match_level: MatchLevel;
  matching_skills: string[];
  missing_skills: string[];
  experience_match: "strong" | "partial" | "weak" | null;
  visa_compatible: boolean | null;
  visa_signal: VisaSignal;
  visa_evidence: string | null;
  summary: string | null;
}

export interface JobWithAnalysis extends JobListing {
  analysis?: JobAnalysis;
}
 
export interface User {
  id: string;
  email: string;
  full_name: string;
  target_market: "vietnam" | "us" | "both";
  visa_check_enabled: boolean;
  min_match_score: number;
  job_keywords: string[];
}

export interface JobListing {
  id: string;
  title: string;
  company: string;
  location: string | null;
  country: string | null;
  source: string | null;
  url: string;
  posted_at: string | null;
  scraped_at: string | null;
  is_processed: boolean;
}


