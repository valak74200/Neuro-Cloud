from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_license_exists_and_not_empty():
    p = ROOT / "LICENSE"
    assert p.exists()
    assert p.read_text(encoding="utf-8").strip()


def test_contributing_exists_and_not_empty():
    p = ROOT / "CONTRIBUTING.md"
    assert p.exists()
    assert p.read_text(encoding="utf-8").strip()


def test_env_example_exists():
    p = ROOT / ".env.example"
    assert p.exists()
