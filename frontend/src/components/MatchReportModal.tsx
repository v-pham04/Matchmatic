import type { JobListing, JobAnalysis } from "../types";
import MatchBadge from "./MatchBadge";
import VisaBadge from "./VisaBadge";
 
interface Props {
  job: JobListing;
  analysis: JobAnalysis | null;
  loading: boolean;
  onClose: () => void;
  onTailor: () => void;
  onSkip: () => void;
}
 
export default function MatchReportModal({
  job, analysis, loading, onClose, onTailor, onSkip
}: Props) {
  return (
    // Backdrop
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={onClose}>
      {/* Modal panel — stop clicks from closing when clicking inside */}
      <div
        className="bg-white rounded-2xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-6 border-b border-gray-100">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-xl font-bold text-gray-900">{job.title}</h2>
              <p className="text-gray-600 mt-0.5">{job.company}</p>
              {job.location && <p className="text-gray-400 text-sm">{job.location}</p>}
            </div>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-2xl leading-none">&times;</button>
          </div>
        </div>
 
        <div className="p-6 space-y-6">
 
          {/* Loading state */}
          {loading && (
            <div className="text-center py-8">
              <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              <p className="text-gray-500 text-sm">Running AI analysis...</p>
            </div>
          )}
 
          {/* No analysis yet */}
          {!loading && !analysis && (
            <div className="text-center py-8 text-gray-500">
              <p className="font-medium">Analysis not available yet</p>
              <p className="text-sm mt-1">Upload your resume in Settings to enable AI scoring</p>
            </div>
          )}
 
          {/* Analysis results */}
          {!loading && analysis && (
            <>
              {/* Score row */}
              <div className="flex items-center gap-3 flex-wrap">
                <MatchBadge score={analysis.ats_score} level={analysis.match_level} size="md" />
                {analysis.visa_signal && <VisaBadge signal={analysis.visa_signal} size="md" />}
                {analysis.experience_match && (
                  <span className="text-sm text-gray-500">
                    Experience: <span className="font-medium text-gray-700 capitalize">{analysis.experience_match}</span>
                  </span>
                )}
              </div>
 
              {/* Visa evidence quote */}
              {analysis.visa_evidence && analysis.visa_evidence !== "Not found" && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                  <p className="text-xs text-yellow-700 font-medium mb-1">Visa signal from JD:</p>
                  <p className="text-sm text-yellow-800 italic">"{analysis.visa_evidence}"</p>
                </div>
              )}
 
              {/* Skills grid */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">Matching Skills</p>
                  <div className="flex flex-wrap gap-1.5">
                    {(analysis.matching_skills ?? []).map(skill => (
                      <span key={skill} className="text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded-full">
                        {skill}
                      </span>
                    ))}
                    {(analysis.matching_skills ?? []).length === 0 && (
                      <span className="text-xs text-gray-400">None identified</span>
                    )}
                  </div>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">Missing Skills</p>
                  <div className="flex flex-wrap gap-1.5">
                    {(analysis.missing_skills ?? []).map(skill => (
                      <span key={skill} className="text-xs bg-red-100 text-red-800 px-2 py-0.5 rounded-full">
                        {skill}
                      </span>
                    ))}
                    {(analysis.missing_skills ?? []).length === 0 && (
                      <span className="text-xs text-gray-400">None identified</span>
                    )}
                  </div>
                </div>
              </div>
 
              {/* Written analysis — the 4-paragraph report */}
              {analysis.summary && (
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">Match Analysis</p>
                  <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                    {analysis.summary.split("\n\n").filter(p => p.trim()).map((para, i) => (
                      <p key={i} className="text-sm text-gray-700 leading-relaxed">{para}</p>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
 
        {/* Action buttons */}
        <div className="p-6 border-t border-gray-100 flex gap-3">
          <button
            onClick={onTailor}
            disabled={!analysis}
            className="flex-1 py-3 bg-blue-600 text-white font-medium rounded-xl hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Tailor Resume & Apply
          </button>
          <button
            onClick={onSkip}
            className="px-6 py-3 text-gray-600 border border-gray-200 rounded-xl hover:bg-gray-50"
          >
            Skip
          </button>
          <a
            href={job.url}
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-3 text-blue-600 border border-blue-200 rounded-xl hover:bg-blue-50 text-sm"
          >
            View Job ↗
          </a>
        </div>
      </div>
    </div>
  );
}