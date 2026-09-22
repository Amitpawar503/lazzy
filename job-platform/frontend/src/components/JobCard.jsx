import React from "react";

function scoreColor(s) {
  if (s == null) return "#9ca3af";
  if (s >= 70) return "#16a34a";
  if (s >= 40) return "#d97706";
  return "#6b7280";
}

export default function JobCard({ job, onEnhance, canEnhance }) {
  const posted = job.posted_at ? new Date(job.posted_at).toLocaleDateString() : "—";
  return (
    <div className="job-card">
      <div className="job-card-head">
        <div>
          <h3 className="job-title">{job.title}</h3>
          <div className="job-company">
            {job.company}
            {job.location_raw ? ` · ${job.location_raw}` : ""}
          </div>
        </div>
        {job.match_score != null && (
          <div className="match-badge" style={{ borderColor: scoreColor(job.match_score) }}>
            <span style={{ color: scoreColor(job.match_score) }}>{Math.round(job.match_score)}</span>
            <small>match</small>
          </div>
        )}
      </div>

      <div className="job-tags">
        {job.is_remote && <span className="tag tag-remote">Remote</span>}
        {job.remote_scope === "india" && <span className="tag">Remote · India</span>}
        {job.remote_scope === "outside_india" && <span className="tag">Remote · Outside India</span>}
        {job.remote_scope === "global" && <span className="tag">Remote · Global</span>}
        {job.is_wfh_ncr && <span className="tag tag-wfh">WFH · Delhi-NCR</span>}
        {job.category && <span className="tag tag-cat">{job.category}</span>}
        {job.country && <span className="tag tag-country">{job.country}</span>}
        {job.salary_raw && <span className="tag tag-salary">{job.salary_raw}</span>}
        <span className="tag tag-source">{job.source}</span>
      </div>

      {job.match_reason && <div className="match-reason">🎯 {job.match_reason}</div>}

      <div className="job-actions">
        <a className="btn btn-apply" href={job.apply_url} target="_blank" rel="noreferrer">
          Apply
        </a>
        {canEnhance && (
          <button className="btn btn-ghost" onClick={() => onEnhance(job)}>
            ✨ Tailor resume
          </button>
        )}
        <span className="job-date">Posted {posted}</span>
      </div>
    </div>
  );
}
