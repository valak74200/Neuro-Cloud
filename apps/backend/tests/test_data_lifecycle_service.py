from app.domain.entities.memory import Memory
from app.services.data_lifecycle_service import DataLifecycleService, PurgePolicy
from app.services.in_memory_memory_repo import InMemoryMemoryRepository


def test_export_and_purge_user_memories() -> None:
    repo = InMemoryMemoryRepository()
    svc = DataLifecycleService(repo)

    # Seed
    repo.save(Memory(id="m1", user_id="u1", content="A", source="manual"))
    repo.save(Memory(id="m2", user_id="u1", content="B", source="manual"))
    repo.save(Memory(id="m3", user_id="u2", content="C", source="manual"))

    exported = svc.export_user_memories("u1")
    assert {m.id for m in exported} == {"m1", "m2"}

    deleted = svc.purge_user_memories("u1", PurgePolicy(by_user=True))
    assert deleted == 2
    assert {m.id for m in repo.list_by_user("u1")} == set()
