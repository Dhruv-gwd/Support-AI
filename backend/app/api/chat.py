from fastapi import APIRouter, HTTPException, Depends
from fastapi import status
from sqlalchemy.orm import Session

from app.models.schemas import ChatRequest, ChatResponse
from app.services.rag_service import RagService
from app.services.gemini_service import GeminiServiceError
from app.services.embedding_service import EmbeddingServiceError
from app.models.database import SessionLocal, Message as DBMessage, Conversation, User
from app.api.auth import get_current_user

router = APIRouter()
rag_service = RagService()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        history = []
        conversation = None
        if request.conversation_id:
            conversation = (
                db.query(Conversation)
                .filter(
                    Conversation.id == request.conversation_id,
                    Conversation.user_id == current_user.id,
                )
                .first()
            )
            if not conversation:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
            msgs = db.query(DBMessage).filter(DBMessage.conversation_id == conversation.id).all()
            history = [{"role": m.role, "content": m.content} for m in msgs]

        answer, sources, images = rag_service.answer(
            request.message, history=history, tenant_id=current_user.tenant_id
        )

        conversation_id = request.conversation_id
        if not conversation_id:
            conversation = Conversation(user_id=current_user.id, title=request.message[:50])
            db.add(conversation)
            db.flush()
            conversation_id = conversation.id

        user_msg = DBMessage(
            conversation_id=conversation_id,
            role="user",
            content=request.message,
        )
        bot_msg = DBMessage(
            conversation_id=conversation_id,
            role="assistant",
            content=answer,
            sources=",".join(sources),
            images=",".join(images),
        )
        db.add(user_msg)
        db.add(bot_msg)
        db.commit()

        return ChatResponse(
            response=answer,
            sources=sources,
            images=images,
            conversation_id=conversation_id or 0,
        )
    except (GeminiServiceError, EmbeddingServiceError) as e:
        raise HTTPException(
            status_code=503,
            detail="AI service is temporarily unavailable. Please try again shortly.",
        ) from e
