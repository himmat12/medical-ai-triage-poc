from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.models.chat_history import ChatHistory
from app.schemas.chat_history import ChatHistoryCreate, ChatHistoryUpdate


def get_chat_message(db: Session, chat_id: int) -> Optional[ChatHistory]:
    return db.query(ChatHistory).filter(ChatHistory.chat_id == chat_id).first()


def get_chat_history(db: Session, skip: int = 0, limit: int = 100) -> List[ChatHistory]:
    return db.query(ChatHistory).offset(skip).limit(limit).all()


def get_chat_history_by_call(db: Session, call_id: int, skip: int = 0, limit: int = 100) -> List[ChatHistory]:
    """Get chat history for a specific call session, ordered by sequence"""
    return db.query(ChatHistory).filter(
        ChatHistory.call_id == call_id
    ).order_by(ChatHistory.message_sequence).offset(skip).limit(limit).all()


def get_next_message_sequence(db: Session, call_id: int) -> int:
    """Get the next message sequence number for a call session"""
    max_sequence = db.query(func.max(ChatHistory.message_sequence)).filter(
        ChatHistory.call_id == call_id
    ).scalar()
    return (max_sequence or 0) + 1


def create_chat_message(db: Session, chat_message: ChatHistoryCreate) -> ChatHistory:
    # Get next sequence number for this call
    next_sequence = get_next_message_sequence(db, chat_message.call_id)
    
    db_chat_message = ChatHistory(
        call_id=chat_message.call_id,
        speaker=chat_message.speaker,
        message_text=chat_message.message_text,
        message_sequence=next_sequence
    )
    db.add(db_chat_message)
    db.commit()
    db.refresh(db_chat_message)
    return db_chat_message


def update_chat_message(db: Session, chat_id: int, chat_message: ChatHistoryUpdate) -> Optional[ChatHistory]:
    db_chat_message = db.query(ChatHistory).filter(ChatHistory.chat_id == chat_id).first()
    if db_chat_message:
        update_data = chat_message.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_chat_message, field, value)
        db.commit()
        db.refresh(db_chat_message)
    return db_chat_message


def delete_chat_message(db: Session, chat_id: int) -> bool:
    db_chat_message = db.query(ChatHistory).filter(ChatHistory.chat_id == chat_id).first()
    if db_chat_message:
        db.delete(db_chat_message)
        db.commit()
        return True
    return False


def get_recent_messages(db: Session, call_id: int, limit: int = 10) -> List[ChatHistory]:
    """Get the most recent messages for a call session"""
    return db.query(ChatHistory).filter(
        ChatHistory.call_id == call_id
    ).order_by(desc(ChatHistory.message_sequence)).limit(limit).all() 