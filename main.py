# Load necessary libraries
from unittest import result
from fastapi import FastAPI, Request, Form, Body, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from database import SessionLocal
from models import Expense, Document, Chat, User
from database import engine, Base
from collections import defaultdict

# for file uploads (Document management)

import shutil
import os

# Initialize FastAPI app and database
app = FastAPI()
templates = Jinja2Templates(directory="templates")
Base.metadata.create_all(bind=engine)

app.mount("/data", StaticFiles(directory="data"), name="data")

def get_current_user(request: Request):
    return request.cookies.get("user")


#home route
@app.get("/")
def home(request: Request):
    # user = get_current_user(request)

    # if not user:
    #     return RedirectResponse(url="/login")

    return templates.TemplateResponse("index.html", {"request": request})



#finance management routes
@app.get("/finances")
def finance(request: Request, month: str = None):
    db = SessionLocal()
    user = request.cookies.get("user")
    if month:
        expenses = db.query(Expense).filter(Expense.date.startswith(month), Expense.user == user).all()
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
    user = request.cookies.get("user")
    expense = Expense(
        amount=amount,
        category=category,
        note=note,
        date=date,
        user = user
    )

    db.add(expense)
    db.commit()
    db.close()

    return RedirectResponse(url="/finances", status_code=303)

@app.get("/finances/delete/{id}")
def delete_expense(id: int):
    db = SessionLocal()
    expense = db.query(Expense).get(id)
    db.delete(expense)
    db.commit()
    db.close()

    return RedirectResponse(url="/finances/", status_code=303)

@app.get("/finances/edit/{id}")
def edit_page(request: Request, id: int):
    db = SessionLocal()
    expense = db.query(Expense).get(id)
    db.close()

    return templates.TemplateResponse(
        "finances_edit.html",
        {"request": request, "expense": expense}
    )


@app.post("/finances/update/{id}")
def update_expense(
    id: int,
    amount: float = Form(...),
    category: str = Form(...),
    note: str = Form(""),
    date: str = Form(...)
):
    db = SessionLocal()
    expense = db.query(Expense).get(id)

    expense.amount = amount
    expense.category = category
    expense.note = note
    expense.date = date

    db.commit()
    db.close()

    return RedirectResponse(url="/finances", status_code=303)



#document management routes
@app.get("/documents")
def documents(request: Request):
    db = SessionLocal()
    docs = db.query(Document).all()
    db.close()

    return templates.TemplateResponse(
        "documents.html",
        {"request": request, "docs": docs}
    )



@app.post("/documents/upload")
def upload_document(file: UploadFile = File(...)):
    file_location = f"data/documents/{file.filename}"

    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    db = SessionLocal()
    doc = Document(
        name=file.filename,
        file_path=file_location,
        uploaded_date="today"
    )
    db.add(doc)
    db.commit()
    db.close()

    return RedirectResponse(url="/documents", status_code=303)



@app.get("/documents/delete/{id}")
def delete_document(id: int):
    db = SessionLocal()
    doc = db.get(Document, id)

    # delete file from folder
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    db.delete(doc)
    db.commit()
    db.close()

    return RedirectResponse(url="/documents", status_code=303)



# news routes
import requests

@app.get("/news")
def news(request: Request):
    api_key = os.environ.get("NEWS_TOKEN")
    # "58eea8fde7024a45ba0952d99b0164ee"

    url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={api_key}"

    response = requests.get(url)
    data = response.json()
    print(data)
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

    db = SessionLocal()
    user = request.cookies.get("user")
    print(user)
    expenses = db.query(Expense).filter(Expense.user == user).all()
    db.close()

    # simple fallback (important)
    if "total" in message.lower():
        total = sum(e.amount for e in expenses)
        return {"reply": f"Your total spending is ₹{total}"}

    # prepare context
    expense_text = "\n".join(
        [f"{e.category} - ₹{e.amount} on {e.date}" for e in expenses]
    )

    prompt = f"""
You are a personal finance assistant.

User data:
{expense_text}

User question:
{message}

Answer clearly.
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

        user = request.cookies.get("user")

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
    user = request.cookies.get("user")

    db = SessionLocal()
    chats = db.query(Chat).filter(Chat.user == user).order_by(Chat.id).all()
    db.close()

    return chats

@app.get("/clear-chat")
def clear_chat():
    db = SessionLocal()
    db.query(Chat).delete()
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

    if user and user.password == password:
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(key="user", value=username)
        return response

    return {"message": "Invalid credentials"}


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