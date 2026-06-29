import type { JobListing, JobAnalysis } from "../types";
import MatchBadge from "./MatchBadge";
import VisaBadge from "./VisaBadge";

interface Props {
  job: JobListing;
  analysis?: JobAnalysis;
  onClick: () => void;
}

 
// Helper to show how long ago the job was posted
function timeAgo(dateStr: string | null): string {
  if (!dateStr) return "Recently";
  const diff = Date.now() - new Date(dateStr).getTime();
  const hours = Math.floor(diff / 1000 / 60 / 60);
  if (hours < 1) return "Just now";
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}
 
export default function JobCard({ job, analysis, onClick }: Props) {
  const countryFlag = job.country === "us" ? "🇺🇸" : job.country === "vietnam" ? "🇻🇳" : "";
  const sourceLabels: Record<string, string> = {
    jsearch_us: "JSearch",
  };
  const sourceLabel = sourceLabels[job.source ?? ""] ?? job.source ?? "Job board";
 
  return (
    <div
      onClick={onClick}
      className="bg-white border border-gray-200 rounded-xl p-5 hover:border-blue-400 hover:shadow-sm cursor-pointer transition-all">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-gray-900 truncate">{job.title}</h3>
          <p className="text-gray-600 text-sm mt-0.5">{job.company}</p>
          {job.location && <p className="text-gray-400 text-xs mt-1">{job.location}</p>}
        </div>
        <div className="flex flex-col items-end gap-1.5 shrink-0">
          {/* AI Score Badge — shows score, failure, or pending state */}
          {analysis?.status === "failed" ? (
            <span className="text-xs bg-red-100 text-red-700 px-2 py-1 rounded-full">
              Analysis failed
            </span>
          ) : analysis?.status === "complete" || (analysis?.match_level && analysis?.ats_score != null) ? (
            <MatchBadge score={analysis.ats_score} level={analysis.match_level} />
          ) : (
            <span className="text-xs bg-gray-100 text-gray-500 px-2 py-1 rounded-full animate-pulse">
              Analysing...
            </span>
          )}
          <span className="text-xs text-gray-400">{timeAgo(job.posted_at)}</span>
        </div>
      </div>
 
      {/* Footer row — source, country, visa badge */}
      <div className="mt-3 flex items-center gap-2 flex-wrap">
        <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">{countryFlag} {sourceLabel}</span>
        {analysis?.visa_signal && (
          <VisaBadge signal={analysis.visa_signal} size="sm" />
        )}
      </div>
    </div>
  );
}