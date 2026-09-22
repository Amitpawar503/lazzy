import React, { useEffect, useState } from "react";
import { api } from "../api";

export default function EnhanceModal({ job, resumeId, onClose }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    let alive = true;
    setData(null);
    setErr("");
    api
      .enhance(resumeId, job.id)
      .then((d) => alive && setData(d))
      .catch(() => alive && setErr("Could not generate enhancement."));
    return () => {
      alive = false;
    };
  }, [job.id, resumeId]);

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <div>
            <h2>Tailor resume → {job.title}</h2>
            <div className="muted">{job.company}</div>
          </div>
          <button className="btn btn-ghost" onClick={onClose}>✕</button>
        </div>

        {!data && !err && <div className="loading">Generating tailored resume…</div>}
        {err && <div className="error">{err}</div>}

        {data && (
          <div className="modal-body">
            <div className="ai-flag">
              {data.ai_used ? "✨ AI-generated (Anthropic)" : "⚙️ Rule-based draft (set ANTHROPIC_API_KEY for AI)"}
            </div>

            <section>
              <h4>Tailored summary</h4>
              <p>{data.enhanced_summary}</p>
            </section>

            <section>
              <h4>Suggested bullet points</h4>
              <ul>
                {data.tailored_bullets.map((b, i) => (
                  <li key={i}>{b}</li>
                ))}
              </ul>
            </section>

            <section>
              <h4>Keywords to add (ATS)</h4>
              <div className="skills">
                {data.keywords_to_add.map((k) => (
                  <span key={k} className="chip">{k}</span>
                ))}
              </div>
            </section>

            <section>
              <h4>Cover letter</h4>
              <pre className="cover">{data.cover_letter}</pre>
            </section>
          </div>
        )}
      </div>
    </div>
  );
}
