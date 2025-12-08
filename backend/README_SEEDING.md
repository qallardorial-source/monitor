# Script de Seeding des Moniteurs Fictifs

## 📋 Description

Ce script crée **10 moniteurs fictifs réalistes** avec leurs profils complets et quelques cours d'exemple. Les moniteurs sont automatiquement approuvés et visibles sur le site.

## 🎯 Ce qui est créé

### Moniteurs fictifs (10 profils)
- **Noms réalistes** : Pierre Dumont, Sophie Martin, Marc Bertrand, etc.
- **Emails de démo** : `prenom.nom@skimonitor-demo.fr`
- **Avatars génériques** : Illustrations via DiceBear API
- **Bios détaillées** : Expérience, spécialités, approche pédagogique
- **Variété de profils** :
  - Spécialités : Ski alpin, Snowboard, Freestyle, Hors-piste, Ski de fond
  - Niveaux : Du débutant à l'expert
  - Tarifs : De 50€ à 85€/heure
  - Stations : Courchevel, Val Thorens, Chamonix, Tignes, etc.

### Cours d'exemple (2-4 par moniteur)
- **Mix de cours privés et collectifs**
- **Dates futures** : Dans les 2 prochaines semaines
- **Horaires variés** : Entre 9h et 18h
- **Prix cohérents** : Basés sur le tarif horaire du moniteur

## 🚀 Comment l'utiliser

### Option 1 : Exécution simple
```bash
cd backend
python3 seed_instructors.py
```

Le script vous demandera confirmation avant de créer les données si des moniteurs approuvés existent déjà.

### Option 2 : Depuis votre environnement Python
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
pip install -r requirements.txt
python seed_instructors.py
```

## ⚙️ Pré-requis

1. **MongoDB doit être lancé** et accessible
2. **Fichier `.env`** doit contenir :
   ```env
   MONGO_URL=mongodb://localhost:27017/
   DB_NAME=skimonitor
   ```
3. **Dépendances Python** installées :
   ```bash
   pip install motor python-dotenv
   ```

## 📊 Résultat attendu

Après l'exécution, vous verrez :
```
✨ Seeding terminé avec succès !
   📊 10 utilisateurs créés
   🎿 10 moniteurs approuvés créés
   📅 30 cours d'exemple créés

💡 Les moniteurs sont maintenant visibles sur le site !
   Vous pouvez les voir sur : /instructors
   Et leurs cours sur : /lessons
```

## 🔍 Vérification

### Dans la base de données
```javascript
// MongoDB Shell
use skimonitor

// Compter les moniteurs
db.instructors.countDocuments({status: "approved"})

// Voir les moniteurs créés
db.instructors.find({status: "approved"}).pretty()

// Voir les cours créés
db.lessons.find().pretty()
```

### Sur le site
1. Accédez à **`/instructors`** → Vous devriez voir les 10 moniteurs
2. Accédez à **`/lessons`** → Vous devriez voir tous les cours
3. Cliquez sur un moniteur → Voir son profil et ses cours

## 🗑️ Nettoyage (si besoin)

Pour supprimer les données de test créées :

```javascript
// MongoDB Shell
use skimonitor

// Supprimer les utilisateurs de démo
db.users.deleteMany({email: /@skimonitor-demo\.fr$/})

// Supprimer les moniteurs associés
db.instructors.deleteMany({}) // ⚠️ Supprime TOUS les moniteurs

// Supprimer les cours
db.lessons.deleteMany({}) // ⚠️ Supprime TOUS les cours
```

## 🎨 Personnalisation

Vous pouvez modifier le script pour :

### Ajouter plus de moniteurs
Éditez la liste `FICTIONAL_INSTRUCTORS` dans `seed_instructors.py`

### Changer les avatars
Modifiez `AVATAR_URLS` ou utilisez vos propres URLs d'images

### Créer plus de cours
Ajustez `num_lessons = randint(2, 4)` à `randint(5, 10)` par exemple

### Modifier les templates de cours
Éditez `LESSON_TEMPLATES` pour ajouter de nouveaux types de cours

## ⚠️ Avertissements

1. **Données fictives** : Ces profils sont entièrement fictifs. Ne les présentez pas comme réels.
2. **Emails de démo** : Utilisent le domaine `@skimonitor-demo.fr` pour éviter toute confusion
3. **Sécurité** : Ne partagez jamais la base de données contenant ces données comme si c'étaient de vraies personnes
4. **RGPD** : Ces données fictives ne posent pas de problème RGPD, mais documentez-les comme "profils de démonstration"

## 🔄 Mise à jour

Pour rafraîchir les moniteurs de test :
1. Nettoyez la base (voir section Nettoyage)
2. Relancez le script

## 💡 Conseils

- **Pour une démo** : Gardez ces 10 profils, c'est suffisant
- **Pour le lancement** : Remplacez progressivement par de vrais moniteurs
- **Pour le développement** : Parfait pour tester toutes les fonctionnalités

## 📝 Note

Les avatars utilisent l'API DiceBear qui génère des illustrations SVG cohérentes et professionnelles. Vous pouvez les remplacer par :
- Des photos de stock libres de droits
- Des avatars génériques
- Des icônes personnalisées

---

**Créé pour SkiMonitor** - Option B : Données fictives réalistes 🎿
