"""Google Trends signal for a niche, via pytrends (free, no API key).

pytrends scrapes Google Trends' public frontend rather than calling an
official API, so it has no auth but is also not guaranteed stable -- Google
can rate-limit or change the response shape without notice. Every failure
mode (network, rate limit, empty data) falls back to a neutral offline
signal instead of raising, matching the rest of this pipeline's philosophy.
"""

from __future__ import annotations

from apex_orchestrator.contracts import TrendSignal


def _offline_fallback(niche: str) -> TrendSignal:
    return TrendSignal(
        niche=niche,
        source="offline_fallback",
        velocity_score=0.5,
        sample_titles=[niche],
    )


def fetch_google_trends_signal(niche: str, timeframe: str = "now 7-d") -> TrendSignal:
    try:
        from pytrends.request import TrendReq

        pytrends = TrendReq(hl="en-US", tz=360)
        pytrends.build_payload([niche], timeframe=timeframe)

        interest = pytrends.interest_over_time()
        velocity = 0.5
        if not interest.empty and niche in interest.columns:
            series = interest[niche]
            baseline = series.iloc[: max(1, len(series) // 2)].mean()
            recent = series.iloc[max(1, len(series) // 2) :].mean()
            if baseline > 0:
                velocity = max(0.0, min(1.0, recent / baseline / 2))

        sample_titles: list[str] = []
        related = pytrends.related_queries().get(niche, {})
        rising = related.get("rising")
        if rising is not None and not rising.empty:
            sample_titles = rising["query"].head(5).tolist()

        return TrendSignal(
            niche=niche,
            source="google_trends",
            velocity_score=velocity,
            sample_titles=sample_titles or [niche],
        )
    except Exception:
        return _offline_fallback(niche)
