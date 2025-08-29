from pathlib import Path


def test_precommit_config_exists():
    root = Path(__file__).resolve().parents[3]
    assert root.joinpath(".pre-commit-config.yaml").exists()
