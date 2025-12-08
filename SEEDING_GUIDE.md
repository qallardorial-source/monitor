# 🚀 Guide : Lancer le Seeding depuis votre Navigateur

## ✨ Solution Simple - Endpoint Admin

Vous pouvez maintenant créer les 10 moniteurs fictifs **directement depuis votre navigateur** ou avec une simple requête HTTP !

## 📍 Comment faire ?

### Option 1 : Depuis le Dashboard Admin (Recommandé)

1. **Connectez-vous** à votre site en tant qu'admin
2. **Allez sur** `/admin` (le dashboard administrateur)
3. **Ouvrez la console** de votre navigateur (F12)
4. **Collez ce code** :

```javascript
fetch('/api/admin/seed-instructors', {
  method: 'POST',
  credentials: 'include'
})
  .then(res => res.json())
  .then(data => {
    console.log('✅ Seeding réussi !');
    console.log(`📊 ${data.created_users} utilisateurs créés`);
    console.log(`🎿 ${data.created_instructors} moniteurs créés`);
    console.log(`📅 ${data.created_lessons} cours créés`);
    alert('Seeding terminé ! ' + data.message);
    // Recharger la page pour voir les nouveaux moniteurs
    window.location.reload();
  })
  .catch(err => {
    console.error('❌ Erreur:', err);
    alert('Erreur lors du seeding');
  });
```

5. **Appuyez sur Entrée**
6. **Attendez** le message de confirmation
7. **Actualisez** la page `/instructors` pour voir vos nouveaux moniteurs !

### Option 2 : Avec cURL (en ligne de commande)

Si vous avez accès à un terminal :

```bash
# Remplacez YOUR_ADMIN_SESSION_COOKIE par votre cookie de session admin
curl -X POST https://votre-site.com/api/admin/seed-instructors \
  -H "Cookie: session=YOUR_ADMIN_SESSION_COOKIE" \
  -H "Content-Type: application/json"
```

### Option 3 : Avec Postman/Insomnia

1. **Créez** une nouvelle requête POST
2. **URL** : `https://votre-site.com/api/admin/seed-instructors`
3. **Méthode** : POST
4. **Headers** : Ajoutez votre cookie de session admin
5. **Envoyez** la requête

### Option 4 : Bouton dans le Dashboard (À ajouter)

Ajoutez ce bouton dans votre dashboard admin React :

```jsx
// Dans AdminDashboard component
const handleSeedData = async () => {
  if (!window.confirm('Créer 10 moniteurs fictifs avec ~30 cours d\'exemple ?')) {
    return;
  }

  try {
    const response = await axios.post(`${API}/admin/seed-instructors`, {}, {
      withCredentials: true
    });

    toast.success(`${response.data.message}\n` +
      `📊 ${response.data.created_users} utilisateurs\n` +
      `🎿 ${response.data.created_instructors} moniteurs\n` +
      `📅 ${response.data.created_lessons} cours`
    );

    // Recharger les stats
    window.location.reload();
  } catch (e) {
    toast.error('Erreur lors du seeding');
  }
};

// Dans le JSX, ajoutez ce bouton
<Button onClick={handleSeedData} variant="outline">
  🌱 Peupler la base de données
</Button>
```

## 🔐 Sécurité

⚠️ **Important** : Cet endpoint est **protégé** et nécessite :
- ✅ Être connecté
- ✅ Avoir le rôle **"admin"**

Si vous n'êtes pas admin, vous recevrez une erreur `403 Forbidden`.

## 📊 Ce qui sera créé

Quand vous appelez cet endpoint, il crée automatiquement :

### 10 Moniteurs Fictifs
- Pierre Dumont (Courchevel, Ski alpin, 65€/h)
- Sophie Martin (Val Thorens, Snowboard/Freestyle, 75€/h)
- Marc Bertrand (Méribel, Ski alpin/fond, 55€/h)
- Julie Rousseau (Chamonix, Hors-piste, 85€/h)
- Thomas Leroy (Tignes, Ski/Snowboard, 70€/h)
- Emma Dubois (Les Saisies, Ski de fond, 50€/h)
- Lucas Moreau (Avoriaz, Snowboard/Freestyle, 72€/h)
- Chloé Bernard (Megève, Ski alpin, 58€/h)
- Antoine Petit (Val d'Isère, Hors-piste, 80€/h)
- Léa Fontaine (Les Arcs, Ski/Snowboard, 62€/h)

### ~30 Cours d'Exemple
- 2 à 4 cours par moniteur
- Mix de cours privés et collectifs
- Dates dans les 2 prochaines semaines
- Horaires variés (9h-18h)

## 🎯 Résultat Attendu

Réponse JSON :
```json
{
  "success": true,
  "message": "Seeding terminé avec succès !",
  "created_users": 10,
  "created_instructors": 10,
  "created_lessons": 30,
  "skipped": 0
}
```

## 🔄 Relancer le Seeding

Si vous relancez l'endpoint :
- Les moniteurs **déjà existants** (même email) seront **ignorés**
- Seuls les **nouveaux** seront créés
- Le champ `"skipped"` indiquera combien ont été ignorés

## 🗑️ Nettoyage (Si Besoin)

Pour supprimer les données de test, connectez-vous à MongoDB :

```javascript
// Supprimer les utilisateurs de démo
db.users.deleteMany({email: /@skimonitor-demo\.fr$/})

// Supprimer les cours orphelins
db.lessons.deleteMany({instructor_id: {$in: [/* IDs des instructeurs supprimés */]}})
```

Ou créez un endpoint `/api/admin/clear-demo-data` similaire.

## ✅ Vérification

Après le seeding :

1. **Allez sur `/instructors`** → Vous devriez voir 10 moniteurs
2. **Allez sur `/lessons`** → Vous devriez voir ~30 cours
3. **Cliquez sur un moniteur** → Voir son profil complet et ses cours

## 🎨 Personnalisation

Pour modifier les moniteurs, éditez directement le fichier :
- **`backend/server.py`** ligne 1364-1455
- Modifiez la liste `FICTIONAL_INSTRUCTORS`

## 💡 Conseil

**Lancez le seeding dès maintenant** pour avoir du contenu sur votre plateforme !

Cela vous permettra de :
- ✅ Tester toutes les fonctionnalités
- ✅ Faire des démos professionnelles
- ✅ Avoir un site vivant dès le départ
- ✅ Attirer de vrais utilisateurs avec du contenu existant

---

**Créé pour SkiMonitor** - Seeding simplifié via API 🎿
