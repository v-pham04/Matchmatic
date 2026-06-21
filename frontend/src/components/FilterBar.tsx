interface Filters {
    country: string;
    matchLevel: string;
  }
   
  interface Props {
    filters: Filters;
    onChange: (filters: Filters) => void;
    totalJobs: number;
  }
   
  export default function FilterBar({ filters, onChange, totalJobs }: Props) {
    const countries = [
      { value: "", label: "All Countries" },
      { value: "us", label: "🇺🇸 US" },
      { value: "vietnam", label: "🇻🇳 Vietnam" },
    ];
   
    const levels = [
      { value: "", label: "All Levels" },
      { value: "HIGH",   label: "🟢 High Match"   },
      { value: "MEDIUM", label: "🟡 Medium Match" },
      { value: "LOW",    label: "🔴 Low Match"    },
    ];
   
    return (
      <div className="flex items-center justify-between flex-wrap gap-3 mb-6">
        <p className="text-sm text-gray-500">{totalJobs} jobs found</p>
   
        <div className="flex items-center gap-2 flex-wrap">
          {/* Country filter */}
          <div className="flex gap-1">
            {countries.map(c => (
              <button
                key={c.value}
                onClick={() => onChange({ ...filters, country: c.value })}
                className={`px-3 py-1.5 text-xs rounded-lg border transition-colors ${ 
                  filters.country === c.value
                    ? "bg-blue-600 text-white border-blue-600"
                    : "bg-white text-gray-600 border-gray-300 hover:border-blue-400"
                }`}
              >
                {c.label}
              </button>
            ))}
          </div>
   
          {/* Match level filter */}
          <div className="flex gap-1">
            {levels.map(l => (
              <button
                key={l.value}
                onClick={() => onChange({ ...filters, matchLevel: l.value })}
                className={`px-3 py-1.5 text-xs rounded-lg border transition-colors ${ 
                  filters.matchLevel === l.value
                    ? "bg-blue-600 text-white border-blue-600"
                    : "bg-white text-gray-600 border-gray-300 hover:border-blue-400"
                }`}
              >
                {l.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }
  