import { useEffect, useState } from "react";
import { api } from "./api";
import Heatmap360 from "./components/Heatmap360";
import SectorHeatmap from "./components/SectorHeatmap";
import FiiDiiActivity from "./components/FiiDiiActivity";
import SignalScorecard from "./components/SignalScorecard";
import Screeners from "./components/Screeners";
import NewsFeed from "./components/NewsFeed";
import NewsImpact from "./components/NewsImpact";
import { StockDetailProvider } from "./components/StockDetail";
import Strategies from "./components/Strategies";

type Tab = "360" | "sectors" | "fiidii" | "signals" | "screeners" | "news" | "impact" | "ideas" | "themes";

const TABS: { id: Tab; label: string }[] = [
  { id: "360", label: "360° Market" },
  { id: "sectors", label: "Sector Heatmap" },
  { id: "screeners", label: "Best Stocks" },
  { id: "ideas", label: "Ideas" },
  { id: "themes", label: "Themes" },
  { id: "signals", label: "Algo Signals" },
  { id: "fiidii", label: "FII / DII Activity" },
  { id: "news", label: "News" },
  { id: "impact", label: "News Impact" },
];

export default function App() {
  const [tab, setTab] = useState<Tab>("360");
  const [prov, setProv] = useState<{ provider?: string; live?: boolean; size?: number } | null>(null);
  useEffect(() => {
    api.meta().then((m) => setProv({ provider: m.provider, live: m.live, size: m.universe_size })).catch(() => {});
  }, []);
  return (
    <StockDetailProvider>
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="logo">◆</span> Lazzy <b>Markets</b>
        </div>
        <nav className="tabs">
          {TABS.map((t) => (
            <button
              key={t.id}
              className={t.id === tab ? "on" : ""}
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </nav>
        <div className="disclaimer">
          {prov?.live
            ? <span><span className="live-dot">● LIVE</span> · {prov.provider} · {prov.size} stocks</span>
            : <span>sample data · {prov?.size ?? ""} stocks</span>}
        </div>
      </header>

      <main className="content">
        {tab === "360" && <Heatmap360 />}
        {tab === "sectors" && <SectorHeatmap />}
        {tab === "fiidii" && <FiiDiiActivity />}
        {tab === "signals" && <SignalScorecard />}
        {tab === "screeners" && <Screeners />}
        {tab === "ideas" && <Strategies variant="ideas" />}
        {tab === "themes" && <Strategies variant="themes" />}
        {tab === "news" && <NewsFeed />}
        {tab === "impact" && <NewsImpact />}
      </main>

      <footer className="foot">
        Not investment advice · data may be delayed or illustrative · click any stock for its full thesis
      </footer>
    </div>
    </StockDetailProvider>
  );
}
