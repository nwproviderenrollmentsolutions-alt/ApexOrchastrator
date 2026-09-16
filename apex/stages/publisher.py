"""Publishing fan-out: pushes an approved QCResult to TikTok/Reels and YouTube Shorts.

Mocked — swap `publish()` for real platform upload APIs (e.g. TikTok
Content Posting API, YouTube Data API) once credentials are available.
"""

from __future__ import annotations

import random

from ..models import Platform, PublishResult, QCResult


class Publisher:
    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)

    def publish(self, qc_result: QCResult, platforms: list[Platform] | None = None) -> list[PublishResult]:
        if not qc_result.approved:
            raise ValueError("Refusing to publish a package that failed Quality Control")

        targets = platforms or [qc_result.package.strategy.target_platform]
        results = []
        for platform in targets:
            post_id = self._rng.randint(10**8, 10**9)
            results.append(
                PublishResult(
                    qc_result=qc_result,
                    platform=platform,
                    post_url=f"https://{platform.value}.example/post/{post_id}",
                )
            )
        return results
