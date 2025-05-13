from django.apps import AppConfig
from pymongo import ASCENDING
import pymongo.errors



class EventManagerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'event_manager'

    def ready(self):
        # Importer ici ta connexion et ta collection
        # Adapte le chemin si ton fichier s'appelle différemment
        from .models import event_collection

        try:
            # Crée un index TTL sur le champ "date" pour supprimer
            # le document dès que date < now
            event_collection.create_index(
                [("date", ASCENDING)],
                expireAfterSeconds=0,
                name="event_date_ttl"
            )
            # Tu peux logguer ou print pour vérifier en dev
            print("✅ Index TTL 'event_date_ttl' OK")
        except pymongo.errors.OperationFailure as e:
            # Si l’index existe déjà ou autre erreur
            print(f"⚠️ Échec création index TTL : {e}")








