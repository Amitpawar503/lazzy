import { useState } from "react";
import Heatmap360 from "./components/Heatmap360";
import SectorHeatmap from "./components/SectorHeatmap";
import FiiDiiActivity from "./components/FiiDiiActivity";
import SignalScorecard from "./components/SignalScorecard";
import Screeners from "./components/Screeners";
import NewsFeed from "./components/NewsFeed";
import NewsImpact from "./components/NewsImpact";
import { StockDetailProvider } from "./components/StockDetail";
import Strategies from "./components/Strategies";
import StylePicks from "./components/StylePicks";

type Tab = "360" | "sectors" | "fiidii" | "signals" | "screeners" | "news" | "impact" | "ideas" | "style";

const TABS: { id: Tab; label: string }[] = [
  { id: "360", label: "360° Market" },
  { id: "sectors", label: "Sector Heatmap" },
  { id: "screeners", label: "Best Stocks" },
  { id: "ideas", label: "Ideas" },
  { id: "style", label: "Style Picks" },
  { id: "signals", label: "Algo Signals" },
  { id: "fiidii", label: "FII / DII Activity" },
  { id: "news", label: "News" },
  { id: "impact", label: "News Impact" },
];

export default function App() {
  const [tab, setTab] = useState<Tab>("360");
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
        <div className="disclaimer">EOD / delayed · sample data if offline</div>
      </header>

      <main className="content">
        {tab === "360" && <Heatmap360 />}
        {tab === "sectors" && <SectorHeatmap />}
        {tab === "fiidii" && <FiiDiiActivity />}
        {tab === "signals" && <SignalScorecard />}
        {tab === "screeners" && <Screeners />}
        {tab === "ideas" && <Strategies />}
        {tab === "style" && <StylePicks />}
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
