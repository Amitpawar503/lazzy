"""News sources + bundled sample headlines.

RSS_FEEDS lists free feeds we can poll live in a later phase (Moneycontrol, ET,
Livemint, Google News, Reuters, etc.). For now the News screen renders from
SAMPLE_NEWS so it works offline; the live fetcher (services/news.py) is a
drop-in that falls back to this list.
"""
from __future__ import annotations

# Free/public RSS feeds (poll politely + cache). Wired in a later phase.
RSS_FEEDS: dict[str, str] = {
    # India
    "Moneycontrol": "https://www.moneycontrol.com/rss/latestnews.xml",
    "Economic Times": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "Livemint": "https://www.livemint.com/rss/markets",
    "Business Standard": "https://www.business-standard.com/rss/markets-106.rss",
    "Google News (India markets)":
        "https://news.google.com/rss/search?q=NSE+BSE+Indian+stock+market&hl=en-IN&gl=IN&ceid=IN:en",
    # Global
    "Reuters Business": "https://www.reutersagency.com/feed/?best-topics=business-finance",
    "CNBC Markets": "https://www.cnbc.com/id/20910258/device/rss/rss.html",
    "MarketWatch": "https://feeds.marketwatch.com/marketwatch/topstories/",
}

# id, source, title, url, published, summary, tickers, sentiment, score, category
_ROWS = [
    ("n1", "Economic Times",
     "Tata Sons weighs listing; group holding companies in focus",
     "https://economictimes.indiatimes.com/", "2026-09-18 09:15",
     "Reports suggest Tata Sons may pursue a listing. Market attention turns to "
     "listed Tata entities and holders of Tata Sons stakes.",
     ["TATAMOTORS", "TCS", "TATASTEEL"], "positive", 0.55, "india"),
    ("n2", "Moneycontrol",
     "FII inflows lift banking stocks; Nifty Bank at record high",
     "https://www.moneycontrol.com/", "2026-09-18 10:05",
     "Foreign investors added to private banks as the index touched a new peak.",
     ["HDFCBANK", "ICICIBANK", "AXISBANK"], "positive", 0.6, "india"),
    ("n3", "Livemint",
     "IT majors cautious on FY27 guidance amid soft discretionary spend",
     "https://www.livemint.com/", "2026-09-18 08:40",
     "Management commentary points to muted near-term demand for IT services.",
     ["TCS", "INFY", "WIPRO"], "negative", -0.45, "india"),
    ("n4", "Business Standard",
     "Auto sales momentum continues into festive season",
     "https://www.business-standard.com/", "2026-09-17 18:20",
     "Passenger vehicle makers report strong festive bookings.",
     ["MARUTI", "TATAMOTORS", "M&M"], "positive", 0.5, "india"),
    ("n5", "Moneycontrol",
     "Metal stocks slip as China demand worries resurface",
     "https://www.moneycontrol.com/", "2026-09-17 14:10",
     "Steel and aluminium names fell on weaker global cues.",
     ["TATASTEEL", "JSWSTEEL", "HINDALCO"], "negative", -0.4, "india"),
    ("n6", "Economic Times",
     "RBI holds rates, retains 'withdrawal of accommodation' stance",
     "https://economictimes.indiatimes.com/", "2026-09-16 11:00",
     "Policy unchanged; rate-sensitive sectors react modestly.",
     ["HDFCBANK", "BAJFINANCE"], "neutral", 0.05, "india"),
    ("n7", "Livemint",
     "Pharma exporters gain on favourable USFDA outcomes",
     "https://www.livemint.com/", "2026-09-16 09:30",
     "Select pharma names rose after clean inspection reports.",
     ["SUNPHARMA", "CIPLA", "DRREDDY"], "positive", 0.48, "india"),
    ("n8", "Moneycontrol",
     "Reliance unveils new energy capex roadmap",
     "https://www.moneycontrol.com/", "2026-09-15 16:45",
     "Conglomerate details investments across green energy and retail.",
     ["RELIANCE"], "positive", 0.4, "india"),
    # Global
    ("n9", "Reuters Business",
     "US Fed signals data-dependent path; global equities steady",
     "https://www.reuters.com/", "2026-09-18 06:00",
     "Rate outlook keeps risk assets range-bound.",
     [], "neutral", 0.1, "global"),
    ("n10", "CNBC Markets",
     "Oil edges higher on supply concerns",
     "https://www.cnbc.com/", "2026-09-17 22:30",
     "Crude gains weigh on oil-importing economies.",
     ["ONGC", "RELIANCE"], "negative", -0.2, "global"),
    ("n11", "MarketWatch",
     "Global chip rally continues; Asian tech suppliers follow",
     "https://www.marketwatch.com/", "2026-09-17 20:10",
     "Semiconductor strength spills over to Asian markets.",
     [], "positive", 0.35, "global"),
    ("n12", "Reuters Business",
     "Gold near record as investors seek safety",
     "https://www.reuters.com/", "2026-09-16 07:15",
     "Safe-haven demand supports bullion.",
     [], "neutral", 0.0, "global"),
]


def sample_news() -> list[dict]:
    return [
        {
            "id": i, "source": src, "title": t, "url": u, "published": p,
            "summary": s, "tickers": tk, "sentiment": sent,
            "sentiment_score": sc, "category": cat,
        }
        for (i, src, t, u, p, s, tk, sent, sc, cat) in _ROWS
    ]
