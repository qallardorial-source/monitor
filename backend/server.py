from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone, timedelta
import httpx

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Stripe setup
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest
stripe_api_key = os.environ.get('STRIPE_API_KEY', 'sk_test_emergent')

app = FastAPI()
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============== MODELS ==============

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    picture: Optional[str] = None
    role: str = "client"  # client, instructor, admin
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Instructor(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    bio: str = ""
    specialties: List[str] = []  # ski, snowboard, freestyle, etc.
    ski_levels: List[str] = []  # debutant, intermediaire, avance, expert
    hourly_rate: float = 50.0
    status: str = "pending"  # pending, approved, rejected
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Lesson(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    instructor_id: str
    lesson_type: str  # private, group
    title: str
    description: str = ""
    date: str  # ISO date string YYYY-MM-DD
    start_time: str  # HH:MM
    end_time: str  # HH:MM
    max_participants: int = 1
    current_participants: int = 0
    price: float
    status: str = "available"  # available, full, cancelled
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Booking(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    lesson_id: str
    user_id: str
    participants: int = 1
    status: str = "pending"  # pending, confirmed, cancelled
    payment_status: str = "pending"  # pending, paid, failed
    payment_session_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PaymentTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    user_id: Optional[str] = None
    booking_id: str
    amount: float
    currency: str = "eur"
    status: str = "initiated"  # initiated, paid, failed, expired
    payment_status: str = "pending"
    metadata: Optional[Dict] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ============== REQUEST/RESPONSE MODELS ==============

class SessionRequest(BaseModel):
    session_id: str

class InstructorCreate(BaseModel):
    bio: str = ""
    specialties: List[str] = []
    ski_levels: List[str] = []
    hourly_rate: float = 50.0

class InstructorStatusUpdate(BaseModel):
    status: str  # approved, rejected

class LessonCreate(BaseModel):
    lesson_type: str
    title: str
    description: str = ""
    date: str
    start_time: str
    end_time: str
    max_participants: int = 1
    price: float

class BookingCreate(BaseModel):
    lesson_id: str
    participants: int = 1

class PaymentRequest(BaseModel):
    booking_id: str
    origin_url: str

# ============== AUTH HELPERS ==============

async def get_session_from_request(request: Request) -> Optional[UserSession]:
    session_token = request.cookies.get("session_token")
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header.split(" ")[1]
    
    if not session_token:
        return None
    
    session = await db.user_sessions.find_one({"session_token": session_token})
    if not session:
        return None
    
    expires_at = session.get("expires_at")
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
    elif isinstance(expires_at, datetime) and expires_at.tzinfo is None:
        # Handle offset-naive datetime from MongoDB
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    
    if expires_at < datetime.now(timezone.utc):
        await db.user_sessions.delete_one({"session_token": session_token})
        return None
    
    return UserSession(**{k: v for k, v in session.items() if k != '_id'})

async def get_current_user(request: Request) -> Optional[User]:
    session = await get_session_from_request(request)
    if not session:
        return None
    
    user = await db.users.find_one({"id": session.user_id})
    if not user:
        return None
    
    return User(**{k: v for k, v in user.items() if k != '_id'})

async def require_auth(request: Request) -> User:
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Non authentifié")
    return user

async def require_admin(request: Request) -> User:
    user = await require_auth(request)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Accès admin requis")
    return user

async def require_instructor(request: Request) -> User:
    user = await require_auth(request)
    if user.role not in ["instructor", "admin"]:
        raise HTTPException(status_code=403, detail="Accès moniteur requis")
    return user

# ============== AUTH ROUTES ==============

@api_router.post("/auth/session")
async def process_session(request: Request, response: Response, data: SessionRequest):
    """Process session_id from Google OAuth redirect"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": data.session_id}
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=401, detail="Session invalide")
            
            user_data = resp.json()
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail="Erreur d'authentification")
    
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data["email"]})
    
    if existing_user:
        user_id = existing_user["id"]
        role = existing_user.get("role", "client")
    else:
        user_id = str(uuid.uuid4())
        role = "client"
        new_user = User(
            id=user_id,
            email=user_data["email"],
            name=user_data["name"],
            picture=user_data.get("picture"),
            role=role
        )
        user_doc = new_user.model_dump()
        user_doc["created_at"] = user_doc["created_at"].isoformat()
        await db.users.insert_one(user_doc)
    
    # Create session
    session_token = user_data.get("session_token", str(uuid.uuid4()))
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    session = UserSession(
        user_id=user_id,
        session_token=session_token,
        expires_at=expires_at
    )
    session_doc = session.model_dump()
    session_doc["created_at"] = session_doc["created_at"].isoformat()
    session_doc["expires_at"] = session_doc["expires_at"].isoformat()
    await db.user_sessions.insert_one(session_doc)
    
    # Set cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7*24*60*60
    )
    
    return {
        "id": user_id,
        "email": user_data["email"],
        "name": user_data["name"],
        "picture": user_data.get("picture"),
        "role": role
    }

@api_router.get("/auth/me")
async def get_me(request: Request):
    """Get current authenticated user"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Non authentifié")
    
    # Check if user is an instructor
    instructor = None
    if user.role == "instructor":
        instructor = await db.instructors.find_one({"user_id": user.id})
        if instructor:
            instructor = {k: v for k, v in instructor.items() if k != '_id'}
    
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
        "role": user.role,
        "instructor": instructor
    }

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    """Logout user"""
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    
    response.delete_cookie(key="session_token", path="/")
    return {"message": "Déconnecté"}

# ============== INSTRUCTOR ROUTES ==============

@api_router.get("/instructors")
async def list_instructors(status: Optional[str] = None):
    """List all approved instructors (public) or filter by status"""
    query = {"status": "approved"} if status is None else {"status": status}
    instructors = await db.instructors.find(query, {"_id": 0}).to_list(100)
    
    # Enrich with user data
    for instructor in instructors:
        user = await db.users.find_one({"id": instructor["user_id"]}, {"_id": 0})
        if user:
            instructor["user"] = user
    
    return instructors

@api_router.post("/instructors")
async def create_instructor(data: InstructorCreate, request: Request):
    """Register as instructor (requires auth)"""
    user = await require_auth(request)
    
    # Check if already instructor
    existing = await db.instructors.find_one({"user_id": user.id})
    if existing:
        raise HTTPException(status_code=400, detail="Déjà inscrit comme moniteur")
    
    instructor = Instructor(
        user_id=user.id,
        bio=data.bio,
        specialties=data.specialties,
        ski_levels=data.ski_levels,
        hourly_rate=data.hourly_rate,
        status="pending"
    )
    
    instructor_doc = instructor.model_dump()
    instructor_doc["created_at"] = instructor_doc["created_at"].isoformat()
    await db.instructors.insert_one(instructor_doc)
    
    # Update user role
    await db.users.update_one({"id": user.id}, {"$set": {"role": "instructor"}})
    
    return instructor_doc

@api_router.get("/instructors/{instructor_id}")
async def get_instructor(instructor_id: str):
    """Get instructor details"""
    instructor = await db.instructors.find_one({"id": instructor_id}, {"_id": 0})
    if not instructor:
        raise HTTPException(status_code=404, detail="Moniteur non trouvé")
    
    user = await db.users.find_one({"id": instructor["user_id"]}, {"_id": 0})
    instructor["user"] = user
    
    return instructor

@api_router.put("/instructors/{instructor_id}")
async def update_instructor(instructor_id: str, data: InstructorCreate, request: Request):
    """Update instructor profile"""
    user = await require_auth(request)
    instructor = await db.instructors.find_one({"id": instructor_id})
    
    if not instructor:
        raise HTTPException(status_code=404, detail="Moniteur non trouvé")
    
    if instructor["user_id"] != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Non autorisé")
    
    await db.instructors.update_one(
        {"id": instructor_id},
        {"$set": {
            "bio": data.bio,
            "specialties": data.specialties,
            "ski_levels": data.ski_levels,
            "hourly_rate": data.hourly_rate
        }}
    )
    
    return {"message": "Profil mis à jour"}

@api_router.put("/instructors/{instructor_id}/status")
async def update_instructor_status(instructor_id: str, data: InstructorStatusUpdate, request: Request):
    """Admin: Approve or reject instructor"""
    await require_admin(request)
    
    if data.status not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Statut invalide")
    
    result = await db.instructors.update_one(
        {"id": instructor_id},
        {"$set": {"status": data.status}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Moniteur non trouvé")
    
    return {"message": f"Moniteur {data.status}"}

# ============== LESSON ROUTES ==============

@api_router.get("/lessons")
async def list_lessons(
    instructor_id: Optional[str] = None,
    date: Optional[str] = None,
    lesson_type: Optional[str] = None
):
    """List available lessons"""
    query = {"status": "available"}
    if instructor_id:
        query["instructor_id"] = instructor_id
    if date:
        query["date"] = date
    if lesson_type:
        query["lesson_type"] = lesson_type
    
    lessons = await db.lessons.find(query, {"_id": 0}).to_list(100)
    
    # Enrich with instructor data
    for lesson in lessons:
        instructor = await db.instructors.find_one({"id": lesson["instructor_id"]}, {"_id": 0})
        if instructor:
            user = await db.users.find_one({"id": instructor["user_id"]}, {"_id": 0})
            instructor["user"] = user
            lesson["instructor"] = instructor
    
    return lessons

@api_router.post("/lessons")
async def create_lesson(data: LessonCreate, request: Request):
    """Instructor: Create a lesson"""
    user = await require_instructor(request)
    
    instructor = await db.instructors.find_one({"user_id": user.id})
    if not instructor:
        raise HTTPException(status_code=400, detail="Profil moniteur non trouvé")
    
    if instructor["status"] != "approved":
        raise HTTPException(status_code=403, detail="Votre profil doit être approuvé")
    
    lesson = Lesson(
        instructor_id=instructor["id"],
        lesson_type=data.lesson_type,
        title=data.title,
        description=data.description,
        date=data.date,
        start_time=data.start_time,
        end_time=data.end_time,
        max_participants=data.max_participants if data.lesson_type == "group" else 1,
        price=data.price
    )
    
    lesson_doc = lesson.model_dump()
    lesson_doc["created_at"] = lesson_doc["created_at"].isoformat()
    await db.lessons.insert_one(lesson_doc)
    
    return lesson_doc

@api_router.get("/lessons/{lesson_id}")
async def get_lesson(lesson_id: str):
    """Get lesson details"""
    lesson = await db.lessons.find_one({"id": lesson_id}, {"_id": 0})
    if not lesson:
        raise HTTPException(status_code=404, detail="Cours non trouvé")
    
    instructor = await db.instructors.find_one({"id": lesson["instructor_id"]}, {"_id": 0})
    if instructor:
        user = await db.users.find_one({"id": instructor["user_id"]}, {"_id": 0})
        instructor["user"] = user
        lesson["instructor"] = instructor
    
    return lesson

@api_router.delete("/lessons/{lesson_id}")
async def delete_lesson(lesson_id: str, request: Request):
    """Instructor: Delete/cancel lesson"""
    user = await require_instructor(request)
    instructor = await db.instructors.find_one({"user_id": user.id})
    
    lesson = await db.lessons.find_one({"id": lesson_id})
    if not lesson:
        raise HTTPException(status_code=404, detail="Cours non trouvé")
    
    if lesson["instructor_id"] != instructor["id"] and user.role != "admin":
        raise HTTPException(status_code=403, detail="Non autorisé")
    
    await db.lessons.update_one({"id": lesson_id}, {"$set": {"status": "cancelled"}})
    return {"message": "Cours annulé"}

@api_router.get("/my-lessons")
async def get_my_lessons(request: Request):
    """Instructor: Get my lessons"""
    user = await require_instructor(request)
    instructor = await db.instructors.find_one({"user_id": user.id})
    
    if not instructor:
        raise HTTPException(status_code=400, detail="Profil moniteur non trouvé")
    
    lessons = await db.lessons.find({"instructor_id": instructor["id"]}, {"_id": 0}).to_list(100)
    
    # Add booking info
    for lesson in lessons:
        bookings = await db.bookings.find({"lesson_id": lesson["id"], "status": {"$ne": "cancelled"}}, {"_id": 0}).to_list(100)
        for booking in bookings:
            user_data = await db.users.find_one({"id": booking["user_id"]}, {"_id": 0})
            booking["user"] = user_data
        lesson["bookings"] = bookings
    
    return lessons

# ============== BOOKING ROUTES ==============

@api_router.post("/bookings")
async def create_booking(data: BookingCreate, request: Request):
    """Create a booking"""
    user = await require_auth(request)
    
    lesson = await db.lessons.find_one({"id": data.lesson_id})
    if not lesson:
        raise HTTPException(status_code=404, detail="Cours non trouvé")
    
    if lesson["status"] != "available":
        raise HTTPException(status_code=400, detail="Cours non disponible")
    
    if lesson["current_participants"] + data.participants > lesson["max_participants"]:
        raise HTTPException(status_code=400, detail="Plus de places disponibles")
    
    # Check existing booking
    existing = await db.bookings.find_one({
        "lesson_id": data.lesson_id,
        "user_id": user.id,
        "status": {"$ne": "cancelled"}
    })
    if existing:
        raise HTTPException(status_code=400, detail="Vous avez déjà réservé ce cours")
    
    booking = Booking(
        lesson_id=data.lesson_id,
        user_id=user.id,
        participants=data.participants
    )
    
    booking_doc = booking.model_dump()
    booking_doc["created_at"] = booking_doc["created_at"].isoformat()
    await db.bookings.insert_one(booking_doc)
    
    # Update lesson participants
    new_count = lesson["current_participants"] + data.participants
    update_data = {"current_participants": new_count}
    if new_count >= lesson["max_participants"]:
        update_data["status"] = "full"
    await db.lessons.update_one({"id": data.lesson_id}, {"$set": update_data})
    
    return booking_doc

@api_router.get("/bookings")
async def list_bookings(request: Request):
    """Get user's bookings"""
    user = await require_auth(request)
    
    bookings = await db.bookings.find({"user_id": user.id}, {"_id": 0}).to_list(100)
    
    for booking in bookings:
        lesson = await db.lessons.find_one({"id": booking["lesson_id"]}, {"_id": 0})
        if lesson:
            instructor = await db.instructors.find_one({"id": lesson["instructor_id"]}, {"_id": 0})
            if instructor:
                user_data = await db.users.find_one({"id": instructor["user_id"]}, {"_id": 0})
                instructor["user"] = user_data
                lesson["instructor"] = instructor
            booking["lesson"] = lesson
    
    return bookings

@api_router.delete("/bookings/{booking_id}")
async def cancel_booking(booking_id: str, request: Request):
    """Cancel a booking"""
    user = await require_auth(request)
    
    booking = await db.bookings.find_one({"id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Réservation non trouvée")
    
    if booking["user_id"] != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Non autorisé")
    
    await db.bookings.update_one({"id": booking_id}, {"$set": {"status": "cancelled"}})
    
    # Update lesson participants
    lesson = await db.lessons.find_one({"id": booking["lesson_id"]})
    if lesson:
        new_count = max(0, lesson["current_participants"] - booking["participants"])
        await db.lessons.update_one(
            {"id": booking["lesson_id"]},
            {"$set": {"current_participants": new_count, "status": "available"}}
        )
    
    return {"message": "Réservation annulée"}

# ============== PAYMENT ROUTES ==============

@api_router.post("/payments/checkout")
async def create_checkout(data: PaymentRequest, request: Request):
    """Create Stripe checkout session"""
    user = await require_auth(request)
    
    booking = await db.bookings.find_one({"id": data.booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Réservation non trouvée")
    
    if booking["user_id"] != user.id:
        raise HTTPException(status_code=403, detail="Non autorisé")
    
    if booking["payment_status"] == "paid":
        raise HTTPException(status_code=400, detail="Déjà payé")
    
    lesson = await db.lessons.find_one({"id": booking["lesson_id"]})
    if not lesson:
        raise HTTPException(status_code=404, detail="Cours non trouvé")
    
    amount = float(lesson["price"]) * booking["participants"]
    
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url=webhook_url)
    
    success_url = f"{data.origin_url}/payment-success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{data.origin_url}/bookings"
    
    checkout_request = CheckoutSessionRequest(
        amount=amount,
        currency="eur",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "booking_id": data.booking_id,
            "user_id": user.id,
            "lesson_id": booking["lesson_id"]
        }
    )
    
    session = await stripe_checkout.create_checkout_session(checkout_request)
    
    # Create payment transaction
    transaction = PaymentTransaction(
        session_id=session.session_id,
        user_id=user.id,
        booking_id=data.booking_id,
        amount=amount,
        currency="eur",
        status="initiated",
        payment_status="pending",
        metadata={"lesson_id": booking["lesson_id"]}
    )
    
    transaction_doc = transaction.model_dump()
    transaction_doc["created_at"] = transaction_doc["created_at"].isoformat()
    await db.payment_transactions.insert_one(transaction_doc)
    
    # Update booking with session id
    await db.bookings.update_one(
        {"id": data.booking_id},
        {"$set": {"payment_session_id": session.session_id}}
    )
    
    return {"url": session.url, "session_id": session.session_id}

@api_router.get("/payments/status/{session_id}")
async def get_payment_status(session_id: str, request: Request):
    """Check payment status"""
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url=webhook_url)
    
    status = await stripe_checkout.get_checkout_status(session_id)
    
    # Update transaction and booking
    if status.payment_status == "paid":
        transaction = await db.payment_transactions.find_one({"session_id": session_id})
        if transaction and transaction["status"] != "paid":
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {"$set": {"status": "paid", "payment_status": "paid"}}
            )
            await db.bookings.update_one(
                {"id": transaction["booking_id"]},
                {"$set": {"status": "confirmed", "payment_status": "paid"}}
            )
    elif status.status == "expired":
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {"status": "expired", "payment_status": "expired"}}
        )
    
    return {
        "status": status.status,
        "payment_status": status.payment_status,
        "amount_total": status.amount_total,
        "currency": status.currency
    }

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    body = await request.body()
    signature = request.headers.get("Stripe-Signature")
    
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url=webhook_url)
    
    try:
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        
        if webhook_response.payment_status == "paid":
            session_id = webhook_response.session_id
            transaction = await db.payment_transactions.find_one({"session_id": session_id})
            if transaction and transaction["status"] != "paid":
                await db.payment_transactions.update_one(
                    {"session_id": session_id},
                    {"$set": {"status": "paid", "payment_status": "paid"}}
                )
                await db.bookings.update_one(
                    {"id": transaction["booking_id"]},
                    {"$set": {"status": "confirmed", "payment_status": "paid"}}
                )
        
        return {"received": True}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"received": True}

# ============== ADMIN ROUTES ==============

@api_router.get("/admin/pending-instructors")
async def get_pending_instructors(request: Request):
    """Admin: Get pending instructor applications"""
    await require_admin(request)
    
    instructors = await db.instructors.find({"status": "pending"}, {"_id": 0}).to_list(100)
    
    for instructor in instructors:
        user = await db.users.find_one({"id": instructor["user_id"]}, {"_id": 0})
        instructor["user"] = user
    
    return instructors

@api_router.get("/admin/stats")
async def get_admin_stats(request: Request):
    """Admin: Get platform statistics"""
    await require_admin(request)
    
    total_users = await db.users.count_documents({})
    total_instructors = await db.instructors.count_documents({"status": "approved"})
    pending_instructors = await db.instructors.count_documents({"status": "pending"})
    total_lessons = await db.lessons.count_documents({"status": "available"})
    total_bookings = await db.bookings.count_documents({"status": {"$ne": "cancelled"}})
    
    return {
        "total_users": total_users,
        "total_instructors": total_instructors,
        "pending_instructors": pending_instructors,
        "total_lessons": total_lessons,
        "total_bookings": total_bookings
    }

# ============== UTILITY ROUTES ==============

@api_router.get("/")
async def root():
    return {"message": "SkiMonitor API"}

@api_router.get("/health")
async def health():
    return {"status": "healthy"}

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
