from pathlib import Path


def test_docker_compose_exists():
    root = Path(__file__).resolve().parents[3]
    assert root.joinpath("docker-compose.yml").exists()
