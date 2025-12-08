# 🚀 Guide de Déploiement - SkiMonitor

## 📋 Vue d'ensemble

Votre projet est configuré pour être déployé sur **Railway** (recommandé) ou **Heroku**.

### Architecture
- **Frontend** : React (déployé sur GitHub Pages)
- **Backend** : FastAPI + Python (déployé sur Railway/Heroku)
- **Base de données** : MongoDB (MongoDB Atlas ou Railway)

---

## 🎯 Option 1 : Railway (RECOMMANDÉ - Le Plus Simple)

Railway détecte automatiquement votre configuration et déploie en quelques clics !

### Étape 1 : Créer un compte Railway

1. Allez sur [railway.app](https://railway.app)
2. Connectez-vous avec votre compte GitHub
3. Gratuit pour commencer (500h/mois incluses)

### Étape 2 : Déployer le Backend

#### Via l'interface Railway :

1. **New Project** → **Deploy from GitHub repo**
2. Sélectionnez votre repo `qallardorial-source/monitor`
3. Railway détecte automatiquement la configuration (`railway.json`)
4. Le backend se déploie automatiquement ! 🎉

### Étape 3 : Ajouter MongoDB

#### Option A : MongoDB via Railway (Plus Simple)

1. Dans votre projet Railway, cliquez **"+ New"**
2. Sélectionnez **"Database" → "Add MongoDB"**
3. Railway crée automatiquement une base MongoDB
4. Railway ajoute automatiquement les variables :
   - `MONGO_URL` ✅
   - `DATABASE_URL` ✅

#### Option B : MongoDB Atlas (Gratuit)

1. Créez un compte sur [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
2. Créez un **cluster gratuit** (M0)
3. **Database Access** → Créez un utilisateur
4. **Network Access** → Ajoutez `0.0.0.0/0` (accès depuis partout)
5. Copiez votre **connection string** :
   ```
   mongodb+srv://username:password@cluster.mongodb.net/
   ```

### Étape 4 : Configurer les Variables d'Environnement

Dans Railway, allez dans **Variables** et ajoutez :

#### Variables OBLIGATOIRES :

```env
MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/
DB_NAME=skimonitor
```

#### Variables OPTIONNELLES :

```env
# Stripe (pour les paiements)
STRIPE_API_KEY=sk_live_votre_clé_stripe

# OpenWeather (pour la météo)
OPENWEATHER_API_KEY=votre_clé_openweather

# CORS (origines autorisées)
CORS_ORIGINS=https://qallardorial-source.github.io

# Admin Secret (optionnel)
ADMIN_SECRET=votre_secret_admin
```

### Étape 5 : Obtenir l'URL du Backend

1. Railway génère automatiquement une URL : `https://votre-app.railway.app`
2. Testez : `https://votre-app.railway.app/api/stations`
3. Copiez cette URL pour le frontend

### Étape 6 : Configurer le Frontend

1. Dans GitHub, allez dans **Settings → Secrets and variables → Actions**
2. Ajoutez le secret :
   ```
   REACT_APP_BACKEND_URL=https://votre-app.railway.app
   ```
3. Le GitHub Actions redéploiera automatiquement avec la bonne URL

### Étape 7 : Créer un Compte Admin

Une fois déployé, créez votre premier admin :

```bash
# Méthode 1 : Via MongoDB Atlas UI
# Allez dans Collections → users → Insert Document
{
  "id": "admin-001",
  "email": "admin@skimonitor.fr",
  "name": "Admin",
  "role": "admin",
  "created_at": { "$date": "2025-12-08T10:00:00Z" }
}

# Méthode 2 : Via MongoDB Shell
use skimonitor
db.users.insertOne({
  id: "admin-001",
  email: "admin@skimonitor.fr",
  name: "Admin",
  role: "admin",
  created_at: new Date()
})
```

### ✅ Vérification Finale

1. **Backend** : `https://votre-app.railway.app/api/stations` → Doit retourner les stations
2. **Frontend** : `https://qallardorial-source.github.io/` → Doit charger
3. **Connexion** : Connectez-vous avec votre compte admin
4. **Seeding** : Lancez le seeding depuis la console (voir SEEDING_GUIDE.md)

---

## 🔧 Option 2 : Heroku

### Étape 1 : Installer Heroku CLI

```bash
# macOS
brew install heroku/brew/heroku

# Windows
# Téléchargez depuis heroku.com

# Linux
curl https://cli-assets.heroku.com/install.sh | sh
```

### Étape 2 : Créer l'Application

```bash
# Se connecter
heroku login

# Créer l'app
heroku create skimonitor-backend

# Ajouter MongoDB
heroku addons:create mongolab:sandbox
```

### Étape 3 : Configurer les Variables

```bash
# Variables obligatoires (si pas de addon MongoDB)
heroku config:set MONGO_URL=mongodb+srv://...
heroku config:set DB_NAME=skimonitor

# Variables optionnelles
heroku config:set STRIPE_API_KEY=sk_live_...
heroku config:set OPENWEATHER_API_KEY=...
heroku config:set CORS_ORIGINS=https://qallardorial-source.github.io
```

### Étape 4 : Déployer

```bash
# Depuis la racine du projet
git push heroku main

# Ou depuis votre branche
git push heroku claude/fix-homepage-redirect-01BKPQ8FimYHhe1NZqnBoTx9:main
```

### Étape 5 : Vérifier

```bash
# Ouvrir l'app
heroku open

# Voir les logs
heroku logs --tail
```

---

## 🐳 Option 3 : Docker (Avancé)

Si vous préférez Docker :

### Créer un Dockerfile

```dockerfile
# Dockerfile dans la racine
FROM python:3.11-slim

WORKDIR /app

# Copier requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code
COPY backend/ .

# Exposer le port
EXPOSE 8000

# Lancer le serveur
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Lancer avec Docker

```bash
# Build
docker build -t skimonitor-backend .

# Run
docker run -p 8000:8000 \
  -e MONGO_URL=mongodb://... \
  -e DB_NAME=skimonitor \
  skimonitor-backend
```

---

## 📊 Variables d'Environnement Complètes

| Variable | Obligatoire | Valeur par Défaut | Description |
|----------|-------------|-------------------|-------------|
| `MONGO_URL` | ✅ Oui | - | URL de connexion MongoDB |
| `DB_NAME` | ✅ Oui | - | Nom de la base de données |
| `STRIPE_API_KEY` | ❌ Non | `sk_test_emergent` | Clé API Stripe pour paiements |
| `OPENWEATHER_API_KEY` | ❌ Non | `''` | Clé API OpenWeather pour météo |
| `CORS_ORIGINS` | ❌ Non | `*` | Origines autorisées (séparées par virgule) |
| `ADMIN_SECRET` | ❌ Non | - | Secret pour opérations admin sensibles |
| `PORT` | ❌ Non | Auto | Port du serveur (auto sur Railway/Heroku) |

---

## 🔍 Dépannage

### Le backend ne démarre pas

```bash
# Vérifier les logs Railway
# Dans l'interface Railway → Deployments → View Logs

# Ou avec Heroku
heroku logs --tail

# Problèmes communs :
# 1. MONGO_URL mal configurée → Vérifiez le format
# 2. Port déjà utilisé → Railway/Heroku gèrent ça automatiquement
# 3. Dépendances manquantes → Vérifiez requirements.txt
```

### Erreur "Cannot connect to MongoDB"

```bash
# Vérifiez :
1. MONGO_URL est correcte
2. IP autorisée dans MongoDB Atlas (0.0.0.0/0)
3. Username/password corrects
4. Nom de la base existe
```

### CORS Error sur le frontend

```bash
# Ajoutez l'origine du frontend dans CORS_ORIGINS
heroku config:set CORS_ORIGINS=https://qallardorial-source.github.io

# Ou sur Railway, dans Variables :
CORS_ORIGINS=https://qallardorial-source.github.io
```

### Le seeding ne fonctionne pas

```bash
# 1. Vérifiez que vous êtes admin
db.users.updateOne(
  {email: "votre@email.com"},
  {$set: {role: "admin"}}
)

# 2. Vérifiez que le backend est bien déployé avec la dernière version
# 3. Testez l'endpoint :
curl -X POST https://votre-app.railway.app/api/admin/seed-instructors \
  -H "Cookie: votre_cookie_session"
```

---

## 🎯 Checklist de Déploiement

- [ ] Backend déployé sur Railway/Heroku
- [ ] MongoDB configuré (Atlas ou Railway)
- [ ] Variables d'environnement ajoutées
- [ ] URL backend copiée
- [ ] Frontend configuré avec REACT_APP_BACKEND_URL
- [ ] Compte admin créé
- [ ] Test : `/api/stations` fonctionne
- [ ] Connexion admin fonctionne
- [ ] Seeding exécuté avec succès
- [ ] `/instructors` affiche les moniteurs
- [ ] `/lessons` affiche les cours

---

## 💡 Recommandations

### Pour le Développement
- Utilisez **Railway** (gratuit, simple, auto-deploy)
- **MongoDB Atlas** free tier (512 MB gratuits)
- Variables d'env de développement

### Pour la Production
- Passez à un plan payant Railway ($5/mois)
- Ajoutez un nom de domaine personnalisé
- Configurez des vraies clés Stripe (live)
- Ajoutez des sauvegardes MongoDB
- Activez le monitoring

---

## 🚀 Prêt à Déployer ?

La méthode la plus simple :

1. **Railway.app** → New Project → GitHub repo
2. **Add MongoDB** dans Railway
3. Ajoutez `DB_NAME=skimonitor` dans Variables
4. Copiez l'URL générée
5. **GitHub Secrets** → `REACT_APP_BACKEND_URL=...`
6. ✅ C'est déployé !

---

Besoin d'aide ? Dites-moi où vous en êtes et je vous guide étape par étape ! 🎿
