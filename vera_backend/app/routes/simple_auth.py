from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.sql_models import User, Company
import bcrypt
import jwt
from datetime import datetime, timedelta
from pydantic import BaseModel

router = APIRouter()

# Simple models
class SimpleLogin(BaseModel):
    email: str
    password: str

class SimpleSignup(BaseModel):
    name: str
    email: str
    password: str
    role: str

class SimpleUser(BaseModel):
    id: str
    name: str
    email: str
    role: str

class SimpleTokenResponse(BaseModel):
    token: str
    user: SimpleUser

# JWT Configuration
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

@router.post("/simple-auth/login", response_model=SimpleTokenResponse)
async def simple_login(user_credentials: SimpleLogin, db: Session = Depends(get_db)):
    """Simple login endpoint"""
    try:
        # Find user by email
        user = db.query(User).filter(User.email == user_credentials.email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Verify password
        if not verify_password(user_credentials.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )
        
        # Return token and user info
        return SimpleTokenResponse(
            token=access_token,
            user=SimpleUser(
                id=str(user.id),
                name=user.name,
                email=user.email,
                role=user.role
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/simple-auth/signup", response_model=SimpleTokenResponse)
async def simple_signup(user_data: SimpleSignup, db: Session = Depends(get_db)):
    """Simple signup endpoint"""
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Get the first company (for demo purposes)
        company = db.query(Company).first()
        if not company:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No company found. Please create a company first."
            )
        
        # Hash password
        hashed_password = get_password_hash(user_data.password)
        
        # Create new user
        new_user = User(
            name=user_data.name,
            email=user_data.email,
            password=hashed_password,
            role=user_data.role,
            company_id=company.id
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(new_user.id)}, expires_delta=access_token_expires
        )
        
        # Return token and user info
        return SimpleTokenResponse(
            token=access_token,
            user=SimpleUser(
                id=str(new_user.id),
                name=new_user.name,
                email=new_user.email,
                role=new_user.role
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Signup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/simple-auth/me", response_model=SimpleUser)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    try:
        return SimpleUser(
            id=str(current_user.id),
            name=current_user.name,
            email=current_user.email,
            role=current_user.role
        )
    except Exception as e:
        print(f"Get current user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        ) 