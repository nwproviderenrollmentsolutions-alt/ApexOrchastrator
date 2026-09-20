from types import SimpleNamespace

from apex_orchestrator import doctor


def test_check_packages_all_real_deps_importable():
    console = SimpleNamespace(print=lambda *a, **k: None)
    assert doctor._check_packages(console) is True


def test_check_packages_reports_missing_module():
    console = SimpleNamespace(print=lambda *a, **k: None)
    fake_packages = [("this_module_does_not_exist_xyz", "nothing")]
    original = doctor.REQUIRED_PACKAGES
    doctor.REQUIRED_PACKAGES = fake_packages
    try:
        assert doctor._check_packages(console) is False
    finally:
        doctor.REQUIRED_PACKAGES = original


def test_check_runs_dir_writable(tmp_path, monkeypatch):
    console = SimpleNamespace(print=lambda *a, **k: None)
    monkeypatch.setattr(doctor, "CONFIG", SimpleNamespace(runs_dir=str(tmp_path / "runs")))
    assert doctor._check_runs_dir(console) is True
    assert (tmp_path / "runs").exists()


def test_run_doctor_returns_true_when_ffmpeg_and_packages_present(tmp_path, monkeypatch):
    monkeypatch.setattr(
        doctor,
        "CONFIG",
        SimpleNamespace(
            runs_dir=str(tmp_path / "runs"),
            integration_summary=lambda: {"llm (Groq)": False},
        ),
    )
    monkeypatch.setattr(doctor.shutil, "which", lambda name: "/usr/bin/ffmpeg")
    assert doctor.run_doctor() is True


def test_run_doctor_returns_false_when_ffmpeg_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(
        doctor,
        "CONFIG",
        SimpleNamespace(
            runs_dir=str(tmp_path / "runs"),
            integration_summary=lambda: {"llm (Groq)": False},
        ),
    )
    monkeypatch.setattr(doctor.shutil, "which", lambda name: None)
    assert doctor.run_doctor() is False
