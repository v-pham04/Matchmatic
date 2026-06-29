import { useState, useEffect } from "react";
import { fetchJobFeed, fetchJobAnalysis, dismissJob } from "../api/analysis";
import JobCard from "../components/JobCard";
import FilterBar from "../components/FilterBar";
import MatchReportModal from "../components/MatchReportModal";
import type { JobListing, JobAnalysis } from "../types";
import { useAuth } from "../hooks/useAuth";
import toast from "react-hot-toast";

export default function Jobs() {
  const { userId } = useAuth();
  const [jobs, setJobs] = useState<JobListing[]>([]);
  const [analyses, setAnalyses] = useState<Record<string, JobAnalysis>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState({ country: "", matchLevel: "" });
  const [selectedJob, setSelectedJob] = useState<JobListing | null>(null);
  const [modalAnalysis, setModalAnalysis] = useState<JobAnalysis | null>(null);
  const [modalLoading, setModalLoading] = useState(false);
 
  useEffect(() => { loadJobs(); }, [filters, userId]);
 
  async function loadJobs() {
    if (!userId) {
      setJobs([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await fetchJobFeed(userId, {
        country: filters.country || undefined,
        matchLevel: filters.matchLevel || undefined,
      });
      setJobs(data);
      loadAnalyses(data);
    } catch {
      setError("Could not load jobs. Make sure the backend is running.");
    } finally {
      setLoading(false);
    }
  }
 
  // Fetch analyses for all jobs — runs in background after jobs load
  async function loadAnalyses(jobList: JobListing[]) {
    if (!userId) return;
    const results: Record<string, JobAnalysis> = {};
    await Promise.all(
      jobList.map(async (job) => {
        const analysis = await fetchJobAnalysis(job.id, userId);
        if (analysis) results[job.id] = analysis;
      })
    );
    setAnalyses(prev => ({ ...prev, ...results }));
  }
 
  async function handleJobClick(job: JobListing) {
    setSelectedJob(job);
    setModalAnalysis(analyses[job.id] ?? null);
    if (!analyses[job.id] && userId) {
      setModalLoading(true);
      const analysis = await fetchJobAnalysis(job.id, userId);
      setModalAnalysis(analysis);
      setModalLoading(false);
    }
  }

  async function handleSkip() {
    if (!selectedJob) return;
    try {
      await dismissJob(selectedJob.id);
      setJobs(prev => prev.filter(j => j.id !== selectedJob.id));
      setSelectedJob(null);
      toast.success("Job removed from feed");
    } catch (err) {
      toast.error("Could not dismiss job");
      setSelectedJob(null);
    }
  }
  
  function handleTailor() {
    toast("Resume tailoring coming in Week 6!", { icon: "🔧" });
    setSelectedJob(null);
  }

  const LEVEL_ORDER: Record<string, number> = { HIGH: 0, MEDIUM: 1, LOW: 2 };
  const [searchQuery, setSearchQuery] = useState("");
 
  // Filter displayed jobs by match level if filter is set
  const displayedJobs = jobs
  .filter(job => {
    // Search filter
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchesTitle   = job.title?.toLowerCase().includes(q);
      const matchesCompany = job.company?.toLowerCase().includes(q);
      if (!matchesTitle && !matchesCompany) return false;
    }
    // Match level filter
    if (!filters.matchLevel) return true;
    const analysis = analyses[job.id];
    if (!analysis) return true;
    return analysis.match_level === filters.matchLevel;
  })
  .sort((a, b) => {
    const aLevel = analyses[a.id]?.match_level ?? "LOW";
    const bLevel = analyses[b.id]?.match_level ?? "LOW";
    const levelDiff = (LEVEL_ORDER[aLevel] ?? 2) - (LEVEL_ORDER[bLevel] ?? 2);
    if (levelDiff !== 0) return levelDiff;
    const aDate = a.posted_at ? new Date(a.posted_at).getTime() : 0;
    const bDate = b.posted_at ? new Date(b.posted_at).getTime() : 0;
    return bDate - aDate;
  });
 
  return (
    <div className="max-w-3xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Job Feed</h1>
        <p className="text-gray-500 text-sm mt-1">AI-scored matches for your profile</p>
      </div>
      <div className="mb-4">
        <input
          type="text"
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          placeholder="Search by job title or company..."
          className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
        />
      </div>
      <FilterBar filters={filters} onChange={setFilters} totalJobs={displayedJobs.length} />
 
      {/* Loading skeletons */}
      {loading && (
        <div className="space-y-3">
          {[1,2,3,4,5].map(i => (
            <div key={i} className="bg-white border border-gray-200 rounded-xl p-5 animate-pulse">
              <div className="flex justify-between">
                <div className="flex-1">
                  <div className="h-4 bg-gray-200 rounded w-3/4 mb-2" />
                  <div className="h-3 bg-gray-100 rounded w-1/2 mb-1" />
                  <div className="h-3 bg-gray-100 rounded w-1/3" />
                </div>
                <div className="h-6 w-24 bg-gray-200 rounded-full" />
              </div>
            </div>
          ))}
        </div>
      )}
 
      {/* Error */}
      {error && !loading && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
          <p className="text-red-700 font-medium">{error}</p>
          <button onClick={loadJobs} className="mt-3 text-sm text-red-600 underline">Try again</button>
        </div>
      )}
 
      {/* Empty */}
      {!loading && !error && displayedJobs.length === 0 && (
        <div className="text-center py-16 text-gray-500">
          <p className="text-lg font-medium">No jobs found</p>
          <p className="text-sm mt-1">Try adjusting the filters or wait for the scraper to run</p>
        </div>
      )}
 
      {/* Job list */}
      {!loading && !error && displayedJobs.length > 0 && (
        <div className="space-y-3">
          {displayedJobs.map(job => (
            <JobCard
              key={job.id}
              job={job}
              analysis={analyses[job.id]}
              onClick={() => handleJobClick(job)}
            />
          ))}
        </div>
      )}
 
      {/* Match report modal */}
      {selectedJob && (
        <MatchReportModal
          job={selectedJob}
          analysis={modalAnalysis}
          loading={modalLoading}
          onClose={() => setSelectedJob(null)}
          onTailor={handleTailor}
          onSkip={handleSkip}
        />
      )}
    </div>
  );
}
