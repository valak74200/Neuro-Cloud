from pathlib import Path

def test_docker_compose_exists():
    assert Path(__file__).resolve().parents[3].joinpath('docker-compose.yml').exists()
