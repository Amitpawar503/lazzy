import React, { useRef, useState } from "react";
import { api } from "../api";

export default function ResumePanel({ resume, setResume, onUploaded }) {
  const fileRef = useRef();
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  async function handleFile(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setBusy(true);
    setErr("");
    try {
      const r = await api.uploadResume(file);
      setResume(r);
      onUploaded?.(r);
    } catch (e) {
      setErr("Upload failed. Use a PDF, DOCX or TXT resume.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="resume-panel">
      {resume ? (
        <div className="resume-loaded">
          <div>
            <strong>📄 {resume.filename}</strong>
            {resume.title_hint && <div className="muted">Target role: {resume.title_hint}</div>}
            {resume.skills && (
              <div className="skills">
                {resume.skills.split(",").slice(0, 10).map((s) => (
                  <span key={s} className="chip">{s.trim()}</span>
                ))}
              </div>
            )}
          </div>
          <button className="btn btn-ghost" onClick={() => fileRef.current?.click()}>
            Replace
          </button>
        </div>
      ) : (
        <div className="resume-empty">
          <span>Upload your resume to get matched jobs ranked for you.</span>
          <button className="btn btn-primary" disabled={busy} onClick={() => fileRef.current?.click()}>
            {busy ? "Parsing…" : "Upload resume"}
          </button>
        </div>
      )}
      <input
        ref={fileRef}
        type="file"
        accept=".pdf,.docx,.txt"
        style={{ display: "none" }}
        onChange={handleFile}
      />
      {err && <div className="error">{err}</div>}
    </div>
  );
}
