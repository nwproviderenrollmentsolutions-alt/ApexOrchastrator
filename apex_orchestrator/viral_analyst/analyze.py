"""Turns raw TrendSignals into an actionable AnalysisReport.

Scope note: this analyzes the *titles* surfaced by Viral Radar (search
terms, trending video titles), not full video content -- pulling per-video
hook/editing/pacing breakdowns would mean downloading and watching each
competitor video, which is a heavier future extension (see README). What's
here already drives real framework and hook decisions in Content
Strategist without needing any paid analysis API.
"""

from __future__ import annotations

import json
import re
from collections import Counter

from apex_orchestrator.contracts import AnalysisReport, TrendSignal
from apex_orchestrator.llm import LLMUnavailable, complete
from apex_orchestrator.quality_control.hook_score import HOOK_PATTERNS

SYSTEM_PROMPT = """You are a short-form content strategist. Given a niche \
and a sample of real trending/rising titles in it, infer what's currently \
working. Return strict JSON with keys: hook_pattern (short description of \
the dominant hook style), content_pattern (one of: listicle, myth_vs_fact, \
before_after_transformation, problem_agitate_solve, storytime, tutorial), \
editing_notes (short, concrete pacing/caption advice), cta_style (short \
description), predicted_comment_themes (array of 2-4 short strings)."""

_CONTENT_PATTERN_RULES = [
    (re.compile(r"^\s*\d+\b"), "listicle"),
    (re.compile(r"\bvs\b|\bmyth\b|\bfact\b|\btruth\b", re.I), "myth_vs_fact"),
    (re.compile(r"\bbefore\b.*\bafter\b|\btransform", re.I), "before_after_transformation"),
    (re.compile(r"\bhow to\b|\btutorial\b|\bguide\b", re.I), "tutorial"),
    (re.compile(r"\bstory\b|\bhappened\b|\bI (tried|did|found)\b", re.I), "storytime"),
]


def _dominant_hook_pattern(titles: list[str]) -> str:
    counts = Counter()
    for title in titles:
        for pattern, label in HOOK_PATTERNS.items():
            if re.search(pattern, title.lower()):
                counts[label] += 1
    if not counts:
        return "no strong pattern detected in current titles; lead with a number or question"
    return counts.most_common(1)[0][0]


def _dominant_content_pattern(titles: list[str]) -> str:
    counts = Counter()
    for title in titles:
        for pattern, label in _CONTENT_PATTERN_RULES:
            if pattern.search(title):
                counts[label] += 1
                break
    if not counts:
        return "problem_agitate_solve"
    return counts.most_common(1)[0][0]


def _heuristic_analysis(niche: str, titles: list[str]) -> AnalysisReport:
    return AnalysisReport(
        niche=niche,
        hook_pattern=_dominant_hook_pattern(titles),
        content_pattern=_dominant_content_pattern(titles),
        editing_notes="fast cuts under 3s per shot, bold on-screen captions synced to narration, no dead air in the first 2 seconds",
        cta_style="ask a direct question and invite a comment, or tease a follow-up part",
        predicted_comment_themes=[
            "relatable agreement ('this is so true')",
            "requests for more detail or a part 2",
            "skepticism challenging the claim",
        ],
        used_llm=False,
    )


def analyze_trends(niche: str, signals: list[TrendSignal]) -> AnalysisReport:
    titles = [t for s in signals for t in s.sample_titles]
    if not titles:
        titles = [niche]

    try:
        user_prompt = f"Niche: {niche}\nSample titles:\n" + "\n".join(f"- {t}" for t in titles)
        raw = complete(SYSTEM_PROMPT, user_prompt, json_mode=True, temperature=0.4)
        data = json.loads(raw)
        return AnalysisReport(
            niche=niche,
            hook_pattern=data["hook_pattern"],
            content_pattern=data["content_pattern"],
            editing_notes=data["editing_notes"],
            cta_style=data["cta_style"],
            predicted_comment_themes=list(data.get("predicted_comment_themes", [])),
            used_llm=True,
        )
    except (LLMUnavailable, KeyError, json.JSONDecodeError, Exception):
        return _heuristic_analysis(niche, titles)
