# Load necessary libraries
from unittest import result
from fastapi import FastAPI, Request, Form, Body, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from database import SessionLocal
from models import Expense, Document, Chat, User, Investment
from database import engine, Base
from collections import defaultdict
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
load_dotenv()

from agents import expense_agent, rag_agent, router

# for file uploads (Document management)

import shutil
import os

# Initialize FastAPI app and database
app = FastAPI()
templates = Jinja2Templates(directory="templates")
Base.metadata.create_all(bind=engine)

app.mount("/data", StaticFiles(directory="data"), name="data")


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    public_paths = ["/login", "/signup", "/create-user", "/static", "/data", "/docs", "/openapi.json"]

    if any(request.url.path.startswith(path) for path in public_paths):
        return await call_next(request)

    user = get_current_user(request)

    if not user or user == "None":
        # API routes → return JSON
        if request.url.path.startswith("/chat") or request.url.path.startswith("/api"):
            return JSONResponse({"error": "Unauthorized"}, status_code=401)

        # UI routes → redirect
        return RedirectResponse(url="/login")

    return await call_next(request)

def get_current_user(request: Request):
    user = request.cookies.get("user")
    if not user or user == "None":
        return None
    return user


#home route
@app.get("/")
def home(request: Request):
    user = get_current_user(request)

    if not user:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse("index.html", {"request": request})


from sqlalchemy import extract

#finance management routes
@app.get("/finances")
def finance(request: Request, month: str = None):
    db = SessionLocal()
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")
    if month:
        try:
            year, month_num = map(int, month.split("-"))
        except:
            return RedirectResponse("/finances")

        expenses = db.query(Expense).filter(
            extract("year", Expense.date) == year,
            extract("month", Expense.date) == month_num,
            Expense.user == user
        ).all()
    else:
        expenses = db.query(Expense).filter(Expense.user == user).all()
    total = sum(e.amount for e in expenses)
    category_totals = defaultdict(float)
    for e in expenses:
        category_totals[e.category] += e.amount  
    db.close()
    return templates.TemplateResponse(
        "finances.html",
        {"request": request, "expenses": expenses, "total": total, "category_totals": dict(category_totals)}
    )

  

@app.post("/finances/add")
def add_expense(
    request: Request,
    amount: float = Form(...),
    category: str = Form(...),
    note: str = Form(""),
    date: str = Form(...)
):
    db = SessionLocal()
    user = get_current_user(request)

    parsed_date = datetime.strptime(date, "%Y-%m-%d").date()

    expense = Expense(
        amount=amount,
        category=category,
        note=note,
        date=parsed_date,
        user=user
    )

    db.add(expense)
    db.commit()
    db.close()

    return RedirectResponse(url="/finances", status_code=303)

@app.get("/finances/delete/{id}")
def delete_expense(request: Request,id: int):
    db = SessionLocal()
    user = get_current_user(request)
    expense = db.query(Expense).filter(
    Expense.id == id,
    Expense.user == user
).first()
    if not expense:
        db.close()
        return RedirectResponse("/finances")
    db.delete(expense)
    db.commit()
    db.close()

    return RedirectResponse(url="/finances/", status_code=303)

@app.get("/finances/edit/{id}")
def edit_page(request: Request, id: int):
    db = SessionLocal()
    user = get_current_user(request)
    expense = db.query(Expense).filter(
    Expense.id == id,
    Expense.user == user
).first()
    db.close()

    return templates.TemplateResponse(
        "finances_edit.html",
        {"request": request, "expense": expense}
    )


@app.post("/finances/update/{id}")
def update_expense(
    request: Request,
    id: int,
    amount: float = Form(...),
    category: str = Form(...),
    note: str = Form(""),
    date: str = Form(...)
):
    db = SessionLocal()
    user = get_current_user(request)
    expense = db.query(Expense).filter(
    Expense.id == id,
    Expense.user == user
).first()

    expense.amount = amount
    expense.category = category
    expense.note = note
    parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
    expense.date = parsed_date


    db.commit()
    db.close()

    return RedirectResponse(url="/finances", status_code=303)



#document management routes
@app.get("/documents")
def documents(request: Request):
    db = SessionLocal()

    user = get_current_user(request)
    docs = db.query(Document).filter(Document.user == user).all()
    db.close()

    return templates.TemplateResponse(
        "documents.html",
        {"request": request, "docs": docs}
    )


from rag import process_document, query_rag

@app.post("/documents/upload")
def upload_document(request: Request,file: UploadFile = File(...)):
    file_location = f"data/documents/{file.filename}"

    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    user = get_current_user(request)

    # Process document safely for RAG
    try:
        process_document(file_location)
    except Exception as e:
        print("PDF processing failed:", str(e))

    db = SessionLocal()
    doc = Document(
        name=file.filename,
        file_path=file_location,
        uploaded_date=datetime.now(timezone.utc).date(),
        user=user
    )
    db.add(doc)
    db.commit()
    db.close()

    return RedirectResponse(url="/documents", status_code=303)



@app.get("/documents/delete/{id}")
def delete_document(request: Request,id: int):
    db = SessionLocal()
    user = get_current_user(request)
    doc = db.query(Document).filter(
    Document.id == id,
    Document.user == user
    ).first()

    if not doc:
        db.close()
        return RedirectResponse("/documents")

    # delete file from folder
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    db.delete(doc)
    db.commit()
    db.close()

    return RedirectResponse(url="/documents", status_code=303)


@app.get("/investments")
def investments_dashboard(request: Request):
    db = SessionLocal()
    user = get_current_user(request)

    if not user:
        return RedirectResponse("/login")

    investments = db.query(Investment).filter(Investment.user == user).all()

    from collections import defaultdict

    # Net worth trend
    monthly_networth = defaultdict(float)
    for i in investments:
        key = i.month.strftime("%Y-%m")
        monthly_networth[key] += i.balance

    # Type distribution
    type_totals = defaultdict(float)
    for i in investments:
        type_totals[i.type] += i.balance

    # Volatility split
    volatility_totals = defaultdict(float)
    for i in investments:
        volatility_totals[i.volatility] += i.balance

    # Top accounts
    top_accounts = sorted(investments, key=lambda x: x.balance, reverse=True)[:5]

    db.close()

    return templates.TemplateResponse(
        "investments.html",
        {
            "request": request,
            "monthly_networth": dict(monthly_networth),
            "type_totals": dict(type_totals),
            "volatility_totals": dict(volatility_totals),
            "top_accounts": top_accounts
        }
    )


# news routes
import requests

@app.get("/news")
def news(request: Request):
    api_key = os.environ.get("NEWS_TOKEN")
    # "58eea8fde7024a45ba0952d99b0164ee"
    # Compute yesterday's date dynamically (YYYY-MM-DD)
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    url = f"https://newsapi.org/v2/everything?q=India&from={yesterday}&sortBy=popularity&apiKey={api_key}"

    response = requests.get(url)
    data = response.json()
    
    articles = data.get("articles", [])[:10]
    
    return templates.TemplateResponse(
        "news.html",
        {"request": request, "articles": articles}
    )

from openai import OpenAI
import os


client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key = os.environ.get("HF_TOKEN"),
)




@app.post("/chat")
def chat_api(request: Request, data: dict = Body(...)):
    message = data.get("message", "")
    user = get_current_user(request)
    # RAG retrieval
    # Step 1: Route the query
    decision = router.route(client, message)

    print("Routing decision:", decision)  # debug

    # Step 2: Call correct agent
    if "expense" in decision:
        prompt = expense_agent.run(user, message)
    elif "document" in decision:
        prompt = rag_agent.run(message)
    else:
        # general fallback (no RAG, no DB)
        prompt = f"""
You are a helpful assistant.
Answer the question normally:

Question:
{message}
"""
    try:
        completion = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3-8B-Instruct",   # ✅ IMPORTANT CHANGE
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150
        )

        reply = completion.choices[0].message.content

        user = get_current_user(request)

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
    

@app.get("/chat")
def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})


@app.get("/chat-history")
def get_chat_history(request: Request):
    user = get_current_user(request)

    db = SessionLocal()
    chats = db.query(Chat).filter(Chat.user == user).order_by(Chat.id).all()
    db.close()

    return [
        {"user_message": c.user_message, "bot_reply": c.bot_reply}
        for c in chats
    ]

@app.get("/clear-chat")
def clear_chat(request: Request):
    user = get_current_user(request)

    db = SessionLocal()
    db.query(Chat).filter(Chat.user == user).delete()
    db.commit()
    db.close()

    return {"message": "Cleared"}

@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    db.close()

    if user is None:
        return {"message": "User does not exist"}

    if user.password != password:
        return {"message": "Incorrect password"}

    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="user", value=user.username)
    return response


@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("user")
    return response

@app.get("/create-user")
def create_user():
    db = SessionLocal()

    user = User(username="admin", password="1234")
    db.add(user)
    db.commit()
    db.close()

    return {"message": "User created"}

@app.get("/signup")
def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@app.post("/signup")
def signup(username: str = Form(...), password: str = Form(...)):
    db = SessionLocal()

    # check if user exists
    existing_user = db.query(User).filter(User.username == username).first()

    if existing_user:
        db.close()
        return {"message": "Username already exists"}

    # create new user
    user = User(username=username, password=password)
    db.add(user)
    db.commit()
    db.close()

    return RedirectResponse(url="/login", status_code=303)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", reload=True)