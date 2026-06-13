from fastapi import APIRouter, Body, Request

from app.agents import expense_agent, rag_agent, router as routing_agent
from app.core.templates import templates
from app.db.session import SessionLocal
from app.models import Chat
from app.services.call_llm import call_llm
from app.utils.auth import get_current_user


router = APIRouter()


@router.post("/chat")
def chat_api(request: Request, data: dict = Body(...)):
    message = data.get("message", "")
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

        chat = Chat(
            user_message=message,
            bot_reply=reply,
            user=user
        )

        db = SessionLocal()
        db.add(chat)
        db.commit()
        db.close()

        return {"reply": reply}

    except Exception as e:
        print("ERROR:", str(e))
        return {"reply": "AI not available, try simple queries."}


@router.get("/chat")
def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})


@router.get("/chat-history")
def get_chat_history(request: Request):
    user = get_current_user(request)

    db = SessionLocal()
    chats = db.query(Chat).filter(Chat.user == user).order_by(Chat.id).all()
    db.close()

    return [
        {"user_message": c.user_message, "bot_reply": c.bot_reply}
        for c in chats
    ]


@router.get("/clear-chat")
def clear_chat(request: Request):
    user = get_current_user(request)

    db = SessionLocal()
    db.query(Chat).filter(Chat.user == user).delete()
    db.commit()
    db.close()

    return {"message": "Cleared"}
