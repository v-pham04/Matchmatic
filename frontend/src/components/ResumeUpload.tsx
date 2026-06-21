import { useState, useRef } from "react";
import client from "../api/client";
 
interface Props {
  userId: string;
  onUploadSuccess?: (fileUrl: string) => void;
}
 
export default function ResumeUpload({ userId, onUploadSuccess }: Props) {
  const [uploading, setUploading] = useState(false);
  const [uploadedName, setUploadedName] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
 
  const handleFile = async (file: File) => {
    if (!userId) {
      setError("User session not ready. Sign out and sign in again.");
      return;
    }

    // Only allow PDF and DOCX
    if (!file.name.match(/\.(pdf|docx)$/i)) {
      setError("Please upload a PDF or DOCX file only.");
      return;
    }
 
    setUploading(true);
    setError(null);
 
    try {
      // FormData is how you send files over HTTP — you cannot send binary in JSON
      const formData = new FormData();
      formData.append("file", file);
 
      const response = await client.post(`/resume/upload?user_id=${userId}`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
 
      setUploadedName(file.name);
      onUploadSuccess?.(response.data.file_url);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Upload failed. Is the backend running?");
    } finally {
      setUploading(false);
    }
  };
 
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };
 
  return (
    <div
      onDragOver={e => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => fileInputRef.current?.click()}
      className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${ 
        dragging ? "border-blue-500 bg-blue-50" :
        uploadedName ? "border-green-500 bg-green-50" :
        "border-gray-300 hover:border-blue-400 bg-white"
      }`}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.docx"
        className="hidden"
        onChange={e => e.target.files?.[0] && handleFile(e.target.files[0])}
      />
 
      {uploading ? (
        <p className="text-blue-600 font-medium">Uploading and extracting text...</p>
      ) : uploadedName ? (
        <div>
          <p className="text-green-700 font-medium">✓ {uploadedName}</p>
          <p className="text-green-600 text-sm mt-1">Resume uploaded successfully. Click to replace.</p>
        </div>
      ) : (
        <div>
          <p className="text-gray-700 font-medium">Drop your resume here</p>
          <p className="text-gray-400 text-sm mt-1">PDF or DOCX · or click to browse</p>
        </div>
      )}
 
      {error && <p className="text-red-600 text-sm mt-3">{error}</p>}
    </div>
  );
}
