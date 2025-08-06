from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
import hashlib

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
SECRET_KEY = "your-secret-key-change-in-production"  # TODO: Move to .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Create the main app
app = FastAPI(title="Story Publishing Platform")

# Create API router
api_router = APIRouter(prefix="/api")

# Pydantic Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: Optional[str] = None
    is_admin: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class Story(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    author_id: str
    author_username: str
    status: str = "pending"  # pending, approved, rejected
    likes: int = 0
    liked_by: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    approved_at: Optional[datetime] = None

class StoryCreate(BaseModel):
    title: str
    content: str

class StoryUpdate(BaseModel):
    status: str  # approved, rejected

# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"username": username})
    if user is None:
        raise credentials_exception
    return User(**user)

async def get_current_admin_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

# Initialize admin user
async def create_admin_user():
    admin_exists = await db.users.find_one({"username": "admin"})
    if not admin_exists:
        admin_user = User(
            username="admin",
            email="admin@storyplatform.com",
            is_admin=True
        )
        admin_dict = admin_user.dict()
        admin_dict["password"] = get_password_hash("admin123")  # Change this password!
        await db.users.insert_one(admin_dict)
        print("Admin user created: username=admin, password=admin123")

# API Routes
@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"username": user_data.username})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Create user
    user = User(
        username=user_data.username,
        email=user_data.email,
        is_admin=False
    )
    user_dict = user.dict()
    user_dict["password"] = get_password_hash(user_data.password)
    
    await db.users.insert_one(user_dict)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer", user=user)

@api_router.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    user = await db.users.find_one({"username": user_data.username})
    if not user or not verify_password(user_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    
    user_obj = User(**user)
    return Token(access_token=access_token, token_type="bearer", user=user_obj)

@api_router.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

@api_router.post("/stories", response_model=Story)
async def create_story(story_data: StoryCreate, current_user: User = Depends(get_current_user)):
    story = Story(
        title=story_data.title,
        content=story_data.content,
        author_id=current_user.id,
        author_username=current_user.username,
        status="pending"
    )
    
    await db.stories.insert_one(story.dict())
    return story

@api_router.get("/stories/my", response_model=List[Story])
async def get_my_stories(current_user: User = Depends(get_current_user)):
    stories = await db.stories.find({"author_id": current_user.id}).to_list(1000)
    return [Story(**story) for story in stories]

@api_router.get("/stories/public", response_model=List[Story])
async def get_public_stories():
    stories = await db.stories.find({"status": "approved"}).sort("approved_at", -1).to_list(1000)
    return [Story(**story) for story in stories]

@api_router.get("/stories/pending", response_model=List[Story])
async def get_pending_stories(current_user: User = Depends(get_current_admin_user)):
    stories = await db.stories.find({"status": "pending"}).sort("created_at", -1).to_list(1000)
    return [Story(**story) for story in stories]

@api_router.put("/stories/{story_id}/moderate")
async def moderate_story(
    story_id: str, 
    update_data: StoryUpdate,
    current_user: User = Depends(get_current_admin_user)
):
    update_dict = {"status": update_data.status}
    if update_data.status == "approved":
        update_dict["approved_at"] = datetime.utcnow()
    
    result = await db.stories.update_one(
        {"id": story_id},
        {"$set": update_dict}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Story not found")
    
    return {"message": f"Story {update_data.status}"}

@api_router.post("/stories/{story_id}/like")
async def like_story(story_id: str, current_user: User = Depends(get_current_user)):
    story = await db.stories.find_one({"id": story_id, "status": "approved"})
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    liked_by = story.get("liked_by", [])
    
    if current_user.id in liked_by:
        # Unlike
        liked_by.remove(current_user.id)
        likes = len(liked_by)
        await db.stories.update_one(
            {"id": story_id},
            {"$set": {"liked_by": liked_by, "likes": likes}}
        )
        return {"message": "Story unliked", "likes": likes}
    else:
        # Like
        liked_by.append(current_user.id)
        likes = len(liked_by)
        await db.stories.update_one(
            {"id": story_id},
            {"$set": {"liked_by": liked_by, "likes": likes}}
        )
        return {"message": "Story liked", "likes": likes}

# Include the router in the main app
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve React static files
frontend_build_path = Path(__file__).parent.parent / "frontend" / "build"
if frontend_build_path.exists():
    app.mount("/static", StaticFiles(directory=frontend_build_path / "static"), name="static")
    
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404)
        return FileResponse(frontend_build_path / "index.html")

# Events
@app.on_event("startup")
async def startup_event():
    await create_admin_user()

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)