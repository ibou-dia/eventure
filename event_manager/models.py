from django.db import models
from .db_connection import db
from django.contrib.auth.hashers import make_password, check_password
from bson.objectid import ObjectId
from datetime import datetime

# Collections MongoDB
event_collection = db['Event']
user_collection = db['User']
booking_collection = db['Booking']
invitations_collection = db['invitation']

# Classe utilitaire pour les utilisateurs MongoDB
class MongoUser:
    @staticmethod
    def create_user(username, email, password, **extra_fields):
        """Créer un nouvel utilisateur avec mot de passe hashé"""
        if user_collection.find_one({"username": username}):
            return None, "Ce nom d'utilisateur existe déjà"
        
        if user_collection.find_one({"email": email}):
            return None, "Cette adresse email est déjà utilisée"
        
        user_data = {
            "username": username,
            "email": email,
            "password": make_password(password),  # Hashage du mot de passe
            "date_joined": datetime.now(),       # Utiliser datetime.now() directement
            "is_active": True,
            **extra_fields
        }
        
        user_id = user_collection.insert_one(user_data).inserted_id
        return user_id, None
    
    @staticmethod
    def authenticate(username=None, email=None, password=None):
        """Authentifier un utilisateur avec son nom d'utilisateur/email et mot de passe"""
        if username:
            user = user_collection.find_one({"username": username})
        elif email:
            user = user_collection.find_one({"email": email})
        else:
            return None
        
        if user and check_password(password, user.get("password", "")):
            return user
        
        return None
    
    @staticmethod
    def get_user_by_id(user_id):
        """Récupérer un utilisateur par son ID"""
        if isinstance(user_id, str):
            try:
                user_id = ObjectId(user_id)
            except Exception:
                return None
        
        return user_collection.find_one({"_id": user_id})
    
    @staticmethod
    def update_user(user_id, **update_data):
        """Mettre à jour un utilisateur"""
        if "password" in update_data and update_data["password"]:
            update_data["password"] = make_password(update_data["password"])
        
        if isinstance(user_id, str):
            try:
                user_id = ObjectId(user_id)
            except Exception:
                return False
        
        result = user_collection.update_one(
            {"_id": user_id},
            {"$set": update_data}
        )
        
        return result.modified_count > 0
    