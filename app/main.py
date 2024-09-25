from fastapi import FastAPI, Request, Depends, HTTPException, Cookie, Response
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2AuthorizationCodeBearer
from httpx import AsyncClient
from sqlalchemy.orm import Session
from models import User, SessionLocal
import os
import secrets
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sqlite3
from fastapi.responses import JSONResponse

load_dotenv()

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="https://discord.com/api/oauth2/authorize",
    tokenUrl="https://discord.com/api/oauth2/token"
)

CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")

state_storage = {}
user_sessions = {}


# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
async def home(request: Request, session: str = Cookie(None), db: Session = Depends(get_db)):
    if session and session in user_sessions:
        discord_id = user_sessions[session]['discord_id']
        user = db.query(User).filter(User.discord_id == discord_id).first()
        username = user_sessions[session]['username'] if user else "guest"
        return templates.TemplateResponse(request=request, name="index.html", context={"username": username.lower()})

    return templates.TemplateResponse(request=request, name="index.html", context={"username": "guest"})


@app.get("/login")
async def login():
    state = secrets.token_hex(16)
    state_storage[state] = True
    redirect_url = (
        f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}&response_type=code&scope=identify&state={state}"
    )
    return RedirectResponse(redirect_url)


@app.get("/auth/callback")
async def auth_callback(code: str, state: str, db: Session = Depends(get_db)):
    if state not in state_storage:
        raise HTTPException(status_code=403, detail="Invalid state parameter")

    async with AsyncClient() as client:
        token_response = await client.post(
            "https://discord.com/api/oauth2/token",
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI,
            },
        )

        if token_response.status_code != 200:
            raise HTTPException(status_code=token_response.status_code, detail="Failed to get access token")

        token_data = token_response.json()
        access_token = token_data['access_token']

        user_response = await client.get(
            "https://discord.com/api/users/@me",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if user_response.status_code != 200:
            raise HTTPException(status_code=user_response.status_code, detail="Failed to fetch user data")

        user_data = user_response.json()
        discord_id = str(user_data['id'])
        username = user_data['username']

        # Check if user already exists
        user = db.query(User).filter(User.discord_id == discord_id).first()
        if not user:
            user = User(username=username, discord_id=discord_id, challenges=[], score=0, roles=["user"])
            db.add(user)
            db.commit()
            db.refresh(user)

        # Create a unique user session ID
        user_id = secrets.token_hex(64)
        user_sessions[user_id] = {"username": username, "discord_id": discord_id}

        response = RedirectResponse(url="/")
        response.set_cookie(key="session", value=user_id, httponly=True, secure=True, samesite="Lax", path="/")

        del state_storage[state]

        return response

