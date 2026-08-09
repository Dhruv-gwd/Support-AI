from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.models.database import (
    SessionLocal,
    User,
    Conversation,
    Message,
    Tenant,
    Document,
)
from app.models.schemas import (
    Token,
    UserCreate,
    UserResponse,
    ConversationResponse,
    MessageResponse,
    LoginRequest,
)
from app.services.auth_service import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
)
from app.config import SECRET_KEY, ALGORITHM, RATE_LIMIT_PER_MINUTE
from app.limiter import limiter

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login", auto_error=False
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
        )
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    return user


async def get_current_user_optional(
    token: str = Depends(oauth2_scheme_optional), db: Session = Depends(get_db)
):
    if not token:
        return None
    payload = decode_access_token(token)
    if payload is None:
        return None
    user_id = payload.get("sub")
    if user_id is None:
        return None
    return db.query(User).filter(User.id == user_id).first()


def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    return current_user


@router.post(
    "/auth/register", response_model=Token, status_code=status.HTTP_201_CREATED
)
@limiter.limit(f"{RATE_LIMIT_PER_MINUTE}/minute")
def register(request: Request, user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    tenant = Tenant(
        name=user_in.full_name or "Default", slug=user_in.email.split("@")[0]
    )
    db.add(tenant)
    db.flush()

    # The first user registered into a tenant becomes that tenant's admin.
    # Without this, a fresh signup has no route to the admin panel at all —
    # promotion currently requires shell access to run make_admin.py.
    existing_users_in_tenant = (
        db.query(User).filter(User.tenant_id == tenant.id).count()
    )
    role = "admin" if existing_users_in_tenant == 0 else "user"

    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=role,
        tenant_id=tenant.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/auth/login", response_model=Token)
@limiter.limit(f"{RATE_LIMIT_PER_MINUTE}/minute")
def login(request: Request, credentials: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/auth/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/auth/conversations", response_model=list[ConversationResponse])
def list_conversations(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )


@router.post(
    "/auth/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    conv = Conversation(user_id=current_user.id, title="New Conversation")
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


@router.get(
    "/auth/conversations/{conversation_id}/messages",
    response_model=list[MessageResponse],
)
def get_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id, Conversation.user_id == current_user.id
        )
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .all()
    )


@router.delete(
    "/auth/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id, Conversation.user_id == current_user.id
        )
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(conv)
    db.commit()
    return None


@router.get("/admin/users", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db), current_user: User = Depends(require_admin)
):
    return db.query(User).filter(User.tenant_id == current_user.tenant_id).all()


@router.get("/admin/documents", response_model=list[dict])
def list_tenant_documents(
    db: Session = Depends(get_db), current_user: User = Depends(require_admin)
):
    docs = db.query(Document).filter(Document.tenant_id == current_user.tenant_id).all()
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "uploaded_by": d.uploaded_by,
            "created_at": d.created_at,
        }
        for d in docs
    ]
