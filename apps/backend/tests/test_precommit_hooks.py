from pathlib import Path

def test_precommit_config_exists():
    assert Path(__file__).resolve().parents[3].joinpath('.pre-commit-config.yaml').exists()
