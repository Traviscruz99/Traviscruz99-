from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import hashlib
import jwt
import secrets
from decimal import Decimal
import asyncio

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-here')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

# Create the main app without a prefix
app = FastAPI(title="Digital Bank API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# Models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: str
    
class UserLogin(BaseModel):
    email: EmailStr
    password: str
    
class User(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    phone: str
    created_at: datetime
    is_active: bool = True
    
class AccountCreate(BaseModel):
    account_type: str  # "checking", "savings", "investment"
    currency: str = "TRY"
    
class Account(BaseModel):
    id: str
    user_id: str
    account_number: str
    iban: str
    account_type: str
    currency: str
    balance: float
    created_at: datetime
    is_active: bool = True
    
class TransactionCreate(BaseModel):
    from_account_id: str
    to_account_id: Optional[str] = None
    to_iban: Optional[str] = None
    amount: float
    transaction_type: str  # "transfer", "deposit", "withdrawal", "bill_payment"
    description: str
    category: Optional[str] = None
    
class Transaction(BaseModel):
    id: str
    from_account_id: Optional[str]
    to_account_id: Optional[str]
    from_iban: Optional[str]
    to_iban: Optional[str]
    amount: float
    transaction_type: str
    description: str
    category: Optional[str]
    status: str  # "pending", "completed", "failed"
    created_at: datetime
    
class MoneyTransfer(BaseModel):
    to_iban: str
    amount: float
    description: str
    
class BillPayment(BaseModel):
    bill_type: str  # "electricity", "gas", "water", "telecom", "internet"
    provider: str
    account_number: str
    amount: float
    
class CardCreate(BaseModel):
    account_id: str
    card_type: str  # "debit", "credit"
    limit: Optional[float] = None
    
class Card(BaseModel):
    id: str
    account_id: str
    card_number: str
    card_type: str
    limit: Optional[float]
    status: str  # "active", "blocked", "expired"
    created_at: datetime
    expires_at: datetime

# Utility Functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hashlib.sha256(password.encode()).hexdigest() == hashed

def create_jwt_token(user_id: str) -> str:
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def generate_iban() -> str:
    """Generate Turkish IBAN format"""
    bank_code = "0001"  # Mock bank code
    branch_code = "0001"
    account_number = str(secrets.randbelow(10**11)).zfill(11)
    check_digits = "32"  # Simplified check digit
    return f"TR{check_digits} {bank_code} {branch_code} {account_number}"

def generate_account_number() -> str:
    return str(secrets.randbelow(10**10)).zfill(10)

def generate_card_number() -> str:
    return "4*** **** **** " + str(secrets.randbelow(10**4)).zfill(4)

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_jwt_token(token)
    user_id = payload.get('user_id')
    
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return User(**user)

# Auth Routes
@api_router.post("/auth/register", response_model=dict)
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user_id = str(uuid.uuid4())
    user_dict = {
        "id": user_id,
        "email": user_data.email,
        "password_hash": hash_password(user_data.password),
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "phone": user_data.phone,
        "created_at": datetime.utcnow(),
        "is_active": True
    }
    
    await db.users.insert_one(user_dict)
    
    # Create default checking account
    account_id = str(uuid.uuid4())
    account_dict = {
        "id": account_id,
        "user_id": user_id,
        "account_number": generate_account_number(),
        "iban": generate_iban(),
        "account_type": "checking",
        "currency": "TRY",
        "balance": 1000.0,  # Welcome bonus
        "created_at": datetime.utcnow(),
        "is_active": True
    }
    
    await db.accounts.insert_one(account_dict)
    
    # Generate JWT token
    token = create_jwt_token(user_id)
    
    return {
        "message": "User registered successfully",
        "token": token,
        "user": {
            "id": user_id,
            "email": user_data.email,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name
        }
    }

@api_router.post("/auth/login", response_model=dict)
async def login(login_data: UserLogin):
    user = await db.users.find_one({"email": login_data.email})
    if not user or not verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_jwt_token(user["id"])
    
    return {
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "first_name": user["first_name"],
            "last_name": user["last_name"]
        }
    }

# Account Routes
@api_router.get("/accounts", response_model=List[Account])
async def get_accounts(current_user: User = Depends(get_current_user)):
    accounts = await db.accounts.find({"user_id": current_user.id, "is_active": True}).to_list(100)
    return [Account(**account) for account in accounts]

@api_router.post("/accounts", response_model=Account)
async def create_account(account_data: AccountCreate, current_user: User = Depends(get_current_user)):
    account_id = str(uuid.uuid4())
    account_dict = {
        "id": account_id,
        "user_id": current_user.id,
        "account_number": generate_account_number(),
        "iban": generate_iban(),
        "account_type": account_data.account_type,
        "currency": account_data.currency,
        "balance": 0.0,
        "created_at": datetime.utcnow(),
        "is_active": True
    }
    
    await db.accounts.insert_one(account_dict)
    return Account(**account_dict)

@api_router.get("/accounts/{account_id}/balance")
async def get_account_balance(account_id: str, current_user: User = Depends(get_current_user)):
    account = await db.accounts.find_one({"id": account_id, "user_id": current_user.id})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return {"balance": account["balance"], "currency": account["currency"]}

# Transaction Routes
@api_router.get("/accounts/{account_id}/transactions", response_model=List[Transaction])
async def get_transactions(account_id: str, current_user: User = Depends(get_current_user)):
    # Verify account ownership
    account = await db.accounts.find_one({"id": account_id, "user_id": current_user.id})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    transactions = await db.transactions.find({
        "$or": [
            {"from_account_id": account_id},
            {"to_account_id": account_id}
        ]
    }).sort("created_at", -1).to_list(100)
    
    return [Transaction(**transaction) for transaction in transactions]

@api_router.post("/accounts/{account_id}/deposit")
async def deposit_money(account_id: str, amount: float, current_user: User = Depends(get_current_user)):
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    account = await db.accounts.find_one({"id": account_id, "user_id": current_user.id})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Update balance
    new_balance = account["balance"] + amount
    await db.accounts.update_one(
        {"id": account_id},
        {"$set": {"balance": new_balance}}
    )
    
    # Create transaction record
    transaction_id = str(uuid.uuid4())
    transaction_dict = {
        "id": transaction_id,
        "from_account_id": None,
        "to_account_id": account_id,
        "from_iban": None,
        "to_iban": account["iban"],
        "amount": amount,
        "transaction_type": "deposit",
        "description": "Account deposit",
        "category": "deposit",
        "status": "completed",
        "created_at": datetime.utcnow()
    }
    
    await db.transactions.insert_one(transaction_dict)
    
    return {"message": "Deposit successful", "new_balance": new_balance}

@api_router.post("/accounts/{account_id}/transfer")
async def transfer_money(account_id: str, transfer_data: MoneyTransfer, current_user: User = Depends(get_current_user)):
    if transfer_data.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    # Get source account
    from_account = await db.accounts.find_one({"id": account_id, "user_id": current_user.id})
    if not from_account:
        raise HTTPException(status_code=404, detail="Source account not found")
    
    if from_account["balance"] < transfer_data.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    
    # Find destination account by IBAN
    to_account = await db.accounts.find_one({"iban": transfer_data.to_iban})
    
    # Create transaction
    transaction_id = str(uuid.uuid4())
    transaction_dict = {
        "id": transaction_id,
        "from_account_id": account_id,
        "to_account_id": to_account["id"] if to_account else None,
        "from_iban": from_account["iban"],
        "to_iban": transfer_data.to_iban,
        "amount": transfer_data.amount,
        "transaction_type": "transfer",
        "description": transfer_data.description,
        "category": "transfer",
        "status": "completed" if to_account else "pending",
        "created_at": datetime.utcnow()
    }
    
    # Update balances
    new_from_balance = from_account["balance"] - transfer_data.amount
    await db.accounts.update_one(
        {"id": account_id},
        {"$set": {"balance": new_from_balance}}
    )
    
    if to_account:
        new_to_balance = to_account["balance"] + transfer_data.amount
        await db.accounts.update_one(
            {"id": to_account["id"]},
            {"$set": {"balance": new_to_balance}}
        )
    
    await db.transactions.insert_one(transaction_dict)
    
    return {
        "message": "Transfer initiated successfully",
        "transaction_id": transaction_id,
        "status": transaction_dict["status"]
    }

@api_router.post("/accounts/{account_id}/pay-bill")
async def pay_bill(account_id: str, bill_data: BillPayment, current_user: User = Depends(get_current_user)):
    if bill_data.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    account = await db.accounts.find_one({"id": account_id, "user_id": current_user.id})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    if account["balance"] < bill_data.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    
    # Update balance
    new_balance = account["balance"] - bill_data.amount
    await db.accounts.update_one(
        {"id": account_id},
        {"$set": {"balance": new_balance}}
    )
    
    # Create transaction record
    transaction_id = str(uuid.uuid4())
    transaction_dict = {
        "id": transaction_id,
        "from_account_id": account_id,
        "to_account_id": None,
        "from_iban": account["iban"],
        "to_iban": None,
        "amount": bill_data.amount,
        "transaction_type": "bill_payment",
        "description": f"{bill_data.bill_type} bill payment to {bill_data.provider}",
        "category": bill_data.bill_type,
        "status": "completed",
        "created_at": datetime.utcnow()
    }
    
    await db.transactions.insert_one(transaction_dict)
    
    return {
        "message": "Bill payment successful",
        "transaction_id": transaction_id,
        "new_balance": new_balance
    }

# Card Routes
@api_router.get("/cards", response_model=List[Card])
async def get_cards(current_user: User = Depends(get_current_user)):
    # Get user's accounts first
    accounts = await db.accounts.find({"user_id": current_user.id}).to_list(100)
    account_ids = [acc["id"] for acc in accounts]
    
    cards = await db.cards.find({"account_id": {"$in": account_ids}}).to_list(100)
    return [Card(**card) for card in cards]

@api_router.post("/cards", response_model=Card)
async def create_card(card_data: CardCreate, current_user: User = Depends(get_current_user)):
    # Verify account ownership
    account = await db.accounts.find_one({"id": card_data.account_id, "user_id": current_user.id})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    card_id = str(uuid.uuid4())
    card_dict = {
        "id": card_id,
        "account_id": card_data.account_id,
        "card_number": generate_card_number(),
        "card_type": card_data.card_type,
        "limit": card_data.limit,
        "status": "active",
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(days=1460)  # 4 years
    }
    
    await db.cards.insert_one(card_dict)
    return Card(**card_dict)

# Dashboard Routes
@api_router.get("/dashboard")
async def get_dashboard(current_user: User = Depends(get_current_user)):
    # Get all accounts
    accounts = await db.accounts.find({"user_id": current_user.id, "is_active": True}).to_list(100)
    
    # Calculate total balance
    total_balance = sum(acc["balance"] for acc in accounts)
    
    # Get recent transactions
    account_ids = [acc["id"] for acc in accounts]
    recent_transactions = await db.transactions.find({
        "$or": [
            {"from_account_id": {"$in": account_ids}},
            {"to_account_id": {"$in": account_ids}}
        ]
    }).sort("created_at", -1).limit(10).to_list(10)
    
    # Get cards
    cards = await db.cards.find({"account_id": {"$in": account_ids}}).to_list(100)
    
    return {
        "user": {
            "id": current_user.id,
            "name": f"{current_user.first_name} {current_user.last_name}",
            "email": current_user.email
        },
        "total_balance": total_balance,
        "accounts": accounts,
        "recent_transactions": recent_transactions,
        "cards": cards
    }

# Health check
@api_router.get("/")
async def root():
    return {"message": "Digital Bank API is running", "version": "1.0.0"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()