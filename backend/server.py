from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends, Query
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import io
import csv
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

# Weather API
OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY', '')

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

# ============== SKI STATIONS DATA (avec coordonnées GPS pour météo) ==============

SKI_STATIONS = [
    # Savoie
    {"id": "courchevel", "name": "Courchevel", "region": "Savoie", "altitude": 1850, "lat": 45.4167, "lon": 6.6333},
    {"id": "meribel", "name": "Méribel", "region": "Savoie", "altitude": 1450, "lat": 45.3967, "lon": 6.5656},
    {"id": "val-thorens", "name": "Val Thorens", "region": "Savoie", "altitude": 2300, "lat": 45.2983, "lon": 6.5800},
    {"id": "les-menuires", "name": "Les Menuires", "region": "Savoie", "altitude": 1850, "lat": 45.3236, "lon": 6.5328},
    {"id": "tignes", "name": "Tignes", "region": "Savoie", "altitude": 2100, "lat": 45.4686, "lon": 6.9064},
    {"id": "val-disere", "name": "Val d'Isère", "region": "Savoie", "altitude": 1850, "lat": 45.4478, "lon": 6.9797},
    {"id": "les-arcs", "name": "Les Arcs", "region": "Savoie", "altitude": 1600, "lat": 45.5703, "lon": 6.8269},
    {"id": "la-plagne", "name": "La Plagne", "region": "Savoie", "altitude": 1970, "lat": 45.5058, "lon": 6.6772},
    {"id": "la-rosiere", "name": "La Rosière", "region": "Savoie", "altitude": 1850},
    {"id": "sainte-foy", "name": "Sainte-Foy-Tarentaise", "region": "Savoie", "altitude": 1550},
    {"id": "valmorel", "name": "Valmorel", "region": "Savoie", "altitude": 1400},
    {"id": "pralognan", "name": "Pralognan-la-Vanoise", "region": "Savoie", "altitude": 1410},
    {"id": "aussois", "name": "Aussois", "region": "Savoie", "altitude": 1500},
    {"id": "bonneval", "name": "Bonneval-sur-Arc", "region": "Savoie", "altitude": 1800},
    {"id": "bessans", "name": "Bessans", "region": "Savoie", "altitude": 1750},
    {"id": "orelle", "name": "Orelle", "region": "Savoie", "altitude": 900},
    {"id": "saint-francois", "name": "Saint-François-Longchamp", "region": "Savoie", "altitude": 1450},
    {"id": "valloire", "name": "Valloire", "region": "Savoie", "altitude": 1430},
    {"id": "valmeinier", "name": "Valmeinier", "region": "Savoie", "altitude": 1500},
    {"id": "valfrejus", "name": "Valfréjus", "region": "Savoie", "altitude": 1550},
    {"id": "albiez", "name": "Albiez-Montrond", "region": "Savoie", "altitude": 1600},
    {"id": "saint-sorlin", "name": "Saint-Sorlin-d'Arves", "region": "Savoie", "altitude": 1600},
    {"id": "saint-colomban", "name": "Saint-Colomban-des-Villards", "region": "Savoie", "altitude": 1100},
    {"id": "le-corbier", "name": "Le Corbier", "region": "Savoie", "altitude": 1550},
    {"id": "la-toussuire", "name": "La Toussuire", "region": "Savoie", "altitude": 1700},
    {"id": "arêches-beaufort", "name": "Arêches-Beaufort", "region": "Savoie", "altitude": 1080},
    {"id": "les-saisies", "name": "Les Saisies", "region": "Savoie", "altitude": 1650},
    {"id": "crest-voland", "name": "Crest-Voland Cohennoz", "region": "Savoie", "altitude": 1230},
    {"id": "notre-dame-bellecombe", "name": "Notre-Dame-de-Bellecombe", "region": "Savoie", "altitude": 1150},
    {"id": "peisey-vallandry", "name": "Peisey-Vallandry", "region": "Savoie", "altitude": 1600},
    {"id": "champagny", "name": "Champagny-en-Vanoise", "region": "Savoie", "altitude": 1250},
    {"id": "montchavin", "name": "Montchavin-Les Coches", "region": "Savoie", "altitude": 1250},
    {"id": "brides-les-bains", "name": "Brides-les-Bains", "region": "Savoie", "altitude": 600},
    {"id": "saint-martin-belleville", "name": "Saint-Martin-de-Belleville", "region": "Savoie", "altitude": 1450},
    
    # Haute-Savoie
    {"id": "chamonix", "name": "Chamonix Mont-Blanc", "region": "Haute-Savoie", "altitude": 1035},
    {"id": "megeve", "name": "Megève", "region": "Haute-Savoie", "altitude": 1113},
    {"id": "saint-gervais", "name": "Saint-Gervais Mont-Blanc", "region": "Haute-Savoie", "altitude": 850},
    {"id": "les-contamines", "name": "Les Contamines-Montjoie", "region": "Haute-Savoie", "altitude": 1164},
    {"id": "combloux", "name": "Combloux", "region": "Haute-Savoie", "altitude": 1000},
    {"id": "avoriaz", "name": "Avoriaz", "region": "Haute-Savoie", "altitude": 1800},
    {"id": "morzine", "name": "Morzine", "region": "Haute-Savoie", "altitude": 1000},
    {"id": "les-gets", "name": "Les Gets", "region": "Haute-Savoie", "altitude": 1172},
    {"id": "chatel", "name": "Châtel", "region": "Haute-Savoie", "altitude": 1200},
    {"id": "la-chapelle-abondance", "name": "La Chapelle d'Abondance", "region": "Haute-Savoie", "altitude": 1020},
    {"id": "abondance", "name": "Abondance", "region": "Haute-Savoie", "altitude": 930},
    {"id": "la-clusaz", "name": "La Clusaz", "region": "Haute-Savoie", "altitude": 1100},
    {"id": "le-grand-bornand", "name": "Le Grand-Bornand", "region": "Haute-Savoie", "altitude": 1000},
    {"id": "manigod", "name": "Manigod", "region": "Haute-Savoie", "altitude": 1460},
    {"id": "saint-jean-sixt", "name": "Saint-Jean-de-Sixt", "region": "Haute-Savoie", "altitude": 963},
    {"id": "flaine", "name": "Flaine", "region": "Haute-Savoie", "altitude": 1600},
    {"id": "samoens", "name": "Samoëns", "region": "Haute-Savoie", "altitude": 720},
    {"id": "morillon", "name": "Morillon", "region": "Haute-Savoie", "altitude": 700},
    {"id": "sixt-fer-a-cheval", "name": "Sixt-Fer-à-Cheval", "region": "Haute-Savoie", "altitude": 760},
    {"id": "les-carroz", "name": "Les Carroz d'Arâches", "region": "Haute-Savoie", "altitude": 1140},
    {"id": "praz-de-lys", "name": "Praz de Lys Sommand", "region": "Haute-Savoie", "altitude": 1500},
    {"id": "les-brasses", "name": "Les Brasses", "region": "Haute-Savoie", "altitude": 1000},
    {"id": "le-semnoz", "name": "Le Semnoz", "region": "Haute-Savoie", "altitude": 1704},
    {"id": "bernex", "name": "Bernex Dent d'Oche", "region": "Haute-Savoie", "altitude": 1000},
    {"id": "thollon", "name": "Thollon-les-Mémises", "region": "Haute-Savoie", "altitude": 1000},
    {"id": "habere-poche", "name": "Habère-Poche", "region": "Haute-Savoie", "altitude": 945},
    {"id": "le-reposoir", "name": "Le Reposoir", "region": "Haute-Savoie", "altitude": 980},
    {"id": "les-houches", "name": "Les Houches", "region": "Haute-Savoie", "altitude": 1008},
    {"id": "servoz", "name": "Servoz", "region": "Haute-Savoie", "altitude": 816},
    {"id": "vallorcine", "name": "Vallorcine", "region": "Haute-Savoie", "altitude": 1260},
    {"id": "argentiere", "name": "Argentière", "region": "Haute-Savoie", "altitude": 1252},
    
    # Isère
    {"id": "les-2-alpes", "name": "Les 2 Alpes", "region": "Isère", "altitude": 1650},
    {"id": "alpe-dhuez", "name": "Alpe d'Huez", "region": "Isère", "altitude": 1860},
    {"id": "vaujany", "name": "Vaujany", "region": "Isère", "altitude": 1250},
    {"id": "oz-en-oisans", "name": "Oz-en-Oisans", "region": "Isère", "altitude": 1350},
    {"id": "auris", "name": "Auris-en-Oisans", "region": "Isère", "altitude": 1600},
    {"id": "villard-de-lans", "name": "Villard-de-Lans", "region": "Isère", "altitude": 1050},
    {"id": "correncon", "name": "Corrençon-en-Vercors", "region": "Isère", "altitude": 1111},
    {"id": "autrans", "name": "Autrans-Méaudre", "region": "Isère", "altitude": 1050},
    {"id": "lans-en-vercors", "name": "Lans-en-Vercors", "region": "Isère", "altitude": 1020},
    {"id": "chamrousse", "name": "Chamrousse", "region": "Isère", "altitude": 1650},
    {"id": "les-7-laux", "name": "Les 7 Laux", "region": "Isère", "altitude": 1350},
    {"id": "le-collet", "name": "Le Collet d'Allevard", "region": "Isère", "altitude": 1450},
    {"id": "saint-pierre-chartreuse", "name": "Saint-Pierre-de-Chartreuse", "region": "Isère", "altitude": 900},
    {"id": "col-de-porte", "name": "Col de Porte", "region": "Isère", "altitude": 1326},
    {"id": "la-grave", "name": "La Grave - La Meije", "region": "Isère", "altitude": 1450},
    {"id": "venosc", "name": "Venosc", "region": "Isère", "altitude": 1000},
    {"id": "mont-de-lans", "name": "Mont-de-Lans", "region": "Isère", "altitude": 1300},
    {"id": "bourg-doisans", "name": "Bourg-d'Oisans", "region": "Isère", "altitude": 720},
    
    # Hautes-Alpes
    {"id": "serre-chevalier", "name": "Serre Chevalier", "region": "Hautes-Alpes", "altitude": 1200},
    {"id": "montgenevre", "name": "Montgenèvre", "region": "Hautes-Alpes", "altitude": 1860},
    {"id": "vars", "name": "Vars", "region": "Hautes-Alpes", "altitude": 1650},
    {"id": "risoul", "name": "Risoul", "region": "Hautes-Alpes", "altitude": 1850},
    {"id": "orcieres", "name": "Orcières Merlette", "region": "Hautes-Alpes", "altitude": 1850},
    {"id": "superdevoluy", "name": "SuperDévoluy", "region": "Hautes-Alpes", "altitude": 1500},
    {"id": "la-joue-du-loup", "name": "La Joue du Loup", "region": "Hautes-Alpes", "altitude": 1500},
    {"id": "ancelle", "name": "Ancelle", "region": "Hautes-Alpes", "altitude": 1350},
    {"id": "chaillol", "name": "Chaillol", "region": "Hautes-Alpes", "altitude": 1450},
    {"id": "laye", "name": "Laye", "region": "Hautes-Alpes", "altitude": 1170},
    {"id": "saint-leger-les-melezes", "name": "Saint-Léger-les-Mélèzes", "region": "Hautes-Alpes", "altitude": 1260},
    {"id": "puy-saint-vincent", "name": "Puy-Saint-Vincent", "region": "Hautes-Alpes", "altitude": 1400},
    {"id": "pelvoux", "name": "Pelvoux-Vallouise", "region": "Hautes-Alpes", "altitude": 1250},
    {"id": "les-orres", "name": "Les Orres", "region": "Hautes-Alpes", "altitude": 1650},
    {"id": "reallon", "name": "Réallon", "region": "Hautes-Alpes", "altitude": 1560},
    {"id": "crévoux", "name": "Crévoux", "region": "Hautes-Alpes", "altitude": 1600},
    {"id": "ceillac", "name": "Ceillac", "region": "Hautes-Alpes", "altitude": 1640},
    {"id": "molines-en-queyras", "name": "Molines-en-Queyras", "region": "Hautes-Alpes", "altitude": 1750},
    {"id": "saint-veran", "name": "Saint-Véran", "region": "Hautes-Alpes", "altitude": 2040},
    {"id": "abries", "name": "Abriès-Ristolas", "region": "Hautes-Alpes", "altitude": 1550},
    {"id": "aiguilles", "name": "Aiguilles", "region": "Hautes-Alpes", "altitude": 1470},
    {"id": "arvieux", "name": "Arvieux", "region": "Hautes-Alpes", "altitude": 1550},
    
    # Alpes-de-Haute-Provence
    {"id": "pra-loup", "name": "Pra Loup", "region": "Alpes-de-Haute-Provence", "altitude": 1600},
    {"id": "le-sauze", "name": "Le Sauze", "region": "Alpes-de-Haute-Provence", "altitude": 1400},
    {"id": "sainte-anne", "name": "Sainte-Anne la Condamine", "region": "Alpes-de-Haute-Provence", "altitude": 1800},
    {"id": "la-foux-dallos", "name": "La Foux d'Allos", "region": "Alpes-de-Haute-Provence", "altitude": 1800},
    {"id": "val-dallos", "name": "Val d'Allos", "region": "Alpes-de-Haute-Provence", "altitude": 1400},
    {"id": "chabanon", "name": "Chabanon", "region": "Alpes-de-Haute-Provence", "altitude": 1600},
    {"id": "montclar", "name": "Montclar", "region": "Alpes-de-Haute-Provence", "altitude": 1350},
    {"id": "saint-jean-montclar", "name": "Saint-Jean-Montclar", "region": "Alpes-de-Haute-Provence", "altitude": 1350},
    
    # Alpes-Maritimes
    {"id": "isola-2000", "name": "Isola 2000", "region": "Alpes-Maritimes", "altitude": 2000},
    {"id": "auron", "name": "Auron", "region": "Alpes-Maritimes", "altitude": 1600},
    {"id": "valberg", "name": "Valberg", "region": "Alpes-Maritimes", "altitude": 1700},
    {"id": "la-colmiane", "name": "La Colmiane", "region": "Alpes-Maritimes", "altitude": 1500},
    {"id": "gréolières", "name": "Gréolières-les-Neiges", "region": "Alpes-Maritimes", "altitude": 1450},
    {"id": "turini-camp-dargent", "name": "Turini Camp d'Argent", "region": "Alpes-Maritimes", "altitude": 1500},
    {"id": "roubion", "name": "Roubion-les-Buisses", "region": "Alpes-Maritimes", "altitude": 1420},
    {"id": "beuil", "name": "Beuil-les-Launes", "region": "Alpes-Maritimes", "altitude": 1470},
    {"id": "peïra-cava", "name": "Peïra-Cava", "region": "Alpes-Maritimes", "altitude": 1450},
    {"id": "saint-dalmas", "name": "Saint-Dalmas-le-Selvage", "region": "Alpes-Maritimes", "altitude": 1500},
    
    # Pyrénées-Atlantiques
    {"id": "gourette", "name": "Gourette", "region": "Pyrénées-Atlantiques", "altitude": 1400},
    {"id": "la-pierre-saint-martin", "name": "La Pierre Saint-Martin", "region": "Pyrénées-Atlantiques", "altitude": 1527},
    {"id": "artouste", "name": "Artouste", "region": "Pyrénées-Atlantiques", "altitude": 1400},
    {"id": "iraty", "name": "Iraty", "region": "Pyrénées-Atlantiques", "altitude": 1327},
    {"id": "issarbe", "name": "Issarbe", "region": "Pyrénées-Atlantiques", "altitude": 1450},
    
    # Hautes-Pyrénées
    {"id": "cauterets", "name": "Cauterets", "region": "Hautes-Pyrénées", "altitude": 932},
    {"id": "luz-ardiden", "name": "Luz-Ardiden", "region": "Hautes-Pyrénées", "altitude": 1680},
    {"id": "grand-tourmalet", "name": "Grand Tourmalet", "region": "Hautes-Pyrénées", "altitude": 1800},
    {"id": "barèges", "name": "Barèges", "region": "Hautes-Pyrénées", "altitude": 1250},
    {"id": "la-mongie", "name": "La Mongie", "region": "Hautes-Pyrénées", "altitude": 1800},
    {"id": "gavarnie", "name": "Gavarnie-Gèdre", "region": "Hautes-Pyrénées", "altitude": 1850},
    {"id": "piau-engaly", "name": "Piau-Engaly", "region": "Hautes-Pyrénées", "altitude": 1850},
    {"id": "saint-lary", "name": "Saint-Lary-Soulan", "region": "Hautes-Pyrénées", "altitude": 1680},
    {"id": "peyragudes", "name": "Peyragudes", "region": "Hautes-Pyrénées", "altitude": 1600},
    {"id": "val-louron", "name": "Val Louron", "region": "Hautes-Pyrénées", "altitude": 1450},
    {"id": "nistos", "name": "Nistos", "region": "Hautes-Pyrénées", "altitude": 1500},
    {"id": "hautacam", "name": "Hautacam", "region": "Hautes-Pyrénées", "altitude": 1500},
    {"id": "payolle", "name": "Payolle", "region": "Hautes-Pyrénées", "altitude": 1100},
    
    # Haute-Garonne
    {"id": "luchon-superbagneres", "name": "Luchon-Superbagnères", "region": "Haute-Garonne", "altitude": 1800},
    {"id": "le-mourtis", "name": "Le Mourtis", "region": "Haute-Garonne", "altitude": 1350},
    {"id": "bourg-doueil", "name": "Bourg-d'Oueil", "region": "Haute-Garonne", "altitude": 1350},
    
    # Ariège
    {"id": "ax-3-domaines", "name": "Ax 3 Domaines", "region": "Ariège", "altitude": 1400},
    {"id": "les-monts-dolmes", "name": "Les Monts d'Olmes", "region": "Ariège", "altitude": 1500},
    {"id": "guzet", "name": "Guzet-Neige", "region": "Ariège", "altitude": 1400},
    {"id": "mijanès-donezan", "name": "Mijanès-Donezan", "region": "Ariège", "altitude": 1530},
    {"id": "ascou-pailhères", "name": "Ascou-Pailhères", "region": "Ariège", "altitude": 1500},
    {"id": "le-chioula", "name": "Le Chioula", "region": "Ariège", "altitude": 1240},
    {"id": "beille", "name": "Beille", "region": "Ariège", "altitude": 1800},
    {"id": "etang-de-lers", "name": "Étang de Lers", "region": "Ariège", "altitude": 1270},
    
    # Pyrénées-Orientales
    {"id": "font-romeu", "name": "Font-Romeu Pyrénées 2000", "region": "Pyrénées-Orientales", "altitude": 1800},
    {"id": "les-angles", "name": "Les Angles", "region": "Pyrénées-Orientales", "altitude": 1650},
    {"id": "formiguères", "name": "Formiguères", "region": "Pyrénées-Orientales", "altitude": 1500},
    {"id": "puyvalador", "name": "Puyvalador", "region": "Pyrénées-Orientales", "altitude": 1700},
    {"id": "porté-puymorens", "name": "Porté-Puymorens", "region": "Pyrénées-Orientales", "altitude": 1600},
    {"id": "cambre-daze", "name": "Cambre d'Aze", "region": "Pyrénées-Orientales", "altitude": 1700},
    {"id": "espace-cambre-daze", "name": "Espace Cambre d'Aze", "region": "Pyrénées-Orientales", "altitude": 1700},
    {"id": "err-puigmal", "name": "Err-Puigmal", "region": "Pyrénées-Orientales", "altitude": 1850},
    {"id": "la-quillane", "name": "La Quillane", "region": "Pyrénées-Orientales", "altitude": 1714},
    {"id": "le-capcir", "name": "Le Capcir", "region": "Pyrénées-Orientales", "altitude": 1500},
    
    # Aude
    {"id": "camurac", "name": "Camurac", "region": "Aude", "altitude": 1400},
    {"id": "les-monts-dolmes-pradelles", "name": "Ascou-Pailhères", "region": "Aude", "altitude": 1500},
    
    # Vosges
    {"id": "la-bresse", "name": "La Bresse Hohneck", "region": "Vosges", "altitude": 900},
    {"id": "gerardmer", "name": "Gérardmer", "region": "Vosges", "altitude": 750},
    {"id": "ventron", "name": "Ventron", "region": "Vosges", "altitude": 850},
    {"id": "le-markstein", "name": "Le Markstein", "region": "Haut-Rhin", "altitude": 1200},
    {"id": "le-lac-blanc", "name": "Le Lac Blanc", "region": "Haut-Rhin", "altitude": 900},
    {"id": "le-schnepfenried", "name": "Le Schnepfenried", "region": "Haut-Rhin", "altitude": 1100},
    {"id": "le-grand-ballon", "name": "Le Grand Ballon", "region": "Haut-Rhin", "altitude": 1100},
    {"id": "le-champ-du-feu", "name": "Le Champ du Feu", "region": "Bas-Rhin", "altitude": 1100},
    {"id": "le-donon", "name": "Le Donon", "region": "Bas-Rhin", "altitude": 727},
    {"id": "rouge-gazon", "name": "Rouge Gazon", "region": "Vosges", "altitude": 1086},
    
    # Jura
    {"id": "les-rousses", "name": "Les Rousses", "region": "Jura", "altitude": 1120},
    {"id": "metabief", "name": "Métabief", "region": "Doubs", "altitude": 1000},
    {"id": "monts-jura", "name": "Monts Jura", "region": "Ain", "altitude": 900},
    {"id": "mijoux-la-faucille", "name": "Mijoux-La Faucille", "region": "Ain", "altitude": 1000},
    {"id": "lelex", "name": "Lélex-Crozet", "region": "Ain", "altitude": 900},
    
    # Massif Central
    {"id": "super-besse", "name": "Super Besse", "region": "Puy-de-Dôme", "altitude": 1350},
    {"id": "le-mont-dore", "name": "Le Mont-Dore", "region": "Puy-de-Dôme", "altitude": 1050},
    {"id": "chastreix-sancy", "name": "Chastreix-Sancy", "region": "Puy-de-Dôme", "altitude": 1350},
    {"id": "super-lioran", "name": "Super Lioran", "region": "Cantal", "altitude": 1160},
    {"id": "le-lioran", "name": "Le Lioran", "region": "Cantal", "altitude": 1160},
    {"id": "prat-de-bouc", "name": "Prat de Bouc", "region": "Cantal", "altitude": 1392},
    {"id": "laguiole-brameloup", "name": "Laguiole-Brameloup", "region": "Aveyron", "altitude": 1350},
    {"id": "nasbinals", "name": "Nasbinals", "region": "Lozère", "altitude": 1180},
    {"id": "le-bleymard", "name": "Le Bleymard Mont Lozère", "region": "Lozère", "altitude": 1400},
    
    # Corse
    {"id": "val-dese", "name": "Val d'Ese", "region": "Corse-du-Sud", "altitude": 1620},
    {"id": "ghisoni", "name": "Ghisoni Capanelle", "region": "Haute-Corse", "altitude": 1600},
    {"id": "haut-asco", "name": "Haut-Asco", "region": "Haute-Corse", "altitude": 1450},
    {"id": "vergio", "name": "Vergio", "region": "Haute-Corse", "altitude": 1400},
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

class Review(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    instructor_id: str
    user_id: str
    booking_id: Optional[str] = None
    rating: int  # 1-5 stars
    comment: str = ""
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

class ReviewCreate(BaseModel):
    instructor_id: str
    rating: int  # 1-5
    comment: str = ""
    booking_id: Optional[str] = None

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

# ============== INSTRUCTOR DASHBOARD STATS ==============

@api_router.get("/instructor/stats")
async def get_instructor_stats(request: Request):
    """Get instructor dashboard statistics"""
    user = await require_instructor(request)
    instructor = await db.instructors.find_one({"user_id": user.id})
    
    if not instructor:
        raise HTTPException(status_code=404, detail="Profil moniteur non trouvé")
    
    # Get all lessons
    lessons = await db.lessons.find({"instructor_id": instructor["id"]}, {"_id": 0}).to_list(1000)
    
    # Get all bookings for instructor's lessons
    lesson_ids = [l["id"] for l in lessons]
    bookings = await db.bookings.find({"lesson_id": {"$in": lesson_ids}}, {"_id": 0}).to_list(1000)
    
    # Get transactions
    booking_ids = [b["id"] for b in bookings]
    transactions = await db.payment_transactions.find({
        "booking_id": {"$in": booking_ids},
        "status": "paid"
    }, {"_id": 0}).to_list(1000)
    
    # Calculate stats
    total_lessons = len(lessons)
    available_lessons = len([l for l in lessons if l["status"] == "available"])
    completed_lessons = len([l for l in lessons if l["date"] < datetime.now(timezone.utc).strftime("%Y-%m-%d")])
    
    total_bookings = len([b for b in bookings if b["status"] != "cancelled"])
    confirmed_bookings = len([b for b in bookings if b["status"] == "confirmed"])
    
    total_revenue = sum(t.get("instructor_amount", 0) for t in transactions)
    total_commission_paid = sum(t.get("commission", 0) for t in transactions)
    
    # Monthly revenue (last 6 months)
    monthly_revenue = {}
    for t in transactions:
        created = t.get("created_at", "")
        if isinstance(created, str) and len(created) >= 7:
            month_key = created[:7]  # YYYY-MM
            monthly_revenue[month_key] = monthly_revenue.get(month_key, 0) + t.get("instructor_amount", 0)
    
    # Upcoming lessons
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    upcoming_lessons = sorted(
        [l for l in lessons if l["date"] >= today and l["status"] != "cancelled"],
        key=lambda x: (x["date"], x["start_time"])
    )[:10]
    
    # Add booking info to upcoming lessons
    for lesson in upcoming_lessons:
        lesson_bookings = [b for b in bookings if b["lesson_id"] == lesson["id"] and b["status"] != "cancelled"]
        for booking in lesson_bookings:
            client = await db.users.find_one({"id": booking["user_id"]}, {"_id": 0})
            booking["user"] = client
        lesson["bookings"] = lesson_bookings
    
    return {
        "total_lessons": total_lessons,
        "available_lessons": available_lessons,
        "completed_lessons": completed_lessons,
        "total_bookings": total_bookings,
        "confirmed_bookings": confirmed_bookings,
        "total_revenue": round(total_revenue, 2),
        "total_commission_paid": round(total_commission_paid, 2),
        "monthly_revenue": monthly_revenue,
        "upcoming_lessons": upcoming_lessons
    }

@api_router.get("/instructor/export")
async def export_instructor_data(request: Request, year: Optional[int] = None, month: Optional[int] = None):
    """Export instructor transactions for accounting (CSV)"""
    user = await require_instructor(request)
    instructor = await db.instructors.find_one({"user_id": user.id})
    
    if not instructor:
        raise HTTPException(status_code=404, detail="Profil moniteur non trouvé")
    
    # Get all lessons
    lessons = await db.lessons.find({"instructor_id": instructor["id"]}, {"_id": 0}).to_list(1000)
    lesson_ids = [l["id"] for l in lessons]
    lessons_dict = {l["id"]: l for l in lessons}
    
    # Get bookings
    bookings = await db.bookings.find({"lesson_id": {"$in": lesson_ids}}, {"_id": 0}).to_list(1000)
    bookings_dict = {b["id"]: b for b in bookings}
    
    # Get transactions
    query = {"booking_id": {"$in": [b["id"] for b in bookings]}, "status": "paid"}
    transactions = await db.payment_transactions.find(query, {"_id": 0}).to_list(1000)
    
    # Filter by year/month if specified
    if year:
        transactions = [t for t in transactions if t.get("created_at", "").startswith(str(year))]
    if month:
        month_str = f"{year or datetime.now().year}-{month:02d}"
        transactions = [t for t in transactions if t.get("created_at", "").startswith(month_str)]
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    
    # Header
    writer.writerow([
        "Date",
        "N° Transaction",
        "Client",
        "Cours",
        "Date du cours",
        "Montant total (€)",
        "Commission plateforme (€)",
        "Montant net (€)",
        "Statut"
    ])
    
    # Data rows
    for tx in sorted(transactions, key=lambda x: x.get("created_at", "")):
        booking = bookings_dict.get(tx.get("booking_id", ""), {})
        lesson = lessons_dict.get(booking.get("lesson_id", ""), {})
        client = await db.users.find_one({"id": booking.get("user_id", "")}, {"_id": 0})
        
        writer.writerow([
            tx.get("created_at", "")[:10] if tx.get("created_at") else "",
            tx.get("id", "")[:8],
            client.get("name", "Inconnu") if client else "Inconnu",
            lesson.get("title", ""),
            lesson.get("date", ""),
            f"{tx.get('amount', 0):.2f}",
            f"{tx.get('commission', 0):.2f}",
            f"{tx.get('instructor_amount', 0):.2f}",
            "Payé"
        ])
    
    # Total row
    total_amount = sum(t.get("amount", 0) for t in transactions)
    total_commission = sum(t.get("commission", 0) for t in transactions)
    total_net = sum(t.get("instructor_amount", 0) for t in transactions)
    
    writer.writerow([])
    writer.writerow([
        "TOTAL", "", "", "", "",
        f"{total_amount:.2f}",
        f"{total_commission:.2f}",
        f"{total_net:.2f}",
        ""
    ])
    
    output.seek(0)
    
    filename = f"export_skimonitor_{user.name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv"
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ============== ADMIN EXPORT ==============

@api_router.get("/admin/export")
async def export_admin_data(request: Request, year: Optional[int] = None, month: Optional[int] = None):
    """Admin: Export all transactions for accounting (CSV)"""
    await require_admin(request)
    
    query = {"status": "paid"}
    transactions = await db.payment_transactions.find(query, {"_id": 0}).to_list(10000)
    
    # Filter by year/month if specified
    if year:
        transactions = [t for t in transactions if t.get("created_at", "").startswith(str(year))]
    if month:
        month_str = f"{year or datetime.now().year}-{month:02d}"
        transactions = [t for t in transactions if t.get("created_at", "").startswith(month_str)]
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    
    # Header
    writer.writerow([
        "Date",
        "N° Transaction",
        "Client",
        "Email client",
        "Moniteur",
        "Cours",
        "Date du cours",
        "Montant total (€)",
        "Commission plateforme (€)",
        "Montant moniteur (€)",
        "Statut"
    ])
    
    # Data rows
    for tx in sorted(transactions, key=lambda x: x.get("created_at", "")):
        booking = await db.bookings.find_one({"id": tx.get("booking_id", "")}, {"_id": 0})
        client = await db.users.find_one({"id": tx.get("user_id", "")}, {"_id": 0}) if tx.get("user_id") else None
        lesson = await db.lessons.find_one({"id": booking.get("lesson_id", "")}, {"_id": 0}) if booking else None
        instructor = await db.instructors.find_one({"id": lesson.get("instructor_id", "")}, {"_id": 0}) if lesson else None
        instructor_user = await db.users.find_one({"id": instructor.get("user_id", "")}, {"_id": 0}) if instructor else None
        
        writer.writerow([
            tx.get("created_at", "")[:10] if tx.get("created_at") else "",
            tx.get("id", "")[:8],
            client.get("name", "Inconnu") if client else "Inconnu",
            client.get("email", "") if client else "",
            instructor_user.get("name", "Inconnu") if instructor_user else "Inconnu",
            lesson.get("title", "") if lesson else "",
            lesson.get("date", "") if lesson else "",
            f"{tx.get('amount', 0):.2f}",
            f"{tx.get('commission', 0):.2f}",
            f"{tx.get('instructor_amount', 0):.2f}",
            "Payé"
        ])
    
    # Total row
    total_amount = sum(t.get("amount", 0) for t in transactions)
    total_commission = sum(t.get("commission", 0) for t in transactions)
    total_net = sum(t.get("instructor_amount", 0) for t in transactions)
    
    writer.writerow([])
    writer.writerow([
        "TOTAL", "", "", "", "", "", "",
        f"{total_amount:.2f}",
        f"{total_commission:.2f}",
        f"{total_net:.2f}",
        ""
    ])
    
    output.seek(0)
    
    filename = f"export_skimonitor_admin_{datetime.now().strftime('%Y%m%d')}.csv"
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ============== WEATHER API ==============

# Coordinates for major stations (fallback)
STATION_COORDS = {
    "chamonix": {"lat": 45.9237, "lon": 6.8694},
    "courchevel": {"lat": 45.4167, "lon": 6.6333},
    "meribel": {"lat": 45.3967, "lon": 6.5656},
    "val-thorens": {"lat": 45.2983, "lon": 6.5800},
    "tignes": {"lat": 45.4686, "lon": 6.9064},
    "val-disere": {"lat": 45.4478, "lon": 6.9797},
    "les-arcs": {"lat": 45.5703, "lon": 6.8269},
    "la-plagne": {"lat": 45.5058, "lon": 6.6772},
    "avoriaz": {"lat": 46.1919, "lon": 6.7747},
    "morzine": {"lat": 46.1797, "lon": 6.7094},
    "megeve": {"lat": 45.8567, "lon": 6.6175},
    "les-2-alpes": {"lat": 45.0167, "lon": 6.1333},
    "alpe-dhuez": {"lat": 45.0922, "lon": 6.0694},
    "serre-chevalier": {"lat": 44.9333, "lon": 6.5667},
    "la-clusaz": {"lat": 45.9047, "lon": 6.4239},
    "les-gets": {"lat": 46.1586, "lon": 6.6697},
    "flaine": {"lat": 46.0058, "lon": 6.6889},
    "les-menuires": {"lat": 45.3236, "lon": 6.5328},
    "saint-gervais": {"lat": 45.8919, "lon": 6.7128},
    "les-contamines": {"lat": 45.8206, "lon": 6.7267},
}

@api_router.get("/weather/{station_id}")
async def get_weather(station_id: str):
    """Get weather for a ski station"""
    # Find station
    station = next((s for s in SKI_STATIONS if s["id"] == station_id), None)
    if not station:
        raise HTTPException(status_code=404, detail="Station non trouvée")
    
    # Get coordinates
    coords = STATION_COORDS.get(station_id)
    if not coords:
        # Use station data if available
        if station.get("lat") and station.get("lon"):
            coords = {"lat": station["lat"], "lon": station["lon"]}
        else:
            # Return simulated weather if no coordinates
            return get_simulated_weather(station)
    
    # Check if API key is configured
    if not OPENWEATHER_API_KEY:
        return get_simulated_weather(station)
    
    try:
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={
                    "lat": coords["lat"],
                    "lon": coords["lon"],
                    "appid": OPENWEATHER_API_KEY,
                    "units": "metric",
                    "lang": "fr"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "station_id": station_id,
                    "station_name": station["name"],
                    "temperature": round(data["main"]["temp"]),
                    "feels_like": round(data["main"]["feels_like"]),
                    "humidity": data["main"]["humidity"],
                    "description": data["weather"][0]["description"].capitalize(),
                    "icon": data["weather"][0]["icon"],
                    "wind_speed": round(data["wind"]["speed"] * 3.6),  # m/s to km/h
                    "visibility": data.get("visibility", 10000) // 1000,  # meters to km
                    "snow": data.get("snow", {}).get("1h", 0),
                    "clouds": data["clouds"]["all"],
                    "source": "openweathermap"
                }
            else:
                return get_simulated_weather(station)
    except Exception as e:
        logger.error(f"Weather API error: {e}")
        return get_simulated_weather(station)

def get_simulated_weather(station: dict):
    """Generate realistic simulated weather for ski station"""
    import random
    
    # Base temperature varies with altitude
    altitude = station.get("altitude", 1500)
    base_temp = -5 - (altitude - 1000) * 0.006  # -6°C per 1000m
    
    # Add some randomness
    temp = round(base_temp + random.uniform(-5, 5))
    
    # Weather conditions weighted for winter ski resort
    conditions = [
        {"description": "Ciel dégagé", "icon": "01d", "weight": 20},
        {"description": "Peu nuageux", "icon": "02d", "weight": 15},
        {"description": "Nuageux", "icon": "03d", "weight": 20},
        {"description": "Couvert", "icon": "04d", "weight": 15},
        {"description": "Neige légère", "icon": "13d", "weight": 15},
        {"description": "Neige", "icon": "13d", "weight": 10},
        {"description": "Brouillard", "icon": "50d", "weight": 5},
    ]
    
    # Weighted random selection
    total_weight = sum(c["weight"] for c in conditions)
    r = random.uniform(0, total_weight)
    cumulative = 0
    selected = conditions[0]
    for c in conditions:
        cumulative += c["weight"]
        if r <= cumulative:
            selected = c
            break
    
    return {
        "station_id": station["id"],
        "station_name": station["name"],
        "temperature": temp,
        "feels_like": temp - random.randint(2, 5),
        "humidity": random.randint(50, 90),
        "description": selected["description"],
        "icon": selected["icon"],
        "wind_speed": random.randint(5, 40),
        "visibility": random.randint(5, 20),
        "snow": random.choice([0, 0, 0, 2, 5, 10, 15]) if "Neige" in selected["description"] else 0,
        "clouds": random.randint(0, 100),
        "source": "simulated"
    }

# ============== REVIEWS ==============

@api_router.post("/reviews")
async def create_review(review_data: ReviewCreate, request: Request):
    """Create a review for an instructor"""
    user = await get_user_from_request(request)
    if not user:
        raise HTTPException(status_code=401, detail="Non authentifié")

    # Validate rating
    if review_data.rating < 1 or review_data.rating > 5:
        raise HTTPException(status_code=400, detail="La note doit être entre 1 et 5")

    # Check if instructor exists
    instructor = await db.instructors.find_one({"id": review_data.instructor_id})
    if not instructor:
        raise HTTPException(status_code=404, detail="Moniteur non trouvé")

    # Check if user already reviewed this instructor
    existing_review = await db.reviews.find_one({
        "user_id": user["id"],
        "instructor_id": review_data.instructor_id
    })
    if existing_review:
        raise HTTPException(status_code=400, detail="Vous avez déjà laissé un avis pour ce moniteur")

    # Create review
    review = Review(
        instructor_id=review_data.instructor_id,
        user_id=user["id"],
        rating=review_data.rating,
        comment=review_data.comment,
        booking_id=review_data.booking_id
    )

    await db.reviews.insert_one(review.model_dump())
    return review

@api_router.get("/reviews")
async def get_reviews(instructor_id: str = Query(..., description="ID du moniteur")):
    """Get all reviews for an instructor"""
    reviews = []
    cursor = db.reviews.find({"instructor_id": instructor_id}).sort("created_at", -1)

    async for review in cursor:
        # Get user info
        user = await db.users.find_one({"id": review["user_id"]})
        review_with_user = {
            **review,
            "user_name": user["name"] if user else "Utilisateur",
            "user_picture": user.get("picture") if user else None
        }
        reviews.append(review_with_user)

    return reviews

@api_router.get("/instructors/{instructor_id}/rating")
async def get_instructor_rating(instructor_id: str):
    """Get instructor average rating and review count"""
    reviews = []
    cursor = db.reviews.find({"instructor_id": instructor_id})

    async for review in cursor:
        reviews.append(review)

    if not reviews:
        return {
            "instructor_id": instructor_id,
            "average_rating": 0,
            "review_count": 0
        }

    total_rating = sum(r["rating"] for r in reviews)
    average = total_rating / len(reviews)

    return {
        "instructor_id": instructor_id,
        "average_rating": round(average, 1),
        "review_count": len(reviews)
    }

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
