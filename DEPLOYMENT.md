# 🚀 Guide de déploiement SkiMonitor

## Backend

### Option 1 : Railway.app (Recommandé)

1. Créez un compte sur https://railway.app
2. Créez un nouveau projet
3. Ajoutez MongoDB depuis le marketplace
4. Ajoutez votre repo GitHub
5. Configurez les variables d'environnement :
   ```
   MONGO_URL=<fourni par Railway après ajout de MongoDB>
   DB_NAME=skimonitor
   STRIPE_API_KEY=sk_test_...
   CORS_ORIGINS=https://qallardorial-source.github.io
   ```
6. Railway détectera automatiquement le `railway.json` et déploiera

### Option 2 : Render.com

1. Créez un compte sur https://render.com
2. Créez un nouveau Web Service
3. Connectez votre repo GitHub
4. Configuration :
   - Build Command: `cd backend && pip install -r requirements.txt`
   - Start Command: `cd backend && uvicorn server:app --host 0.0.0.0 --port $PORT`
5. Ajoutez les variables d'environnement
6. Créez une base MongoDB Atlas (gratuit)

### Variables d'environnement requises

```bash
MONGO_URL=mongodb+srv://... # Votre connexion MongoDB
DB_NAME=skimonitor
STRIPE_API_KEY=sk_test_... # Votre clé Stripe
OPENWEATHER_API_KEY=... # Optionnel
CORS_ORIGINS=https://qallardorial-source.github.io
```

## Frontend (GitHub Pages)

Déjà configuré ! Il faut juste :

1. Merger toutes les PRs dans main
2. Ajouter le secret GitHub `REACT_APP_BACKEND_URL` :
   - Settings → Secrets and variables → Actions
   - New repository secret
   - Name: `REACT_APP_BACKEND_URL`
   - Value: URL de votre backend (ex: `https://votre-app.railway.app`)

3. Le workflow GitHub Actions déploiera automatiquement

## Test local

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env
# Éditez .env avec vos vraies valeurs
uvicorn server:app --reload

# Frontend
cd frontend
yarn install
yarn start
```

## Après déploiement

1. Visitez https://qallardorial-source.github.io/monitor/
2. Connectez-vous
3. Ouvrez la console (F12) et exécutez :
   ```javascript
   fetch('/api/auth/promote-to-admin', {
     method: 'POST',
     credentials: 'include'
   }).then(r => r.json()).then(console.log)
   ```
4. Rafraîchissez - vous êtes admin !
