from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.crud import chat_history as crud_chat_history
from app.models.user import User
from app.schemas.chat_history import ChatHistory, ChatHistoryCreate, ChatHistoryUpdate

router = APIRouter()


@router.get("/", response_model=List[ChatHistory])
def read_chat_history(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve chat history
    """
    chat_history = crud_chat_history.get_chat_history(db, skip=skip, limit=limit)
    return chat_history


@router.post("/", response_model=ChatHistory)
def create_chat_message(
    *,
    db: Session = Depends(get_db),
    chat_message_in: ChatHistoryCreate,
    current_user: User = Depends(get_current_user),
):
    """
    Create new chat message
    """
    chat_message = crud_chat_history.create_chat_message(db, chat_message_in)
    return chat_message


@router.get("/{chat_id}", response_model=ChatHistory)
def read_chat_message(
    *,
    db: Session = Depends(get_db),
    chat_id: int,
    current_user: User = Depends(get_current_user),
):
    """
    Get chat message by ID
    """
    chat_message = crud_chat_history.get_chat_message(db, chat_id)
    if not chat_message:
        raise HTTPException(status_code=404, detail="Chat message not found")
    return chat_message


@router.put("/{chat_id}", response_model=ChatHistory)
def update_chat_message(
    *,
    db: Session = Depends(get_db),
    chat_id: int,
    chat_message_in: ChatHistoryUpdate,
    current_user: User = Depends(get_current_user),
):
    """
    Update chat message
    """
    chat_message = crud_chat_history.update_chat_message(db, chat_id, chat_message_in)
    if not chat_message:
        raise HTTPException(status_code=404, detail="Chat message not found")
    return chat_message


@router.get("/call/{call_id}", response_model=List[ChatHistory])
def read_chat_history_by_call(
    *,
    db: Session = Depends(get_db),
    call_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
):
    """
    Get chat history for a specific call session
    """
    chat_history = crud_chat_history.get_chat_history_by_call(db, call_id, skip=skip, limit=limit)
    return chat_history


@router.get("/call/{call_id}/recent", response_model=List[ChatHistory])
def read_recent_messages(
    *,
    db: Session = Depends(get_db),
    call_id: int,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
):
    """
    Get recent messages for a call session
    """
    chat_history = crud_chat_history.get_recent_messages(db, call_id, limit=limit)
    return chat_history


@router.delete("/{chat_id}")
def delete_chat_message(
    *,
    db: Session = Depends(get_db),
    chat_id: int,
    current_user: User = Depends(get_current_user),
):
    """
    Delete chat message
    """
    deleted = crud_chat_history.delete_chat_message(db, chat_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Chat message not found")
    return {"message": "Chat message deleted successfully"} 