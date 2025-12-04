from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends, Query
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

# Platform settings
PLATFORM_COMMISSION = 0.10  # 10% commission

app = FastAPI()
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============== EMAIL SERVICE (SIMULATED) ==============

class EmailService:
    """Simulated email service - logs emails to console"""
    
    @staticmethod
    async def send_booking_confirmation(user_email: str, user_name: str, lesson_title: str, lesson_date: str, lesson_time: str, instructor_name: str, price: float):
        logger.info(f"""
        ╔══════════════════════════════════════════════════════════════╗
        ║                    EMAIL DE CONFIRMATION                      ║
        ╠══════════════════════════════════════════════════════════════╣
        ║ À: {user_email}
        ║ Objet: Confirmation de réservation - {lesson_title}
        ║
        ║ Bonjour {user_name},
        ║
        ║ Votre réservation a bien été enregistrée !
        ║
        ║ Détails du cours:
        ║ - Cours: {lesson_title}
        ║ - Date: {lesson_date}
        ║ - Horaire: {lesson_time}
        ║ - Moniteur: {instructor_name}
        ║ - Prix: {price}€
        ║
        ║ À bientôt sur les pistes !
        ║ L'équipe SkiMonitor
        ╚══════════════════════════════════════════════════════════════╝
        """)
    
    @staticmethod
    async def send_payment_confirmation(user_email: str, user_name: str, lesson_title: str, amount: float):
        logger.info(f"""
        ╔══════════════════════════════════════════════════════════════╗
        ║                  EMAIL DE PAIEMENT CONFIRMÉ                   ║
        ╠══════════════════════════════════════════════════════════════╣
        ║ À: {user_email}
        ║ Objet: Paiement confirmé - {lesson_title}
        ║
        ║ Bonjour {user_name},
        ║
        ║ Votre paiement de {amount}€ a été confirmé.
        ║ Votre réservation est maintenant validée.
        ║
        ║ Rendez-vous sur les pistes !
        ║ L'équipe SkiMonitor
        ╚══════════════════════════════════════════════════════════════╝
        """)
    
    @staticmethod
    async def send_lesson_reminder(user_email: str, user_name: str, lesson_title: str, lesson_date: str, lesson_time: str, instructor_name: str, station: str):
        logger.info(f"""
        ╔══════════════════════════════════════════════════════════════╗
        ║                    RAPPEL DE COURS (24H)                      ║
        ╠══════════════════════════════════════════════════════════════╣
        ║ À: {user_email}
        ║ Objet: Rappel - Votre cours demain !
        ║
        ║ Bonjour {user_name},
        ║
        ║ N'oubliez pas votre cours demain !
        ║
        ║ - Cours: {lesson_title}
        ║ - Date: {lesson_date}
        ║ - Horaire: {lesson_time}
        ║ - Moniteur: {instructor_name}
        ║ - Station: {station}
        ║
        ║ Préparez vos affaires et à demain !
        ║ L'équipe SkiMonitor
        ╚══════════════════════════════════════════════════════════════╝
        """)
    
    @staticmethod
    async def send_instructor_notification(instructor_email: str, instructor_name: str, client_name: str, lesson_title: str, lesson_date: str):
        logger.info(f"""
        ╔══════════════════════════════════════════════════════════════╗
        ║                 NOUVELLE RÉSERVATION MONITEUR                 ║
        ╠══════════════════════════════════════════════════════════════╣
        ║ À: {instructor_email}
        ║ Objet: Nouvelle réservation pour {lesson_title}
        ║
        ║ Bonjour {instructor_name},
        ║
        ║ Vous avez une nouvelle réservation !
        ║
        ║ - Client: {client_name}
        ║ - Cours: {lesson_title}
        ║ - Date: {lesson_date}
        ║
        ║ Connectez-vous pour voir les détails.
        ║ L'équipe SkiMonitor
        ╚══════════════════════════════════════════════════════════════╝
        """)

email_service = EmailService()

# ============== SKI STATIONS DATA ==============

SKI_STATIONS = [
    {"id": "chamonix", "name": "Chamonix Mont-Blanc", "region": "Haute-Savoie", "altitude": 1035},
    {"id": "courchevel", "name": "Courchevel", "region": "Savoie", "altitude": 1850},
    {"id": "meribel", "name": "Méribel", "region": "Savoie", "altitude": 1450},
    {"id": "val-thorens", "name": "Val Thorens", "region": "Savoie", "altitude": 2300},
    {"id": "tignes", "name": "Tignes", "region": "Savoie", "altitude": 2100},
    {"id": "val-disere", "name": "Val d'Isère", "region": "Savoie", "altitude": 1850},
    {"id": "les-arcs", "name": "Les Arcs", "region": "Savoie", "altitude": 1600},
    {"id": "la-plagne", "name": "La Plagne", "region": "Savoie", "altitude": 1970},
    {"id": "avoriaz", "name": "Avoriaz", "region": "Haute-Savoie", "altitude": 1800},
    {"id": "morzine", "name": "Morzine", "region": "Haute-Savoie", "altitude": 1000},
    {"id": "megeve", "name": "Megève", "region": "Haute-Savoie", "altitude": 1113},
    {"id": "les-2-alpes", "name": "Les 2 Alpes", "region": "Isère", "altitude": 1650},
    {"id": "alpe-dhuez", "name": "Alpe d'Huez", "region": "Isère", "altitude": 1860},
    {"id": "serre-chevalier", "name": "Serre Chevalier", "region": "Hautes-Alpes", "altitude": 1200},
    {"id": "la-clusaz", "name": "La Clusaz", "region": "Haute-Savoie", "altitude": 1100},
]

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
    station_id: str = ""  # Associated ski station
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
    is_recurring: bool = False
    recurrence_type: Optional[str] = None  # weekly, biweekly
    recurrence_end_date: Optional[str] = None
    parent_lesson_id: Optional[str] = None  # For recurring lessons
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
    commission: float = 0.0  # Platform commission
    instructor_amount: float = 0.0  # Amount for instructor
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
    station_id: str = ""

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
    is_recurring: bool = False
    recurrence_type: Optional[str] = None  # weekly, biweekly
    recurrence_end_date: Optional[str] = None

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
        async with httpx.AsyncClient() as http_client:
            resp = await http_client.get(
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

# ============== STATIONS ROUTES ==============

@api_router.get("/stations")
async def list_stations():
    """List all ski stations"""
    return SKI_STATIONS

@api_router.get("/stations/{station_id}")
async def get_station(station_id: str):
    """Get station details"""
    station = next((s for s in SKI_STATIONS if s["id"] == station_id), None)
    if not station:
        raise HTTPException(status_code=404, detail="Station non trouvée")
    return station

# ============== INSTRUCTOR ROUTES ==============

@api_router.get("/instructors")
async def list_instructors(
    status: Optional[str] = None,
    station_id: Optional[str] = None,
    specialty: Optional[str] = None,
    level: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None
):
    """List instructors with filters"""
    query = {"status": "approved"} if status is None else {"status": status}
    
    if station_id:
        query["station_id"] = station_id
    if specialty:
        query["specialties"] = {"$in": [specialty]}
    if level:
        query["ski_levels"] = {"$in": [level]}
    if min_price is not None:
        query["hourly_rate"] = {"$gte": min_price}
    if max_price is not None:
        if "hourly_rate" in query:
            query["hourly_rate"]["$lte"] = max_price
        else:
            query["hourly_rate"] = {"$lte": max_price}
    
    instructors = await db.instructors.find(query, {"_id": 0}).to_list(100)
    
    # Enrich with user data and station
    for instructor in instructors:
        user = await db.users.find_one({"id": instructor["user_id"]}, {"_id": 0})
        if user:
            instructor["user"] = user
        # Add station info
        if instructor.get("station_id"):
            station = next((s for s in SKI_STATIONS if s["id"] == instructor["station_id"]), None)
            instructor["station"] = station
    
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
        station_id=data.station_id,
        status="pending"
    )
    
    instructor_doc = instructor.model_dump()
    instructor_doc["created_at"] = instructor_doc["created_at"].isoformat()
    await db.instructors.insert_one(instructor_doc)
    
    # Update user role
    await db.users.update_one({"id": user.id}, {"$set": {"role": "instructor"}})
    
    # Return without _id
    instructor_doc.pop("_id", None)
    return instructor_doc

@api_router.get("/instructors/{instructor_id}")
async def get_instructor(instructor_id: str):
    """Get instructor details"""
    instructor = await db.instructors.find_one({"id": instructor_id}, {"_id": 0})
    if not instructor:
        raise HTTPException(status_code=404, detail="Moniteur non trouvé")
    
    user = await db.users.find_one({"id": instructor["user_id"]}, {"_id": 0})
    instructor["user"] = user
    
    # Add station info
    if instructor.get("station_id"):
        station = next((s for s in SKI_STATIONS if s["id"] == instructor["station_id"]), None)
        instructor["station"] = station
    
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
            "hourly_rate": data.hourly_rate,
            "station_id": data.station_id
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
    lesson_type: Optional[str] = None,
    station_id: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    level: Optional[str] = None
):
    """List available lessons with filters"""
    query = {"status": "available"}
    if instructor_id:
        query["instructor_id"] = instructor_id
    if date:
        query["date"] = date
    if lesson_type:
        query["lesson_type"] = lesson_type
    if min_price is not None:
        query["price"] = {"$gte": min_price}
    if max_price is not None:
        if "price" in query:
            query["price"]["$lte"] = max_price
        else:
            query["price"] = {"$lte": max_price}
    
    lessons = await db.lessons.find(query, {"_id": 0}).to_list(100)
    
    # Filter by station or level (need to check instructor)
    filtered_lessons = []
    for lesson in lessons:
        instructor = await db.instructors.find_one({"id": lesson["instructor_id"]}, {"_id": 0})
        if instructor:
            # Filter by station
            if station_id and instructor.get("station_id") != station_id:
                continue
            # Filter by level
            if level and level not in instructor.get("ski_levels", []):
                continue
            
            user = await db.users.find_one({"id": instructor["user_id"]}, {"_id": 0})
            instructor["user"] = user
            if instructor.get("station_id"):
                station = next((s for s in SKI_STATIONS if s["id"] == instructor["station_id"]), None)
                instructor["station"] = station
            lesson["instructor"] = instructor
            filtered_lessons.append(lesson)
    
    return filtered_lessons

@api_router.post("/lessons")
async def create_lesson(data: LessonCreate, request: Request):
    """Instructor: Create a lesson (with optional recurrence)"""
    user = await require_instructor(request)
    
    instructor = await db.instructors.find_one({"user_id": user.id})
    if not instructor:
        raise HTTPException(status_code=400, detail="Profil moniteur non trouvé")
    
    if instructor["status"] != "approved":
        raise HTTPException(status_code=403, detail="Votre profil doit être approuvé")
    
    created_lessons = []
    
    # Create main lesson
    lesson = Lesson(
        instructor_id=instructor["id"],
        lesson_type=data.lesson_type,
        title=data.title,
        description=data.description,
        date=data.date,
        start_time=data.start_time,
        end_time=data.end_time,
        max_participants=data.max_participants if data.lesson_type == "group" else 1,
        price=data.price,
        is_recurring=data.is_recurring,
        recurrence_type=data.recurrence_type,
        recurrence_end_date=data.recurrence_end_date
    )
    
    lesson_doc = lesson.model_dump()
    lesson_doc["created_at"] = lesson_doc["created_at"].isoformat()
    await db.lessons.insert_one(lesson_doc)
    lesson_doc.pop("_id", None)
    created_lessons.append(lesson_doc)
    
    # Create recurring lessons if enabled
    if data.is_recurring and data.recurrence_type and data.recurrence_end_date:
        parent_id = lesson.id
        current_date = datetime.strptime(data.date, "%Y-%m-%d")
        end_date = datetime.strptime(data.recurrence_end_date, "%Y-%m-%d")
        
        delta = timedelta(weeks=1) if data.recurrence_type == "weekly" else timedelta(weeks=2)
        
        current_date += delta
        while current_date <= end_date:
            recurring_lesson = Lesson(
                instructor_id=instructor["id"],
                lesson_type=data.lesson_type,
                title=data.title,
                description=data.description,
                date=current_date.strftime("%Y-%m-%d"),
                start_time=data.start_time,
                end_time=data.end_time,
                max_participants=data.max_participants if data.lesson_type == "group" else 1,
                price=data.price,
                is_recurring=True,
                recurrence_type=data.recurrence_type,
                parent_lesson_id=parent_id
            )
            
            recurring_doc = recurring_lesson.model_dump()
            recurring_doc["created_at"] = recurring_doc["created_at"].isoformat()
            await db.lessons.insert_one(recurring_doc)
            recurring_doc.pop("_id", None)
            created_lessons.append(recurring_doc)
            
            current_date += delta
    
    return created_lessons[0] if len(created_lessons) == 1 else {"lessons_created": len(created_lessons), "first_lesson": created_lessons[0]}

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
        if instructor.get("station_id"):
            station = next((s for s in SKI_STATIONS if s["id"] == instructor["station_id"]), None)
            instructor["station"] = station
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
    
    if instructor and lesson["instructor_id"] != instructor["id"] and user.role != "admin":
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
    
    # Send email notifications
    instructor = await db.instructors.find_one({"id": lesson["instructor_id"]})
    instructor_user = await db.users.find_one({"id": instructor["user_id"]}) if instructor else None
    
    # Email to client
    await email_service.send_booking_confirmation(
        user_email=user.email,
        user_name=user.name,
        lesson_title=lesson["title"],
        lesson_date=lesson["date"],
        lesson_time=f"{lesson['start_time']} - {lesson['end_time']}",
        instructor_name=instructor_user["name"] if instructor_user else "Moniteur",
        price=lesson["price"] * data.participants
    )
    
    # Email to instructor
    if instructor_user:
        await email_service.send_instructor_notification(
            instructor_email=instructor_user["email"],
            instructor_name=instructor_user["name"],
            client_name=user.name,
            lesson_title=lesson["title"],
            lesson_date=lesson["date"]
        )
    
    # Return without _id
    booking_doc.pop("_id", None)
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
                if instructor.get("station_id"):
                    station = next((s for s in SKI_STATIONS if s["id"] == instructor["station_id"]), None)
                    instructor["station"] = station
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
    """Create Stripe checkout session with commission"""
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
    
    total_amount = float(lesson["price"]) * booking["participants"]
    commission = round(total_amount * PLATFORM_COMMISSION, 2)
    instructor_amount = round(total_amount - commission, 2)
    
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url=webhook_url)
    
    success_url = f"{data.origin_url}/payment-success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{data.origin_url}/bookings"
    
    checkout_request = CheckoutSessionRequest(
        amount=total_amount,
        currency="eur",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "booking_id": data.booking_id,
            "user_id": user.id,
            "lesson_id": booking["lesson_id"],
            "commission": str(commission),
            "instructor_amount": str(instructor_amount)
        }
    )
    
    session = await stripe_checkout.create_checkout_session(checkout_request)
    
    # Create payment transaction with commission details
    transaction = PaymentTransaction(
        session_id=session.session_id,
        user_id=user.id,
        booking_id=data.booking_id,
        amount=total_amount,
        commission=commission,
        instructor_amount=instructor_amount,
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
    
    return {
        "url": session.url,
        "session_id": session.session_id,
        "total_amount": total_amount,
        "commission": commission,
        "instructor_amount": instructor_amount
    }

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
            
            # Send payment confirmation email
            booking = await db.bookings.find_one({"id": transaction["booking_id"]})
            if booking:
                user = await db.users.find_one({"id": booking["user_id"]})
                lesson = await db.lessons.find_one({"id": booking["lesson_id"]})
                if user and lesson:
                    await email_service.send_payment_confirmation(
                        user_email=user["email"],
                        user_name=user["name"],
                        lesson_title=lesson["title"],
                        amount=transaction["amount"]
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
        if instructor.get("station_id"):
            station = next((s for s in SKI_STATIONS if s["id"] == instructor["station_id"]), None)
            instructor["station"] = station
    
    return instructors

@api_router.get("/admin/stats")
async def get_admin_stats(request: Request):
    """Admin: Get platform statistics including commission"""
    await require_admin(request)
    
    total_users = await db.users.count_documents({})
    total_instructors = await db.instructors.count_documents({"status": "approved"})
    pending_instructors = await db.instructors.count_documents({"status": "pending"})
    total_lessons = await db.lessons.count_documents({"status": "available"})
    total_bookings = await db.bookings.count_documents({"status": {"$ne": "cancelled"}})
    
    # Calculate revenue stats
    paid_transactions = await db.payment_transactions.find({"status": "paid"}, {"_id": 0}).to_list(1000)
    total_revenue = sum(t.get("amount", 0) for t in paid_transactions)
    total_commission = sum(t.get("commission", 0) for t in paid_transactions)
    
    return {
        "total_users": total_users,
        "total_instructors": total_instructors,
        "pending_instructors": pending_instructors,
        "total_lessons": total_lessons,
        "total_bookings": total_bookings,
        "total_revenue": round(total_revenue, 2),
        "total_commission": round(total_commission, 2),
        "commission_rate": f"{int(PLATFORM_COMMISSION * 100)}%"
    }

@api_router.get("/admin/transactions")
async def get_transactions(request: Request):
    """Admin: Get all payment transactions"""
    await require_admin(request)
    
    transactions = await db.payment_transactions.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    for tx in transactions:
        if tx.get("user_id"):
            user = await db.users.find_one({"id": tx["user_id"]}, {"_id": 0})
            tx["user"] = user
        if tx.get("booking_id"):
            booking = await db.bookings.find_one({"id": tx["booking_id"]}, {"_id": 0})
            if booking:
                lesson = await db.lessons.find_one({"id": booking["lesson_id"]}, {"_id": 0})
                tx["lesson"] = lesson
    
    return transactions

# ============== REMINDER SYSTEM ==============

@api_router.post("/admin/send-reminders")
async def send_lesson_reminders(request: Request):
    """Admin: Manually trigger 24h lesson reminders"""
    await require_admin(request)
    
    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Find lessons for tomorrow
    lessons = await db.lessons.find({"date": tomorrow, "status": {"$ne": "cancelled"}}, {"_id": 0}).to_list(100)
    
    reminders_sent = 0
    for lesson in lessons:
        # Get instructor info
        instructor = await db.instructors.find_one({"id": lesson["instructor_id"]})
        instructor_user = await db.users.find_one({"id": instructor["user_id"]}) if instructor else None
        station = next((s for s in SKI_STATIONS if s["id"] == instructor.get("station_id", "")), None) if instructor else None
        
        # Get bookings for this lesson
        bookings = await db.bookings.find({"lesson_id": lesson["id"], "status": {"$ne": "cancelled"}}).to_list(100)
        
        for booking in bookings:
            user = await db.users.find_one({"id": booking["user_id"]})
            if user:
                await email_service.send_lesson_reminder(
                    user_email=user["email"],
                    user_name=user["name"],
                    lesson_title=lesson["title"],
                    lesson_date=lesson["date"],
                    lesson_time=f"{lesson['start_time']} - {lesson['end_time']}",
                    instructor_name=instructor_user["name"] if instructor_user else "Moniteur",
                    station=station["name"] if station else "Non spécifiée"
                )
                reminders_sent += 1
    
    return {"message": f"{reminders_sent} rappel(s) envoyé(s)"}

# ============== UTILITY ROUTES ==============

@api_router.get("/")
async def root():
    return {"message": "SkiMonitor API", "commission_rate": f"{int(PLATFORM_COMMISSION * 100)}%"}

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
