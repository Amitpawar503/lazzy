import { useEffect, useState } from "react";
import { api, type NewsFeed as NF } from "../api";

type Cat = "all" | "india" | "global";

function sentClass(s: string) {
  return s === "positive" ? "s-pos" : s === "negative" ? "s-neg" : "s-neu";
}

export default function NewsFeed() {
  const [cat, setCat] = useState<Cat>("all");
  const [data, setData] = useState<NF | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    setErr(null);
    api.news(cat, 50).then(setData).catch((e) => setErr(String(e)));
  }, [cat]);

  return (
    <section>
      <div className="screen-head">
        <div>
          <h2>Market News</h2>
          <p className="sub">
            Aggregated Indian &amp; global market headlines, entity-linked and
            sentiment-tagged{data ? ` · ${data.count} items` : ""}
          </p>
        </div>
        <div className="control">
          <label>Feed</label>
          <div className="segmented">
            {(["all", "india", "global"] as Cat[]).map((c) => (
              <button key={c} className={c === cat ? "on" : ""} onClick={() => setCat(c)}>
                {c}
              </button>
            ))}
          </div>
        </div>
      </div>

      {err && <div className="error">Failed to load: {err}</div>}

      <div className="news-list">
        {data?.items.map((n) => (
          <a className="news-card" key={n.id} href={n.url} target="_blank" rel="noreferrer">
            <div className="news-top">
              <span className={`sent ${sentClass(n.sentiment)}`}>{n.sentiment}</span>
              <span className="news-src">{n.source}</span>
              <span className="news-cat">{n.category}</span>
              <span className="news-time">{n.published}</span>
            </div>
            <div className="news-title">{n.title}</div>
            <div className="news-summary">{n.summary}</div>
            {n.tickers.length > 0 && (
              <div className="news-tickers">
                {n.tickers.map((t) => (
                  <span className="tk" key={t}>{t}</span>
                ))}
              </div>
            )}
          </a>
        ))}
      </div>

      {data && (
        <p className="src-note">
          Sources wired for live polling: {data.sources.join(" · ")}
        </p>
      )}
    </section>
  );
}
