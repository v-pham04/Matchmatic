import type { JobListing } from "../types";
 
interface Props {
  job: JobListing;
  onClick: () => void;
}
 
// Helper to show how long ago the job was posted
function timeAgo(dateStr: string | null): string {
  if (!dateStr) return "Recently posted";
  const diff = Date.now() - new Date(dateStr).getTime();
  const hours = Math.floor(diff / 1000 / 60 / 60);
  if (hours < 1) return "Just posted";
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}
 
export default function JobCard({ job, onClick }: Props) {
  const countryLabel = job.country === "us" ? "🇺🇸 US" : job.country === "vietnam" ? "🇻🇳 Vietnam" : "";
  const sourceLabel = job.source === "indeed_us" ? "Indeed" : job.source === "vietnamworks" ? "VietnamWorks" : job.source ?? "";
 
  return (
    <div
      onClick={onClick}
      className="bg-white border border-gray-200 rounded-xl p-5 hover:border-blue-400 hover:shadow-sm cursor-pointer transition-all"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-gray-900 truncate">{job.title}</h3>
          <p className="text-gray-600 text-sm mt-0.5">{job.company}</p>
          {job.location && <p className="text-gray-400 text-xs mt-1">{job.location}</p>}
        </div>
        <div className="flex flex-col items-end gap-1 shrink-0">
          <span className="text-xs text-gray-400">{timeAgo(job.posted_at)}</span>
          {countryLabel && (
            <span className="text-xs text-gray-500">{countryLabel}</span>
          )}
        </div>
      </div>
      <div className="mt-3 flex items-center gap-2">
        <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">{sourceLabel}</span>
        {!job.is_processed && (
          <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded">Awaiting AI analysis</span>
        )}
      </div>
    </div>
  );
}
