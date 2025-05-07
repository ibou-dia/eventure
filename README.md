# Site de Réservation d'Événements

Ce projet est une implémentation frontend d'un site de réservation d'événements utilisant Django, en préparation à une intégration backend avec Django et MongoDB.

## Structure du projet

```
event_booking/         # Projet Django principal
├── event_manager/     # Application Django pour la gestion des événements
│   ├── models.py      # Modèles de données (Event, Comment, EventRegistration)
│   ├── views.py       # Vues pour gérer les requêtes HTTP
│   └── urls.py        # Configuration des URLs de l'application
├── templates/         # Templates HTML
│   ├── base.html      # Template de base avec navigation et footer
│   └── event_manager/ # Templates spécifiques à l'application
│       ├── home.html           # Page d'accueil avec liste des événements
│       ├── event_detail.html   # Page de détail d'un événement
│       ├── create_event.html   # Formulaire de création d'événement
│       ├── login.html          # Page de connexion
│       └── register.html       # Page d'inscription
├── static/           # Fichiers statiques
│   ├── css/          # Feuilles de style CSS
│   ├── js/           # Scripts JavaScript
│   └── images/       # Images
└── media/           # Fichiers uploadés par les utilisateurs (photos d'événements, etc.)
```

## Fonctionnalités

- **Page d'accueil** : Liste des événements avec filtres
- **Détail d'événement** : Informations complètes, commentaires, système de réservation
- **Création d'événement** : Formulaire pour ajouter un nouvel événement
- **Authentification** : Pages de connexion et d'inscription (placeholder)
- **Système de likes** : Possibilité d'aimer un événement
- **Système de commentaires** : Ajout et affichage des commentaires

## Installation et lancement

1. Assurez-vous d'avoir Python et Django installés
2. Clonez ce dépôt
3. Exécutez les migrations pour initialiser la base de données:
   ```
   python manage.py makemigrations
   python manage.py migrate
   ```
4. Lancez le serveur de développement:
   ```
   python manage.py runserver
   ```
5. Accédez à l'application via `http://localhost:8000`

## Notes de développement

- Le frontend est prêt à être intégré avec un backend Django et MongoDB
- Les formulaires sont configurés pour communiquer avec le backend via des requêtes POST
- Des données statiques sont simulées en attendant l'intégration backend complète
- Les hooks et appels API sont préparés dans les fichiers JavaScript

## Prochaines étapes

- Implémentation complète du backend Django
- Intégration avec MongoDB pour la persistance des données
- Système d'authentification complet
- Intégration d'un système de paiement
- Optimisation pour le déploiement en production
