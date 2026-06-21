import { useState } from "react";
import client from "../api/client";
import ResumeUpload from "../components/ResumeUpload";
import { useAuth } from "../hooks/useAuth";

 
// The shape of our settings form data
interface SettingsForm {
  target_market: "vietnam" | "us" | "both";
  visa_check_enabled: boolean;
  min_match_score: number;
  job_keywords: string[];
}
 
export default function Settings() {
  const { userId } = useAuth();
  const [form, setForm] = useState<SettingsForm>({
    target_market: "both",
    visa_check_enabled: false,
    min_match_score: 70,
    job_keywords: [],
  });
  const [keywordInput, setKeywordInput] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
 
  // For now using a hardcoded user ID — Week 3 will replace this with real auth
  const USER_ID = userId;

  const addKeyword = () => {
    const kw = keywordInput.trim();
    if (kw && !form.job_keywords.includes(kw)) {
      setForm(prev => ({ ...prev, job_keywords: [...prev.job_keywords, kw] }));
    }
    setKeywordInput("");
  };
 
  const removeKeyword = (kw: string) => {
    setForm(prev => ({ ...prev, job_keywords: prev.job_keywords.filter(k => k !== kw) }));
  };
 
  const handleSave = async () => {
    if (!USER_ID) return;
    setSaving(true);
    try {
      await client.patch(`/users/${USER_ID}/settings`, form);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      console.error("Failed to save settings:", err);
      alert("Failed to save. Is the backend running?");
    } finally {
      setSaving(false);
    }
  };
 
  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-1">Settings</h1>
      <p className="text-gray-500 mb-8">Configure your job search before starting the engine.</p>
 
      {/* Country selector */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Target Market
        </label>
        <div className="flex gap-3">
          {(["vietnam", "us", "both"] as const).map(market => (
            <button
              key={market}
              onClick={() => setForm(prev => ({ ...prev, target_market: market }))}
              className={`px-4 py-2 rounded-lg border text-sm font-medium transition-colors ${ 
                form.target_market === market
                  ? "bg-blue-600 text-white border-blue-600"
                  : "bg-white text-gray-700 border-gray-300 hover:border-blue-400"
              }`}
            >
              {market === "both" ? "Both Markets" : market === "us" ? "US Only" : "Vietnam Only"}
            </button>
          ))}
        </div>
      </div>
 
      {/* Visa check toggle — only relevant for US */}
      <div className="mb-6 flex items-center justify-between p-4 bg-gray-50 rounded-lg border">
        <div>
          <p className="text-sm font-medium text-gray-900">F1-OPT Visa Check</p>
          <p className="text-xs text-gray-500 mt-0.5">
            Automatically detect whether US jobs accept visa holders
          </p>
        </div>
        <button
          onClick={() => setForm(prev => ({ ...prev, visa_check_enabled: !prev.visa_check_enabled }))}
          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${ 
            form.visa_check_enabled ? "bg-blue-600" : "bg-gray-300"
          }`}
        >
          <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${ 
            form.visa_check_enabled ? "translate-x-6" : "translate-x-1"
          }`} />
        </button>
      </div>
 
      {/* Minimum match score slider */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Minimum Match Score: <span className="text-blue-600 font-bold">{form.min_match_score}%</span>
        </label>
        <input
          type="range" min={40} max={95} step={5}
          value={form.min_match_score}
          onChange={e => setForm(prev => ({ ...prev, min_match_score: Number(e.target.value) }))}
          className="w-full accent-blue-600"
        />
        <div className="flex justify-between text-xs text-gray-400 mt-1">
          <span>40% (show most jobs)</span>
          <span>95% (very selective)</span>
        </div>
      </div>
 
      {/* Job keywords input */}
      <div className="mb-8">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Job Title Keywords
        </label>
        <div className="flex gap-2 mb-3">
          <input
            type="text"
            value={keywordInput}
            onChange={e => setKeywordInput(e.target.value)}
            onKeyDown={e => e.key === "Enter" && addKeyword()}
            placeholder="e.g. DevOps Engineer — press Enter to add"
            className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={addKeyword}
            className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700"
          >
            Add
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {form.job_keywords.map(kw => (
            <span key={kw} className="flex items-center gap-1 bg-blue-100 text-blue-800 text-sm px-3 py-1 rounded-full">
              {kw}
              <button onClick={() => removeKeyword(kw)} className="text-blue-600 hover:text-blue-900 ml-1">×</button>
            </span>
          ))}
        </div>
      </div>

      <div className="mb-8">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Your Master Resume
        </label>
        <ResumeUpload userId={USER_ID ?? ""} onUploadSuccess={(url) => console.log("Uploaded:", url)} />
      </div>

 
      {/* Save button */}
      <button
        onClick={handleSave}
        disabled={saving}
        className="w-full py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50"
      >
        {saving ? "Saving..." : saved ? "Saved!" : "Save Settings"}
      </button>
    </div>
  );
}
