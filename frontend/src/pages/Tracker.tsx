export default function Tracker() {
  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Application Tracker</h1>
        <p className="text-gray-500 text-sm mt-1">Track every application you submit</p>
      </div>
 
      {/* Empty state — shown until Week 9 when auto-apply is built */}
      <div className="text-center py-20">
        <div className="w-16 h-16 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-4">
          <span className="text-3xl">📋</span>
        </div>
        <h2 className="text-lg font-medium text-gray-900 mb-2">No applications yet</h2>
        <p className="text-gray-500 text-sm max-w-sm mx-auto">
          Once you start applying to jobs through Matchmatic, they will appear here
          as a kanban board with Applied, Interview, Offer, and Rejected columns.
        </p>
        <a
          href="/"
          className="mt-6 inline-block px-5 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700"
        >
          Browse Jobs
        </a>
      </div>
    </div>
  );
}
