import os
from datetime import datetime, timedelta, timezone

import requests
from fastapi import APIRouter, Request

from app.core.templates import templates


router = APIRouter()

@router.get("/news")
def news(request: Request):
    api_key = os.environ.get("NEWS_TOKEN")
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    url = f"https://newsapi.org/v2/everything?q=India&from={yesterday}&sortBy=popularity&apiKey={api_key}"

    response = requests.get(url)
    data = response.json()

    articles = data.get("articles", [])[:10]

    return templates.TemplateResponse(
        "news.html",
        {"request": request, "articles": articles}
    )
