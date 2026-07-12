from fastapi import APIRouter, Body, Request

from app.agents import expense_agent, rag_agent, router as routing_agent
from app.core.templates import templates
from app.db.session import SessionLocal
from app.models import Chat, Conversation
from app.services.call_llm import call_llm
from app.utils.auth import get_current_user


router = APIRouter()


def make_title(message: str) -> str:
    title = " ".join(message.strip().split())
    if not title:
        return "New conversation"

    return title[:45] + ("..." if len(title) > 45 else "")


def get_or_create_conversation(db, user: str, conversation_id, message: str):
    if conversation_id:
        conversation = (
            db.query(Conversation)
            .filter(Conversation.id == conversation_id, Conversation.user == user)
            .first()
        )
        if conversation:
            return conversation

    conversation = Conversation(title=make_title(message), user=user)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def move_legacy_chats_into_conversation(db, user: str):
    legacy_chat = (
        db.query(Chat)
        .filter(Chat.user == user, Chat.conversation_id.is_(None))
        .order_by(Chat.id)
        .first()
    )

    if not legacy_chat:
        return

    conversation = Conversation(title="Previous conversation", user=user)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    (
        db.query(Chat)
        .filter(Chat.user == user, Chat.conversation_id.is_(None))
        .update({"conversation_id": conversation.id})
    )
    db.commit()


@router.post("/chat")
def chat_api(request: Request, data: dict = Body(...)):
    message = data.get("message", "")
    conversation_id = data.get("conversation_id")
    user = get_current_user(request)

    decision = routing_agent.route(message)

    print("Routing decision:", decision)

    if "expense" in decision:
        prompt = expense_agent.run(user, message)
    elif "document" in decision:
        prompt = rag_agent.run(message)
    else:
        prompt = f"""
You are a helpful assistant.
Answer the question normally:

Question:
{message}
"""

    try:
        reply = call_llm(prompt)

        db = SessionLocal()
        conversation = get_or_create_conversation(db, user, conversation_id, message)
        saved_conversation_id = conversation.id
        saved_conversation_title = conversation.title

        chat = Chat(
            conversation_id=saved_conversation_id,
            user_message=message,
            bot_reply=reply,
            user=user
        )

        db.add(chat)
        db.commit()
        db.close()

        return {
            "reply": reply,
            "conversation_id": saved_conversation_id,
            "conversation_title": saved_conversation_title
        }

    except Exception as e:
        print("ERROR:", str(e))
        return {"reply": "AI not available, try simple queries."}


@router.get("/chat")
def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})


@router.get("/chat-history")
def get_chat_history(request: Request, conversation_id: int = None):
    user = get_current_user(request)

    db = SessionLocal()
    query = db.query(Chat).filter(Chat.user == user)
    if conversation_id:
        query = query.filter(Chat.conversation_id == conversation_id)
    else:
        query = query.filter(Chat.conversation_id.is_(None))

    chats = query.order_by(Chat.id).all()
    db.close()

    return [
        {"user_message": c.user_message, "bot_reply": c.bot_reply}
        for c in chats
    ]


@router.get("/chat-conversations")
def get_conversations(request: Request):
    user = get_current_user(request)

    db = SessionLocal()
    move_legacy_chats_into_conversation(db, user)
    conversations = (
        db.query(Conversation)
        .filter(Conversation.user == user)
        .order_by(Conversation.created_at.desc(), Conversation.id.desc())
        .all()
    )
    conversation_data = [
        {
            "id": conversation.id,
            "title": conversation.title,
            "created_at": conversation.created_at.isoformat() if conversation.created_at else None
        }
        for conversation in conversations
    ]
    db.close()

    return conversation_data


@router.post("/chat-conversations")
def create_conversation(request: Request):
    user = get_current_user(request)

    db = SessionLocal()
    conversation = Conversation(title="New conversation", user=user)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    conversation_data = {"id": conversation.id, "title": conversation.title}
    db.close()

    return conversation_data


@router.delete("/chat-conversations/{conversation_id}")
def delete_conversation(request: Request, conversation_id: int):
    user = get_current_user(request)

    db = SessionLocal()
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user == user)
        .first()
    )

    if conversation:
        db.query(Chat).filter(Chat.conversation_id == conversation.id, Chat.user == user).delete()
        db.delete(conversation)
        db.commit()

    db.close()
    return {"message": "Deleted"}


@router.get("/clear-chat")
def clear_chat(request: Request, conversation_id: int = None):
    user = get_current_user(request)

    db = SessionLocal()
    query = db.query(Chat).filter(Chat.user == user)
    if conversation_id:
        query = query.filter(Chat.conversation_id == conversation_id)
    query.delete()
    db.commit()
    db.close()

    return {"message": "Cleared"}
