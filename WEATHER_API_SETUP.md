# Configuration de l'API Météo OpenWeatherMap

## État actuel
L'application affiche actuellement des données météo **simulées** pour les stations de ski. Pour obtenir des données météo réelles, vous devez ajouter une clé API OpenWeatherMap.

## Étapes pour configurer l'API météo

### 1. Obtenir une clé API gratuite

1. Visitez [OpenWeatherMap](https://openweathermap.org/api)
2. Créez un compte gratuit
3. Accédez à votre compte et générez une clé API
4. Le plan gratuit offre :
   - 1000 appels/jour
   - Données météo actuelles
   - Parfait pour les besoins de SkiMonitor

### 2. Ajouter la clé à l'application

Ouvrez le fichier `/app/backend/.env` et ajoutez la ligne suivante :

```env
OPENWEATHER_API_KEY=votre_cle_api_ici
```

### 3. Redémarrer le backend

Après avoir ajouté la clé, redémarrez le service backend :

```bash
sudo supervisorctl restart backend
```

### 4. Vérifier que ça fonctionne

L'application récupérera automatiquement les vraies données météo pour chaque station associée à un moniteur.

## Format des données météo

L'API retourne :
- `temperature` : Température en °C
- `feels_like` : Température ressentie
- `description` : Description du temps (ex: "Peu nuageux")
- `wind_speed` : Vitesse du vent en km/h
- `visibility` : Visibilité en km
- `humidity` : Humidité en %
- `snow` : Chutes de neige récentes (si disponible)
- `source` : "openweathermap" ou "simulated"

## Affichage dans l'interface

La carte météo s'affiche automatiquement sur le tableau de bord du moniteur avec :
- 🌡️ Température
- 💨 Vitesse du vent
- 👁️ Visibilité
- ❄️ Neige (si > 0)

## Notes importantes

- Sans clé API : données simulées aléatoires
- Avec clé API : données réelles mises à jour
- Le cache est géré automatiquement par l'API
- Les coordonnées GPS de chaque station sont déjà configurées dans le backend
