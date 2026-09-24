"""Picks a proven short-form structure and turns it into a ContentBrief.

This is the seam between "what's trending" (Viral Analyst AI) and "what we
actually script" (UGC Creator AI) -- it owns framework selection and the
product angle, everything else in the brief is passed through from the
caller's inputs.
"""

from __future__ import annotations

from apex_orchestrator.contracts import AnalysisReport, ContentBrief, ContentFramework

FRAMEWORK_LABELS = {
    "listicle": "Listicle",
    "myth_vs_fact": "Myth vs. Fact",
    "before_after_transformation": "Before/After Transformation",
    "problem_agitate_solve": "Problem-Agitate-Solve",
    "storytime": "Storytime",
    "tutorial": "Tutorial",
}


def select_framework(analysis: AnalysisReport, learned_framework: str | None = None) -> ContentFramework:
    """`learned_framework` is what the Learning Database says has actually
    performed best for this niche in past runs. When there's enough history
    to trust it, it overrides the Analyst's title-pattern guess -- that's
    the feedback loop from Performance Engine / Learning Database back into
    Content Strategist.
    """
    pattern = learned_framework or analysis.content_pattern
    label = FRAMEWORK_LABELS.get(pattern, "Problem-Agitate-Solve")
    angle = f"{label} format built around what's working in {analysis.niche!r} right now: {analysis.hook_pattern}"
    if learned_framework and learned_framework != analysis.content_pattern:
        angle += f" (learning database: {label} has outperformed for this niche)"
    return ContentFramework(framework=pattern, angle=angle)


def build_brief(
    brief_id: str,
    niche: str,
    analysis: AnalysisReport,
    product_name: str | None = None,
    cta: str | None = None,
    platforms: list[str] | None = None,
    key_claims: list[str] | None = None,
    disclosure_required: bool = False,
    max_duration_sec: int = 45,
    learned_framework: str | None = None,
) -> ContentBrief:
    framework = select_framework(analysis, learned_framework)
    angle = framework.angle
    if product_name:
        angle += f", featuring {product_name}"

    return ContentBrief(
        brief_id=brief_id,
        topic=niche,
        angle=angle,
        cta=cta or analysis.cta_style,
        key_claims=key_claims or [],
        target_platforms=platforms or ["youtube_shorts"],
        product_name=product_name,
        source_trend=analysis.hook_pattern,
        disclosure_required=disclosure_required,
        max_duration_sec=max_duration_sec,
    )
