import React, { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";
import Filters from "./components/Filters";
import JobCard from "./components/JobCard";
import ResumePanel from "./components/ResumePanel";
import EnhanceModal from "./components/EnhanceModal";

const TABS = [
  { key: "all", label: "All jobs" },
  { key: "remote_india", label: "Remote · India" },
  { key: "remote_outside", label: "Remote · Outside India" },
  { key: "wfh_ncr", label: "WFH · Delhi-NCR" },
];

const EMPTY_FILTERS = {
  q: "", category: "", country: "", min_salary: "", date_from: "", sort: "recent",
};

export default function App() {
  const [tab, setTab] = useState("all");
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const [facets, setFacets] = useState({});
  const [page, setPage] = useState({ items: [], total: 0 });
  const [loading, setLoading] = useState(false);
  const [resume, setResume] = useState(null);
  const [enhanceJob, setEnhanceJob] = useState(null);
  const [live, setLive] = useState([]);      // newly streamed jobs
  const [health, setHealth] = useState(null);
  const [banner, setBanner] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.listJobs({
        tab,
        ...filters,
        resume_id: resume?.id,
        sort: resume ? filters.sort : "recent",
        limit: 40,
      });
      setPage(data);
    } catch (e) {
      setBanner("Failed to load jobs. Is the backend running on :8000?");
    } finally {
      setLoading(false);
    }
  }, [tab, filters, resume]);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    api.health().then(setHealth).catch(() => {});
    api.facets().then(setFacets).catch(() => {});
  }, []);

  // --- Live SSE feed of newly ingested jobs ---
  const esRef = useRef(null);
  useEffect(() => {
    const es = new EventSource("/api/stream/jobs");
    esRef.current = es;
    es.addEventListener("job", (ev) => {
      try {
        const job = JSON.parse(ev.data);
        setLive((prev) => [job, ...prev].slice(0, 25));
      } catch {}
    });
    es.onerror = () => {};
    return () => es.close();
  }, []);

  async function seedSample() {
    setBanner("Loading sample jobs…");
    await api.loadSample();
    setBanner("");
    load();
    api.facets().then(setFacets);
  }

  const hasResume = !!resume;

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">🐾 CareerHound<span className="brand-sub">.io</span></div>
        <div className="topbar-right">
          {health && (
            <span className={`pill ${health.ai_enabled ? "pill-on" : "pill-off"}`}>
              AI {health.ai_enabled ? "on" : "off"}
            </span>
          )}
          <button className="btn btn-ghost" onClick={seedSample}>Load sample</button>
          <button className="btn btn-ghost" onClick={() => api.triggerIngest().then(() => setBanner("Ingest triggered — new jobs will stream in."))}>
            Refresh live
          </button>
        </div>
      </header>

      <ResumePanel resume={resume} setResume={setResume} onUploaded={() => load()} />

      {banner && <div className="banner">{banner}</div>}

      {live.length > 0 && (
        <div className="live-strip">
          <span className="live-dot" /> Live:
          {live.slice(0, 4).map((jb, i) => (
            <span key={i} className="live-item">
              {jb.title} @ {jb.company}
              {jb.match_score != null && <b> · {Math.round(jb.match_score)}%</b>}
            </span>
          ))}
          <button className="btn btn-tiny" onClick={() => setLive([])}>clear</button>
        </div>
      )}

      <nav className="tabs">
        {TABS.map((t) => (
          <button
            key={t.key}
            className={`tab ${tab === t.key ? "active" : ""}`}
            onClick={() => setTab(t.key)}
          >
            {t.label}
          </button>
        ))}
        <span className="count">{page.total} jobs</span>
      </nav>

      <div className="layout">
        <Filters filters={filters} setFilters={setFilters} facets={facets} hasResume={hasResume} />

        <main className="results">
          {loading && <div className="loading">Loading…</div>}
          {!loading && page.items.length === 0 && (
            <div className="empty">
              No jobs yet. Click <b>Load sample</b> to try it offline, or configure sources and
              <b> Refresh live</b> to pull from company career pages.
            </div>
          )}
          {page.items.map((job) => (
            <JobCard
              key={job.id}
              job={job}
              canEnhance={hasResume}
              onEnhance={setEnhanceJob}
            />
          ))}
        </main>
      </div>

      {enhanceJob && resume && (
        <EnhanceModal job={enhanceJob} resumeId={resume.id} onClose={() => setEnhanceJob(null)} />
      )}
    </div>
  );
}
