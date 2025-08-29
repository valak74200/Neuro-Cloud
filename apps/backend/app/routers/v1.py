from app.schemas.memory import MemoryCreateRequest, MemoryResponse
from app.services.in_memory_memory_repo import InMemoryMemoryRepository
from app.services.save_memory import SaveMemoryService
from fastapi import APIRouter

api = APIRouter()


@api.post("/memories", response_model=MemoryResponse)
def create_memory(req: MemoryCreateRequest) -> MemoryResponse:
    repo = InMemoryMemoryRepository()
    service = SaveMemoryService(memory_repository=repo)
    memory = service.save_memory(
        user_id=req.user_id, content=req.content, source=req.source
    )
    return MemoryResponse(
        id=memory.id,
        user_id=memory.user_id,
        content=memory.content,
        source=memory.source,
    )
