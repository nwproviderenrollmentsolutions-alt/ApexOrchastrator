from apex_orchestrator.contracts import PerformanceSnapshot
from apex_orchestrator.learning_database import store


def _snapshot(views: int, platform: str = "youtube_shorts") -> PerformanceSnapshot:
    return PerformanceSnapshot(platform=platform, remote_id="abc", views=views)


def test_leaderboard_empty_for_fresh_db(tmp_path):
    db_path = tmp_path / "learning.db"
    assert store.framework_leaderboard(db_path=db_path) == []
    assert store.best_framework_for_niche("budget travel", db_path=db_path) is None


def test_leaderboard_ranks_by_average_views(tmp_path):
    db_path = tmp_path / "learning.db"

    store.record_run("run1", "budget travel", "listicle", "brief1", db_path=db_path)
    store.record_performance("run1", [_snapshot(1000)], db_path=db_path)

    store.record_run("run2", "budget travel", "storytime", "brief2", db_path=db_path)
    store.record_performance("run2", [_snapshot(5000)], db_path=db_path)

    board = store.framework_leaderboard("budget travel", db_path=db_path)
    assert board[0][0] == "storytime"
    assert board[0][1] == 5000.0


def test_best_framework_requires_min_samples(tmp_path):
    db_path = tmp_path / "learning.db"

    store.record_run("run1", "budget travel", "listicle", "brief1", db_path=db_path)
    store.record_performance("run1", [_snapshot(9000)], db_path=db_path)

    # Only one data point for "listicle" -- shouldn't be trusted yet.
    assert store.best_framework_for_niche("budget travel", min_samples=2, db_path=db_path) is None

    store.record_run("run2", "budget travel", "listicle", "brief2", db_path=db_path)
    store.record_performance("run2", [_snapshot(8000)], db_path=db_path)

    assert store.best_framework_for_niche("budget travel", min_samples=2, db_path=db_path) == "listicle"


def test_leaderboard_scoped_by_niche(tmp_path):
    db_path = tmp_path / "learning.db"

    store.record_run("run1", "budget travel", "listicle", "brief1", db_path=db_path)
    store.record_performance("run1", [_snapshot(1000)], db_path=db_path)

    store.record_run("run2", "personal finance", "storytime", "brief2", db_path=db_path)
    store.record_performance("run2", [_snapshot(9000)], db_path=db_path)

    board = store.framework_leaderboard("budget travel", db_path=db_path)
    assert [row[0] for row in board] == ["listicle"]


def test_niche_average_views_none_for_unknown_niche(tmp_path):
    db_path = tmp_path / "learning.db"
    assert store.niche_average_views("budget travel", db_path=db_path) is None


def test_niche_average_views_averages_across_frameworks(tmp_path):
    db_path = tmp_path / "learning.db"

    store.record_run("run1", "budget travel", "listicle", "brief1", db_path=db_path)
    store.record_performance("run1", [_snapshot(1000)], db_path=db_path)

    store.record_run("run2", "budget travel", "storytime", "brief2", db_path=db_path)
    store.record_performance("run2", [_snapshot(3000)], db_path=db_path)

    assert store.niche_average_views("budget travel", db_path=db_path) == 2000.0


def test_niche_average_views_scoped_by_niche(tmp_path):
    db_path = tmp_path / "learning.db"

    store.record_run("run1", "budget travel", "listicle", "brief1", db_path=db_path)
    store.record_performance("run1", [_snapshot(1000)], db_path=db_path)

    store.record_run("run2", "personal finance", "storytime", "brief2", db_path=db_path)
    store.record_performance("run2", [_snapshot(9000)], db_path=db_path)

    assert store.niche_average_views("budget travel", db_path=db_path) == 1000.0
