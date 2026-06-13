from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes.auth import router as auth_router
from app.api.routes.chat import router as chat_router
from app.api.routes.documents import router as documents_router
from app.api.routes.finance import router as finance_router
from app.api.routes.home import router as home_router
from app.api.routes.news import router as news_router
from app.db.session import Base, engine
from app.utils.auth import get_current_user


load_dotenv()

app = FastAPI()
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(finance_router)
app.include_router(home_router)
app.include_router(news_router)
Base.metadata.create_all(bind=engine)

app.mount("/data", StaticFiles(directory="data"), name="data")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    public_paths = ["/login", "/signup", "/create-user", "/static", "/data", "/docs", "/openapi.json"]

    if any(request.url.path.startswith(path) for path in public_paths):
        return await call_next(request)

    user = get_current_user(request)

    if not user or user == "None":
        if request.url.path.startswith("/chat") or request.url.path.startswith("/api"):
            return JSONResponse({"error": "Unauthorized"}, status_code=401)

        return RedirectResponse(url="/login")

    return await call_next(request)
