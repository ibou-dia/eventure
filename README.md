# Eventure - Plateforme de Réservation d'Événements

Eventure est une application web complète de gestion et réservation d'événements développée avec Django et MongoDB. Cette plateforme permet aux utilisateurs de créer, découvrir et réserver des événements, avec un système de paiement intégré.

## Fonctionnalités principales

### Pour les visiteurs
- **Découverte d'événements** : Parcourir les événements disponibles avec filtres de recherche
- **Inscription et connexion** : Création de compte et authentification sécurisée
- **Consultation des détails** : Informations complètes sur chaque événement

### Pour les utilisateurs connectés
- **Réservation de billets** : Processus simple pour réserver des places
- **Paiement en ligne** : Intégration avec Wave et Orange Money
- **Billets électroniques** : Génération et envoi de billets par email
- **Gestion de profil** : Modification des informations personnelles
- **Historique des réservations** : Suivi des événements réservés

### Pour les organisateurs
- **Création d'événements** : Interface intuitive pour créer et publier des événements
- **Gestion des événements** : Modification, suppression et suivi des événements créés
- **Suivi des réservations** : Visualisation des participants à vos événements

## Architecture technique

### Frontend
- **Templates Django** : Interface utilisateur responsive et moderne
- **CSS personnalisé** : Styles adaptés à chaque type de page
- **JavaScript** : Interactions dynamiques et validations côté client

### Backend
- **Django** : Framework web Python pour le développement rapide
- **MongoDB** : Base de données NoSQL pour le stockage flexible des données
- **Authentification personnalisée** : Système basé sur MongoDB au lieu du système Django par défaut

### Structure de la base de données MongoDB

Le projet utilise deux collections principales :

1. **Collection User** :
   - Informations d'authentification (nom d'utilisateur, email, mot de passe hashé)
   - Données de profil (nom, prénom, etc.)
   - Statut du compte

2. **Collection Event** :
   - Informations sur l'événement (titre, description, date, lieu)
   - Capacité et disponibilité (nombre total de places, places restantes)
   - Tarification
   - Réservations imbriquées (approche document pour stocker les réservations)


## Installation et lancement

1. Assurez-vous d'avoir Python, Django et MongoDB installés
2. Clonez ce dépôt
3. Installez les dépendances :
   ```
   pip install -r requirements.txt
   ```
4. Configurez la connexion MongoDB dans `event_manager/db_connection.py`
5. Lancez le serveur de développement :
   ```
   python manage.py runserver
   ```
6. Accédez à l'application via `http://localhost:8000`

## Système de paiement

L'application intègre deux méthodes de paiement populaires en Afrique :

- **Wave** : Paiement mobile via le service Wave
- **Orange Money** : Paiement via le service Orange Money

Le processus de paiement est simulé dans l'environnement de développement, mais peut être connecté aux API réelles en production.

## Fonctionnalités à venir

- Système de notifications en temps réel
- Application mobile (iOS/Android)
- Intégration de méthodes de paiement internationales
- Système d'analyse pour les organisateurs d'événements
- Fonctionnalités sociales avancées (partage, invitations)
