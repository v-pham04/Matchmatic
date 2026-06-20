import { useState, useEffect } from "react";
import { fetchJobs } from "../api/jobs";
import JobCard from "../components/JobCard";
import type { JobListing } from "../types";
 
export default function Jobs() {
  const [jobs, setJobs] = useState<JobListing[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [countryFilter, setCountryFilter] = useState<string>("");
 
  useEffect(() => {
    loadJobs();
  }, [countryFilter]);
 
  async function loadJobs() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchJobs(countryFilter || undefined);
      setJobs(data);
    } catch (err) {
      setError("Could not load jobs. Make sure the backend is running.");
    } finally {
      setLoading(false);
    }
  }
 
  return (
    <div className="max-w-3xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Job Feed</h1>
          <p className="text-gray-500 text-sm mt-1">{jobs.length} jobs found</p>
        </div>
 
        {/* Country filter buttons */}
        <div className="flex gap-2">
          {[["", "All"], ["us", "🇺🇸 US"], ["vietnam", "🇻🇳 Vietnam"]].map(([val, label]) => (
            <button
              key={val}
              onClick={() => setCountryFilter(val)}
              className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${ 
                countryFilter === val
                  ? "bg-blue-600 text-white border-blue-600"
                  : "bg-white text-gray-600 border-gray-300 hover:border-blue-400"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
 
      {/* Loading state */}
      {loading && (
        <div className="space-y-3">
          {[1,2,3,4,5].map(i => (
            <div key={i} className="bg-white border border-gray-200 rounded-xl p-5 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2" />
              <div className="h-3 bg-gray-100 rounded w-1/2" />
            </div>
          ))}
        </div>
      )}
 
      {/* Error state */}
      {error && !loading && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
          <p className="text-red-700 font-medium">{error}</p>
          <button onClick={loadJobs} className="mt-3 text-sm text-red-600 underline">Try again</button>
        </div>
      )}
 
      {/* Empty state */}
      {!loading && !error && jobs.length === 0 && (
        <div className="text-center py-16 text-gray-500">
          <p className="text-lg font-medium">No jobs yet</p>
          <p className="text-sm mt-1">Jobs will appear here once the scraper runs.</p>
        </div>
      )}
 
      {/* Job list */}
      {!loading && !error && jobs.length > 0 && (
        <div className="space-y-3">
          {jobs.map(job => (
            <JobCard
              key={job.id}
              job={job}
              onClick={() => window.open(job.url, "_blank")}
            />
          ))}
        </div>
      )}
    </div>
  );
}
