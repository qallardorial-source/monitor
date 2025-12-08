#!/usr/bin/env python3
"""
Script de seeding pour créer des moniteurs fictifs mais réalistes
Option B : Données fictives réalistes
"""
import asyncio
import os
import sys
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
import uuid
from random import choice, sample, randint, uniform

# Load environment
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Données fictives réalistes
FICTIONAL_INSTRUCTORS = [
    {
        "name": "Pierre Dumont",
        "email": "pierre.dumont@skimonitor-demo.fr",
        "bio": "Moniteur diplômé d'État avec 12 ans d'expérience. Passionné par la transmission de ma passion du ski alpin, j'adapte mes cours à tous les niveaux avec patience et pédagogie.",
        "specialties": ["Ski alpin", "Hors-piste"],
        "ski_levels": ["Débutant", "Intermédiaire", "Avancé"],
        "hourly_rate": 65.0,
        "station": "courchevel"
    },
    {
        "name": "Sophie Martin",
        "email": "sophie.martin@skimonitor-demo.fr",
        "bio": "Ancienne membre de l'équipe de France de ski freestyle, je propose des cours de ski et snowboard avec une approche ludique et technique. Spécialiste des figures et du freestyle.",
        "specialties": ["Snowboard", "Freestyle", "Ski alpin"],
        "ski_levels": ["Intermédiaire", "Avancé", "Expert"],
        "hourly_rate": 75.0,
        "station": "val-thorens"
    },
    {
        "name": "Marc Bertrand",
        "email": "marc.bertrand@skimonitor-demo.fr",
        "bio": "Moniteur ESF depuis 8 ans, je me spécialise dans l'enseignement aux enfants et débutants. Patience et bonne humeur garanties pour progresser en toute confiance !",
        "specialties": ["Ski alpin", "Ski de fond"],
        "ski_levels": ["Débutant", "Intermédiaire"],
        "hourly_rate": 55.0,
        "station": "meribel"
    },
    {
        "name": "Julie Rousseau",
        "email": "julie.rousseau@skimonitor-demo.fr",
        "bio": "Guide de haute montagne et monitrice de ski, j'organise des sorties hors-piste exceptionnelles et des cours techniques pour skieurs confirmés. Sécurité et plaisir avant tout !",
        "specialties": ["Hors-piste", "Ski alpin"],
        "ski_levels": ["Avancé", "Expert"],
        "hourly_rate": 85.0,
        "station": "chamonix"
    },
    {
        "name": "Thomas Leroy",
        "email": "thomas.leroy@skimonitor-demo.fr",
        "bio": "Moniteur polyvalent avec 15 ans d'expérience dans différentes stations alpines. J'enseigne le ski et le snowboard à tous les niveaux avec une approche personnalisée.",
        "specialties": ["Ski alpin", "Snowboard"],
        "ski_levels": ["Débutant", "Intermédiaire", "Avancé", "Expert"],
        "hourly_rate": 70.0,
        "station": "tignes"
    },
    {
        "name": "Emma Dubois",
        "email": "emma.dubois@skimonitor-demo.fr",
        "bio": "Spécialiste du ski de fond et des cours pour enfants. Mon objectif : faire découvrir les joies du ski nordique dans un cadre naturel exceptionnel avec patience et enthousiasme.",
        "specialties": ["Ski de fond", "Ski alpin"],
        "ski_levels": ["Débutant", "Intermédiaire"],
        "hourly_rate": 50.0,
        "station": "les-saisies"
    },
    {
        "name": "Lucas Moreau",
        "email": "lucas.moreau@skimonitor-demo.fr",
        "bio": "Champion régional de snowboard, je partage ma passion pour le freestyle et le freeride. Cours dynamiques et techniques pour progresser rapidement tout en s'amusant !",
        "specialties": ["Snowboard", "Freestyle"],
        "ski_levels": ["Intermédiaire", "Avancé", "Expert"],
        "hourly_rate": 72.0,
        "station": "avoriaz"
    },
    {
        "name": "Chloé Bernard",
        "email": "chloe.bernard@skimonitor-demo.fr",
        "bio": "Monitrice diplômée spécialisée dans l'accompagnement des adultes débutants. Méthode douce et progressive pour vaincre vos appréhensions et prendre du plaisir sur les pistes.",
        "specialties": ["Ski alpin"],
        "ski_levels": ["Débutant", "Intermédiaire"],
        "hourly_rate": 58.0,
        "station": "megeve"
    },
    {
        "name": "Antoine Petit",
        "email": "antoine.petit@skimonitor-demo.fr",
        "bio": "Moniteur passionné avec une double compétence ski alpin et hors-piste. J'accompagne les skieurs expérimentés à la découverte des plus beaux itinéraires de montagne.",
        "specialties": ["Ski alpin", "Hors-piste"],
        "ski_levels": ["Avancé", "Expert"],
        "hourly_rate": 80.0,
        "station": "val-disere"
    },
    {
        "name": "Léa Fontaine",
        "email": "lea.fontaine@skimonitor-demo.fr",
        "bio": "Monitrice polyvalente et diplômée, j'enseigne le ski et le snowboard dans une ambiance conviviale. Spécialiste des cours collectifs et des groupes de tous âges.",
        "specialties": ["Ski alpin", "Snowboard", "Freestyle"],
        "ski_levels": ["Débutant", "Intermédiaire", "Avancé"],
        "hourly_rate": 62.0,
        "station": "les-arcs"
    },
]

# Avatar URLs génériques (illustrations/icônes)
AVATAR_URLS = [
    "https://api.dicebear.com/7.x/avataaars/svg?seed=Pierre",
    "https://api.dicebear.com/7.x/avataaars/svg?seed=Sophie",
    "https://api.dicebear.com/7.x/avataaars/svg?seed=Marc",
    "https://api.dicebear.com/7.x/avataaars/svg?seed=Julie",
    "https://api.dicebear.com/7.x/avataaars/svg?seed=Thomas",
    "https://api.dicebear.com/7.x/avataaars/svg?seed=Emma",
    "https://api.dicebear.com/7.x/avataaars/svg?seed=Lucas",
    "https://api.dicebear.com/7.x/avataaars/svg?seed=Chloe",
    "https://api.dicebear.com/7.x/avataaars/svg?seed=Antoine",
    "https://api.dicebear.com/7.x/avataaars/svg?seed=Lea",
]

# Cours types pour générer des exemples
LESSON_TEMPLATES = [
    {
        "types": ["private"],
        "titles": [
            "Cours particulier de ski",
            "Coaching personnalisé ski alpin",
            "Perfectionnement technique",
        ],
        "descriptions": [
            "Cours individuel adapté à votre niveau pour une progression rapide et efficace.",
            "Session de coaching personnalisé pour travailler votre technique et gagner en confiance.",
        ]
    },
    {
        "types": ["group"],
        "titles": [
            "Stage collectif débutants",
            "Cours groupe niveau intermédiaire",
            "Session groupe perfectionnement",
        ],
        "descriptions": [
            "Cours en petit groupe dans une ambiance conviviale et motivante.",
            "Apprenez ensemble et progressez dans la bonne humeur !",
        ]
    },
]

async def seed_instructors():
    """Crée des moniteurs fictifs avec leurs utilisateurs et quelques cours d'exemple"""

    print("🎿 Début du seeding des moniteurs fictifs...\n")

    # Vérifier si des moniteurs existent déjà
    existing_count = await db.instructors.count_documents({"status": "approved"})
    if existing_count > 0:
        print(f"⚠️  {existing_count} moniteur(s) approuvé(s) trouvé(s) dans la base.")
        response = input("Voulez-vous continuer et ajouter les moniteurs fictifs ? (o/n): ")
        if response.lower() != 'o':
            print("❌ Seeding annulé.")
            return

    created_users = 0
    created_instructors = 0
    created_lessons = 0

    for idx, instructor_data in enumerate(FICTIONAL_INSTRUCTORS):
        # Vérifier si l'utilisateur existe déjà (par email)
        existing_user = await db.users.find_one({"email": instructor_data["email"]})

        if existing_user:
            print(f"ℹ️  Utilisateur {instructor_data['name']} existe déjà, passage...")
            continue

        # Créer l'utilisateur
        user_id = str(uuid.uuid4())
        user = {
            "id": user_id,
            "email": instructor_data["email"],
            "name": instructor_data["name"],
            "picture": AVATAR_URLS[idx],
            "role": "instructor",
            "created_at": datetime.now(timezone.utc)
        }

        await db.users.insert_one(user)
        created_users += 1
        print(f"✅ Utilisateur créé: {instructor_data['name']}")

        # Créer le profil instructeur (directement approuvé)
        instructor_id = str(uuid.uuid4())
        instructor = {
            "id": instructor_id,
            "user_id": user_id,
            "bio": instructor_data["bio"],
            "specialties": instructor_data["specialties"],
            "ski_levels": instructor_data["ski_levels"],
            "hourly_rate": instructor_data["hourly_rate"],
            "station_id": instructor_data["station"],
            "status": "approved",  # Directement approuvé
            "created_at": datetime.now(timezone.utc)
        }

        await db.instructors.insert_one(instructor)
        created_instructors += 1
        print(f"   → Profil moniteur approuvé: {instructor_data['station']}, {instructor_data['hourly_rate']}€/h")

        # Créer quelques cours d'exemple pour chaque moniteur
        num_lessons = randint(2, 4)
        for i in range(num_lessons):
            # Alterner entre cours privé et collectif
            lesson_type = "private" if i % 2 == 0 else "group"

            # Choisir un template de cours
            template = choice([t for t in LESSON_TEMPLATES if lesson_type in t["types"]])

            # Dates dans les 2 prochaines semaines
            days_ahead = randint(1, 14)
            lesson_date = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

            # Horaires aléatoires entre 9h et 16h
            start_hour = randint(9, 15)
            end_hour = start_hour + randint(1, 2)

            lesson_id = str(uuid.uuid4())
            lesson = {
                "id": lesson_id,
                "instructor_id": instructor_id,
                "lesson_type": lesson_type,
                "title": choice(template["titles"]),
                "description": choice(template["descriptions"]),
                "date": lesson_date,
                "start_time": f"{start_hour:02d}:00",
                "end_time": f"{end_hour:02d}:00",
                "max_participants": 1 if lesson_type == "private" else randint(4, 8),
                "current_participants": 0,
                "price": instructor_data["hourly_rate"] * (end_hour - start_hour),
                "status": "available",
                "is_recurring": False,
                "created_at": datetime.now(timezone.utc)
            }

            await db.lessons.insert_one(lesson)
            created_lessons += 1

        print(f"   → {num_lessons} cours créés\n")

    print("=" * 60)
    print(f"✨ Seeding terminé avec succès !")
    print(f"   📊 {created_users} utilisateurs créés")
    print(f"   🎿 {created_instructors} moniteurs approuvés créés")
    print(f"   📅 {created_lessons} cours d'exemple créés")
    print("=" * 60)
    print("\n💡 Les moniteurs sont maintenant visibles sur le site !")
    print("   Vous pouvez les voir sur : /instructors")
    print("   Et leurs cours sur : /lessons\n")

async def main():
    """Point d'entrée principal"""
    try:
        await seed_instructors()
    except Exception as e:
        print(f"\n❌ Erreur lors du seeding: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(main())
