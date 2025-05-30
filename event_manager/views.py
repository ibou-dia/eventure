from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect, Http404
from django.urls import reverse
from django.contrib import messages
from .models import event_collection, user_collection, MongoUser
from datetime import datetime
from django.db.models import Count
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.template.loader import render_to_string
from bson.objectid import ObjectId
from django.contrib.auth.hashers import check_password, make_password
from .middleware import login_required  # Utiliser notre propre décorateur login_required
from bson.binary import Binary
from datetime import datetime
import base64
from django.views.decorators.csrf import csrf_exempt
import json
from django.core.mail import send_mail
import qrcode
import io
import uuid
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator


# Fonction utilitaire pour convertir un ID en ObjectId si possible
def try_convert_to_objectid(id_string):
    try:
        if id_string and isinstance(id_string, str) and len(id_string) == 24 and all(c in '0123456789abcdefABCDEF' for c in id_string):
            return ObjectId(id_string)
        return id_string
    except Exception:
        return id_string


# Pour simuler des données en attendant une intégration complète
def get_sample_events():
    # Vérifier si la collection d'événements est vide
    try:
        if event_collection.count_documents({}) == 0:
            sample_events = [
                {
                    'title': 'Concert de Jazz',
                    'description': 'Une soirée exceptionnelle avec les meilleurs artistes de jazz.',
                    'date': timezone.now() + timezone.timedelta(days=10),
                    'location': 'Salle Pleyel, Paris',
                    'total_seats': 200,
                    'remaining_seats': 150,
                    'price': 25.00,
                },
                {
                    'title': 'Festival de Cinéma',
                    'description': 'Projection de films indépendants et rencontre avec des réalisateurs.',
                    'date': timezone.now() + timezone.timedelta(days=20),
                    'location': 'Cinémathèque, Lyon',
                    'total_seats': 300,
                    'remaining_seats': 300,
                    'price': 15.00,
                },
                {
                    'title': 'Conférence Tech',
                    'description': 'Découvrez les dernières innovations technologiques.',
                    'date': timezone.now() + timezone.timedelta(days=5),
                    'location': 'Centre des Congrès, Lille',
                    'total_seats': 500,
                    'remaining_seats': 350,
                    'price': 0.00,
                },
            ]
            # Trier les événements exemples par date
            sample_events.sort(key=lambda x: x.get('date', datetime.max))
            return sample_events
        # Si des événements existent déjà, les retourner et les trier
        events = list(event_collection.find())
        # Les événements réels seront triés dans la fonction home
        return events
    except Exception as e:
        # En cas d'erreur, retourner une liste vide
        print(f"Erreur lors de la récupération des événements: {e}")
        return []

# Vues principales
def home(request):
    # Récupérer les paramètres de recherche et de filtre
    search_query = request.GET.get('search', '')
    type_filter = request.GET.get('type', '')
    date_filter = request.GET.get('date', '')
    city_filter = request.GET.get('city', '')
    
    # Récupérer les événements (mode statique ou base de données)
    try:
        # Construction du filtre MongoDB
        filter_query = {}
        
        # Appliquer le filtre de recherche (sur le titre ou la description)
        if search_query:
            filter_query['$or'] = [
                {'title': {'$regex': search_query, '$options': 'i'}},
                {'description': {'$regex': search_query, '$options': 'i'}}
            ]
        
        # Appliquer le filtre de type
        if type_filter:
            filter_query['type'] = {'$regex': type_filter, '$options': 'i'}
        
        # Appliquer le filtre de ville
        if city_filter:
            filter_query['location'] = {'$regex': city_filter, '$options': 'i'}
        
        # Appliquer le filtre de date
        now = datetime.now()
        if date_filter == 'today':
            today_start = datetime(now.year, now.month, now.day)
            today_end = datetime(now.year, now.month, now.day, 23, 59, 59)
            filter_query['date'] = {'$gte': today_start, '$lte': today_end}
        elif date_filter == 'tomorrow':
            tomorrow = now + timezone.timedelta(days=1)
            tomorrow_start = datetime(tomorrow.year, tomorrow.month, tomorrow.day)
            tomorrow_end = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 23, 59, 59)
            filter_query['date'] = {'$gte': tomorrow_start, '$lte': tomorrow_end}
        elif date_filter == 'week':
            week_start = now
            week_end = now + timezone.timedelta(days=7)
            filter_query['date'] = {'$gte': week_start, '$lte': week_end}
        elif date_filter == 'weekend':
            # Trouver le prochain weekend
            days_until_saturday = (5 - now.weekday()) % 7
            next_saturday = now + timezone.timedelta(days=days_until_saturday)
            next_sunday = next_saturday + timezone.timedelta(days=1)
            weekend_start = datetime(next_saturday.year, next_saturday.month, next_saturday.day)
            weekend_end = datetime(next_sunday.year, next_sunday.month, next_sunday.day, 23, 59, 59)
            filter_query['date'] = {'$gte': weekend_start, '$lte': weekend_end}
        elif date_filter == 'month':
            month_start = datetime(now.year, now.month, 1)
            if now.month == 12:
                next_month = datetime(now.year + 1, 1, 1)
            else:
                next_month = datetime(now.year, now.month + 1, 1)
            filter_query['date'] = {'$gte': month_start, '$lt': next_month}
        
        # Récupérer les événements filtrés
        events = list(event_collection.find(filter_query))
        parsed_events = []
        
        for event in events:
            parsed_event = event.copy()
            if isinstance(event.get("date"), str):
                try:
                    parsed_event["date"] = datetime.fromisoformat(event["date"].replace("Z", "+00:00"))
                except Exception as e:
                    parsed_event["date"] = None
            
            # Assurer que chaque événement a une propriété 'id' pour les templates
            if '_id' in parsed_event and 'id' not in parsed_event:
                parsed_event['id'] = str(parsed_event['_id'])
            elif 'id' not in parsed_event:
                # Si ni _id ni id n'existe, utiliser l'index comme fallback
                parsed_event['id'] = events.index(event) + 1
                
            parsed_events.append(parsed_event)
        
        # Trier les événements par date (du plus proche au plus éloigné)
        parsed_events.sort(key=lambda x: x.get('date', datetime.max))
    except Exception as e:
        # Fallback sur les événements statiques en cas d'erreur
        print(f"Erreur lors de la recherche d'événements: {e}")
        parsed_events = get_sample_events()
    
    # Pagination : 10 événements par page
    paginator = Paginator(parsed_events, 10)
    page = request.GET.get('page', 1)
    
    try:
        events_page = paginator.page(page)
    except PageNotAnInteger:
        events_page = paginator.page(1)
    except EmptyPage:
        events_page = paginator.page(paginator.num_pages)
    
    return render(request, 'event_manager/home.html', {
        'events': events_page,
        'page_obj': events_page,  # Pour la compatibilité avec les tags de pagination
    })


def event_detail(request, event_id):
    # Convertir l'event_id en ObjectId si ce n'est pas déjà fait
    if not isinstance(event_id, ObjectId):
        try:
            event_id_obj = ObjectId(event_id)
        except:
            # Gérer le cas où l'ID n'est pas un ObjectId valide
            messages.error(request, "ID d'événement invalide.")
            return redirect('events_list')  # Rediriger vers une page appropriée
    else:
        event_id_obj = event_id
    
    # Récupérer l'événement
    event = event_collection.find_one({"_id": event_id_obj})
    if not event:
        messages.error(request, "Cet événement n'existe pas.")
        return redirect('events_list')  # Rediriger vers une page appropriée
    
    # Convertir l'ObjectId en chaîne pour les URLs
    event['id'] = str(event['_id'])
    
    # Récupérer les commentaires associés à cet événement, triés par date décroissante
    comments = sorted(event.get("comments", []), key=lambda x: x["created_at"], reverse=True)

    # Pour chaque commentaire, convertir l'ObjectId en chaîne et enrichir avec les infos utilisateur
    for comment in comments:
        comment['id'] = str(comment.get('_id'))
        
        # Récupérer les informations complètes de l'utilisateur
        username = comment.get('user')
        user_info = user_collection.find_one({"username": username})
        
        if user_info:
            comment['user_info'] = {
                'username': user_info.get('username'),
                'first_name': user_info.get('first_name', ''),
                'last_name': user_info.get('last_name', ''),
                'profile_image': user_info.get('profile_image'),
                'id': str(user_info['_id'])
            }
        else:
            comment['user_info'] = {
                'username': username,
                'first_name': '',
                'last_name': '',
                'profile_image': None,
                'id': 'unknown'
            }
    
    # Récupérer les informations du créateur de l'événement
    creator_info = None
    if 'creator_id' in event:
        try:
            creator_id = event['creator_id']
            if isinstance(creator_id, str):
                creator_id = ObjectId(creator_id)
            creator = user_collection.find_one({"_id": creator_id})
            if creator:
                creator_info = {
                    'username': creator.get('username', 'Utilisateur inconnu'),
                    'first_name': creator.get('first_name', ''),
                    'last_name': creator.get('last_name', ''),
                    'profile_image': creator.get('profile_image', None),
                    'id': str(creator['_id'])
                }
        except Exception as e:
            print(f"Erreur lors de la récupération du créateur: {e}")
    
    # Si aucun créateur n'a été trouvé, fournir un créateur par défaut
    if not creator_info:
        creator_info = {
            'username': 'organisateur',
            'first_name': 'Équipe',
            'last_name': 'Eventure',
            'profile_image': None,
            'id': 'default'
        }
    
    user_has_liked = False
    if request.is_authenticated:
        user_id = str(request.user.get('_id'))
        likes = event.get('likes', [])
        user_has_liked = any(like.get('user').get('user_id') == user_id for like in likes)
        
    context = {
        'event': event,
        'comments': comments,
        'user_has_liked': user_has_liked,
        'creator': creator_info
    }
    
    return render(request, 'event_manager/event_detail.html', context)

@login_required
def delete_event(request, event_id):
    """Vue pour supprimer un événement existant"""
    # Convertir l'ID en ObjectId si possible
    mongo_id = try_convert_to_objectid(event_id)
    
    # Récupérer l'événement depuis la base de données
    event = event_collection.find_one({"_id": mongo_id})
    
    # Vérifier si l'événement existe
    if not event:
        messages.error(request, "L'événement demandé n'existe pas.")
        return redirect('profile')
    
    # Vérifier si l'utilisateur actuel est bien le créateur de l'événement
    if 'creator_id' in event and str(event['creator_id']) != str(request.user['_id']):
        messages.error(request, "Vous n'êtes pas autorisé à supprimer cet événement.")
        return redirect('profile')
    
    if request.method == 'POST':
        try:
            # Supprimer l'événement de la base de données
            event_collection.delete_one({"_id": mongo_id})
            
            messages.success(request, 'Événement supprimé avec succès!')
        except Exception as e:
            messages.error(request, f'Erreur lors de la suppression de l\'événement: {str(e)}')
    
    return redirect('profile')

@login_required
def edit_event(request, event_id):
    """Vue pour modifier un événement existant"""
    # Convertir l'ID en ObjectId si possible
    mongo_id = try_convert_to_objectid(event_id)
    
    # Récupérer l'événement depuis la base de données
    event = event_collection.find_one({"_id": mongo_id})
    
    # Vérifier si l'événement existe
    if not event:
        messages.error(request, "L'événement demandé n'existe pas.")
        return redirect('profile')
    
    # Vérifier si l'utilisateur actuel est bien le créateur de l'événement
    if 'creator_id' in event and str(event['creator_id']) != str(request.session.get('user_id')):
        messages.error(request, "Vous n'êtes pas autorisé à modifier cet événement.")
        return redirect('profile')
    
    if request.method == 'POST':
        # Récupérer les données du formulaire
        title = request.POST.get('title')
        description = request.POST.get('description')
        date_str = request.POST.get('date')
        location = request.POST.get('location')
        type_event = request.POST.get('type')
        total_seats = int(request.POST.get('total_seats', 0))
        price = float(request.POST.get('price', 0))
        
        # Vérifier si une nouvelle image a été fournie
        image_file = request.FILES.get('image')
        image_base64 = None
        
        # Validation simplifiée
        if not all([title, description, date_str, location, total_seats >= 0]):
            messages.error(request, 'Veuillez remplir tous les champs correctement.')
            return render(request, 'event_manager/edit_event.html', {'event': event})
        
        try:
            # Conversion de la date au bon format
            event_date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M")
            
            # Préparation du document à mettre à jour
            update_data = {
                "title": title,
                "type": type_event,
                "description": description,
                "date": event_date,
                "location": location,
                "total_seats": total_seats,
                "price": price,
            }
            
            # Si une nouvelle image a été fournie, la traiter
            if image_file:
                image_bytes = image_file.read()
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                update_data['image'] = image_base64
            
            # Mettre à jour l'événement dans la base de données
            event_collection.update_one({"_id": mongo_id}, {"$set": update_data})
            
            messages.success(request, 'Événement mis à jour avec succès!')
            return redirect('profile')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la mise à jour de l\'événement: {str(e)}')
            return render(request, 'event_manager/edit_event.html', {'event': event})
    
    # Pour les requêtes GET, préparer l'événement pour l'affichage
    # S'assurer que l'ID est disponible dans un format utilisable par les templates
    if '_id' in event:
        event['id'] = str(event['_id'])
    
    return render(request, 'event_manager/edit_event.html', {'event': event})

@login_required
def create_event(request):
    if request.method == 'POST':
        # Dans un contexte réel, on utiliserait un formulaire Django
        title = request.POST.get('title')
        description = request.POST.get('description')
        date_str = request.POST.get('date')
        location = request.POST.get('location')
        type=request.POST.get('type')
        total_seats = int(request.POST.get('total_seats', 0))
        price = float(request.POST.get('price', 0))
        image_file = request.FILES.get('image')
        
        # Validation simplifiée
        if not all([title, description, date_str, location,image_file, total_seats >= 0]):
            messages.error(request, 'Veuillez remplir tous les champs correctement.')
            return render(request, 'event_manager/create_event.html')
        try:
            # Conversion de la date au bon format
            event_date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M")
            image_bytes = image_file.read()
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')

            # Préparation du document à insérer
            event_data = {
                "title": title,
                "etat":"Nouveau",
                "type": type,
                "description": description,
                "date": event_date,
                "location": location,
                "total_seats": total_seats,
                "remaining_seat": total_seats,
                "price": price,
                'image': image_base64,
                'created_at': datetime.utcnow(),
                "creator_id": request.user['_id']
            }

            # Insérer dans la collection MongoDB
            event_collection.insert_one(event_data)

            # En mode statique, rediriger simplement vers la page d'accueil
            # Simuler la création réussie
            messages.success(request, 'Événement créé avec succès!')
            return redirect('home')
        except Exception as e:
            messages.error(request, f"Erreur lors de la création de l'événement : {e}")
            return render(request, 'event_manager/create_event.html')
        
    return render(request, 'event_manager/create_event.html')

@login_required
def add_comment(request, event_id):
    # Convertir l'event_id en ObjectId si ce n'est pas déjà fait
    if not isinstance(event_id, ObjectId):
        try:
            event_id_obj = ObjectId(event_id)
        except:
            # Gérer le cas où l'ID n'est pas un ObjectId valide
            messages.error(request, "ID d'événement invalide.")
            return redirect('events_list')  # Rediriger vers une page appropriée
    else:
        event_id_obj = event_id
    
    # Vérifier que l'événement existe
    event = event_collection.find_one({"_id": event_id_obj})
    if not event:
        messages.error(request, "Cet événement n'existe pas.")
        return redirect('events_list')  # Rediriger vers une page appropriée
    
    if request.method == 'POST':
        content = request.POST.get('content')
        
        if not content:
            messages.error(request, 'Le commentaire ne peut pas être vide.')
            return redirect('event_detail', event_id=event_id)
        
        # Créer un nouveau document de commentaire
        comment = {
            "user": request.user.get('username'),  # ou request.user.id selon votre système d'authentification
            "content": content,
            "created_at": datetime.now()
        }
        
        # Insérer le commentaire dans la collection
        # Ajouter le commentaire à la liste des commentaires dans l'événement
        result = event_collection.update_one(
            {"_id": event_id_obj},
            {"$push": {"comments": comment}}  # Crée le champ 'comments' s’il n'existe pas
        )

        if result.modified_count > 0:
            messages.success(request, 'Commentaire ajouté avec succès!')
        else:
            messages.error(request, "Erreur lors de l'ajout du commentaire.")
        
        return redirect('event_detail', event_id=event_id)
    
    return redirect('event_detail', event_id=event_id)

# Pages d'authentification
def login_view(request):
    # Si l'utilisateur est déjà connecté, rediriger vers la page d'accueil
    if request.is_authenticated:
        return redirect('home')
    
    error = None
    next_url = request.GET.get('next', 'home')
    
    if request.method == 'POST':
        username_or_email = request.POST.get('username_or_email')
        password = request.POST.get('password')
        
        # Essayer de se connecter avec le nom d'utilisateur d'abord
        user = MongoUser.authenticate(username=username_or_email, password=password)
        
        # Si ça ne fonctionne pas, essayer avec l'email
        if not user:
            user = MongoUser.authenticate(email=username_or_email, password=password)
        
        if user:
            # Enregistrer l'ID utilisateur dans la session
            request.session['user_id'] = str(user['_id'])
            messages.success(request, f"Bienvenue, {user['username']}!")
            
            # Rediriger vers l'URL next si présente
            return redirect(next_url)
        else:
            error = "Nom d'utilisateur ou mot de passe incorrect"
    
    return render(request, 'event_manager/login.html', {
        'error': error,
        'next': next_url
    })

def register_view(request):
    # Si l'utilisateur est déjà connecté, rediriger vers la page d'accueil
    if request.is_authenticated:
        return redirect('home')
    
    error = None
    form_data = {}
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        
        form_data = {
            'username': username,
            'email': email,
            'first_name': first_name,
            'last_name': last_name
        }
        
        # Validation basique
        if not all([username, email, password]):
            error = "Tous les champs obligatoires doivent être remplis"
        elif password != password2:
            error = "Les mots de passe ne correspondent pas"
        else:
            # Créer l'utilisateur
            user_id, error = MongoUser.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            if user_id:
                # Connecter l'utilisateur automatiquement
                request.session['user_id'] = str(user_id)
                messages.success(request, f"Bienvenue, {username}! Votre compte a été créé avec succès.")
                return redirect('home')
    
    return render(request, 'event_manager/register.html', {
        'error': error,
        'form_data': form_data
    })

def logout_view(request):
    # Supprimer l'ID utilisateur de la session
    if 'user_id' in request.session:
        del request.session['user_id']
    
    messages.success(request, "Vous avez été déconnecté avec succès.")
    return redirect('home')

@login_required
def profile_view(request):
    user = request.user
    error = None
    success = None
    
    # Récupérer le message de succès stocké dans la session, s'il existe
    if 'profile_success' in request.session:
        success = request.session.pop('profile_success')  # Récupérer et supprimer le message
    
    # Récupérer les événements créés par l'utilisateur
    filtered_events = list(event_collection.find({'creator_id': request.user['_id']}))
    
    # Traitement spécial pour les ObjectIds de MongoDB
    processed_events = []
    for event in filtered_events:
        # Copier l'événement pour éviter de modifier l'original
        processed_event = event.copy()
        
        # Convertir l'ObjectId en chaîne pour l'utiliser dans les templates
        if '_id' in processed_event:
            # Assurer que l'ID est une chaîne utilisable dans les URLs
            processed_event['id'] = str(processed_event['_id'])
        
        # Si creator_id est un ObjectId, le convertir aussi
        if 'creator_id' in processed_event and isinstance(processed_event['creator_id'], ObjectId):
            processed_event['creator_id'] = str(processed_event['creator_id'])
            
        processed_events.append(processed_event)
    
    # Remplacer la liste originale par la liste traitée
    filtered_events = processed_events
    
    if request.method == 'POST':
        # Déterminer quelle section du profil est mise à jour
        action = request.POST.get('action')
        
        if action == 'info':
            # Mise à jour des informations personnelles
            username = request.POST.get('username')
            email = request.POST.get('email')
            first_name = request.POST.get('first_name', '')
            last_name = request.POST.get('last_name', '')
            
            # Vérifier si le nom d'utilisateur ou l'email est déjà utilisé par un autre utilisateur
            if username != user.get('username') and user_collection.find_one({"username": username}):
                error = "Ce nom d'utilisateur est déjà utilisé par un autre utilisateur"
            elif email != user.get('email') and user_collection.find_one({"email": email}):
                error = "Cette adresse email est déjà utilisée par un autre utilisateur"
            else:
                # Mettre à jour les informations
                update_data = {
                    "username": username,
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name
                }
                
                if MongoUser.update_user(user['_id'], **update_data):
                    success = "Vos informations ont été mises à jour avec succès"
                else:
                    error = "Une erreur est survenue lors de la mise à jour de vos informations"
                
        elif action == 'password':
            # Mise à jour du mot de passe
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            # Vérifier le mot de passe actuel
            if not check_password(current_password, user.get("password", "")):
                error = "Mot de passe actuel incorrect"
            elif new_password != confirm_password:
                error = "Les nouveaux mots de passe ne correspondent pas"
            elif not new_password:
                error = "Le nouveau mot de passe ne peut pas être vide"
            else:
                # Mettre à jour le mot de passe
                if MongoUser.update_user(user['_id'], password=new_password):
                    success = "Votre mot de passe a été mis à jour avec succès"
                else:
                    error = "Une erreur est survenue lors de la mise à jour de votre mot de passe"
                    
        elif action == 'delete_photo':
            # Suppression de la photo de profil
            try:
                # Mettre à jour l'utilisateur dans MongoDB en retirant la photo de profil
                if MongoUser.update_user(user['_id'], profile_image=None):
                    # Mettre à jour la session utilisateur
                    updated_user = user_collection.find_one({"_id": ObjectId(user['_id'])})
                    
                    # Convertir les ObjectId et datetime pour la sérialisation JSON
                    def convert_for_json(obj):
                        if isinstance(obj, dict):
                            for key, value in list(obj.items()):
                                if isinstance(value, ObjectId):
                                    obj[key] = str(value)
                                elif isinstance(value, datetime):
                                    obj[key] = value.isoformat()
                                elif isinstance(value, (dict, list)):
                                    convert_for_json(value)
                        elif isinstance(obj, list):
                            for i, item in enumerate(obj):
                                if isinstance(item, ObjectId):
                                    obj[i] = str(item)
                                elif isinstance(item, datetime):
                                    obj[i] = item.isoformat()
                                elif isinstance(item, (dict, list)):
                                    convert_for_json(item)
                    
                    # Appliquer la conversion à tout l'objet utilisateur
                    convert_for_json(updated_user)
                    
                    # Mettre à jour la session
                    request.session['user'] = updated_user
                    request.session.modified = True
                    
                    # Sauvegarder le message de succès dans la session
                    request.session['profile_success'] = "Votre photo de profil a été supprimée"
                    
                    # Rediriger vers la page de profil pour rafraîchir
                    return redirect('profile')
                else:
                    error = "Une erreur est survenue lors de la suppression de votre photo de profil"
            except Exception as e:
                error = f"Une erreur est survenue lors de la suppression de votre photo de profil : {str(e)}"
                    
        elif action == 'profile_photo':
            print("\n\n==== Début du traitement de la photo de profil ====")
            print(f"Action détectée: {action}")
            print(f"FILES: {request.FILES}")
            print(f"POST: {request.POST}")
            
            # Mise à jour de la photo de profil
            if 'profile_photo' in request.FILES:
                print("Fichier photo trouvé dans request.FILES")
                uploaded_file = request.FILES['profile_photo']
                print(f"Type de fichier: {uploaded_file.content_type}, Taille: {uploaded_file.size} bytes")
                
                # Vérifier que c'est bien une image
                if not uploaded_file.content_type.startswith('image'):
                    error = "Le fichier doit être une image"
                else:
                    try:
                        # Lire le contenu de l'image
                        image_data = uploaded_file.read()
                        
                        # Convertir l'image en base64 pour le stockage dans MongoDB
                        import base64
                        encoded_image = base64.b64encode(image_data).decode('utf-8')
                        
                        # Construire l'URL data pour l'affichage direct
                        image_data_url = f"data:{uploaded_file.content_type};base64,{encoded_image}"
                        
                        # Mettre à jour l'utilisateur dans MongoDB
                        if MongoUser.update_user(user['_id'], profile_image=image_data_url):
                            # Mettre à jour la session utilisateur
                            updated_user = user_collection.find_one({"_id": ObjectId(user['_id'])})
                            
                            # Convertir l'ObjectId en string pour éviter les problèmes de sérialisation JSON
                            if updated_user and '_id' in updated_user:
                                updated_user['_id'] = str(updated_user['_id'])
                            
                            # Vérifier tous les champs pour les ObjectId et datetime et les convertir en formats sérialisables
                            def convert_for_json(obj):
                                if isinstance(obj, dict):
                                    for key, value in list(obj.items()):
                                        if isinstance(value, ObjectId):
                                            obj[key] = str(value)
                                        elif isinstance(value, datetime):
                                            obj[key] = value.isoformat()
                                        elif isinstance(value, (dict, list)):
                                            convert_for_json(value)
                                elif isinstance(obj, list):
                                    for i, item in enumerate(obj):
                                        if isinstance(item, ObjectId):
                                            obj[i] = str(item)
                                        elif isinstance(item, datetime):
                                            obj[i] = item.isoformat()
                                        elif isinstance(item, (dict, list)):
                                            convert_for_json(item)
                            
                            # Appliquer la conversion à tout l'objet utilisateur
                            convert_for_json(updated_user)
                            
                            # Mettre à jour la session
                            request.session['user'] = updated_user
                            request.session.modified = True
                            
                            # Sauvegarder le message de succès dans la session
                            request.session['profile_success'] = "Votre photo de profil a été mise à jour avec succès"
                            
                            # Rediriger vers la page de profil pour rafraîchir
                            return redirect('profile')
                        else:
                            error = "Une erreur est survenue lors de la mise à jour de votre photo de profil"
                    except Exception as e:
                        error = f"Une erreur est survenue : {str(e)}"
            else:
                error = "Aucune photo n'a été sélectionnée"
    
    # Récupérer les réservations de l'utilisateur depuis MongoDB
    user_bookings = list(event_collection.find({"bookings.user_id": request.user['_id']}))
    participations_count = len(user_bookings)


    # Pour chaque réservation, récupérer les informations de l'événement
    bookings = []
    for booking in user_bookings:
        event_id = booking.get('_id')
        if event_id:
            try:
                event_obj_id = ObjectId(event_id) if isinstance(event_id, str) else event_id
                event = event_collection.find_one({"_id": event_obj_id})
                if event:
                    # Ajouter l'ID pour les templates
                    if '_id' in event:
                        event['id'] = str(event['_id'])
                    
                    # Calculer le prix total en multipliant le prix unitaire par le nombre de places
                    num_seats = booking.get('num_seats', 1)
                    unit_price = event.get('price', 0)
                    total_price = unit_price * int(num_seats)
                    
                    bookings.append({
                        'id': str(booking.get('_id')),
                        'event': event,
                        'num_seats': num_seats,
                        'total_price': total_price,
                        'status': booking.get('status', 'confirmed')
                    })
            except Exception as e:
                print(f"Erreur lors de la récupération de l'événement: {e}")
    
    # Calculer les statistiques réelles
    events_created_count = event_collection.count_documents({"creator_id": request.user['_id']})
    
    # Récupérer les likes de l'utilisateur
    user_likes = list(event_collection.find({"likes.user.user_id": str(request.user['_id'])}))
    likes_count = len(user_likes)
    
    liked_events = []
    for like in user_likes:
        event_id = like.get('_id')
        if event_id:
            try:
                event_obj_id = ObjectId(event_id) if isinstance(event_id, str) else event_id
                event = event_collection.find_one({"_id": event_obj_id})
                if event:
                    # Ajouter l'ID pour les templates
                    if '_id' in event:
                        event['id'] = str(event['_id'])
                    
                    liked_events.append(event)
            except Exception as e:
                print(f"Erreur lors de la récupération de l'événement: {e}")
    

    return render(request, 'event_manager/profile.html', {
        'user': user,
        'bookings': bookings,
        'error': error,
        'success': success,
        'filtered_events': filtered_events,
        'events_created_count': events_created_count,
        'participations_count': participations_count,
        'likes_count': likes_count,
        'liked_events': liked_events
    })


@login_required
def cancel_booking(request, event_id):
    """Vue pour annuler une réservation existante (version simplifiée)"""
    try:
        # Convertir l'ID en ObjectId
        event_id_obj = ObjectId(event_id)
        current_user_id = ObjectId(str(request.user.get('_id')))
        
        # Récupérer l'événement avec la réservation de l'utilisateur
        event = event_collection.find_one({
            "_id": event_id_obj,
            "bookings.user_id": current_user_id
        })
        
        if not event:
            messages.error(request, "Réservation introuvable ou vous n'êtes pas autorisé à l'annuler.")
            return redirect('profile')
        
        # Trouver la réservation de l'utilisateur
        user_booking = None
        booking_index = None
        
        for i, booking in enumerate(event.get('bookings', [])):
            if str(booking.get('user_id')) == str(current_user_id):
                user_booking = booking
                booking_index = i
                break
        
        if not user_booking:
            messages.error(request, "Votre réservation n'a pas été trouvée.")
            return redirect('profile')
        
        # Récupérer le nombre de places à libérer
        num_seats = int(user_booking.get('num_seats', 1))
        
        # Mettre à jour le nombre de places disponibles pour l'événement
        current_remaining = event.get('remaining_seat', 0)
        new_remaining = current_remaining + num_seats
        
        # Supprimer la réservation du tableau bookings et mettre à jour remaining_seat
        event_collection.update_one(
            {"_id": event_id_obj},
            {
                "$unset": {f"bookings.{booking_index}": 1},  # Marquer l'élément comme supprimé
                "$set": {"remaining_seat": new_remaining}
            }
        )
        
        # Nettoyer le tableau en supprimant les éléments null
        event_collection.update_one(
            {"_id": event_id_obj},
            {"$pull": {"bookings": None}}
        )
        
        messages.success(request, "Votre réservation a été annulée avec succès.")
        
    except Exception as e:
        messages.error(request, f"Une erreur est survenue lors de l'annulation de la réservation : {str(e)}")
    
    return redirect('profile')



@login_required
def payment(request, event_id):
    try:
        event = event_collection.find_one({"_id": ObjectId(event_id)})
        if not event:
            raise Http404("Événement introuvable.")
    except Exception as e:
        raise Http404(f"Erreur : {str(e)}")

    booking_data = request.session.get('booking_data')
    if not booking_data:
        raise Http404("Aucune donnée de réservation trouvée.")
    
    # Traitement du paiement
    if request.method == 'POST':
        numero = request.POST.get('numero')
        methode = request.POST.get('methode')
        paiement_confirme = request.POST.get('paiement_confirme') == 'true'

        if paiement_confirme and numero:
            # Vérifier la disponibilité des places
            nb_place = int(booking_data["num_seats"])
            place_restante = int(event["remaining_seat"])
            place_restante -= nb_place
            
            if place_restante >= 0:  
                # Générer un numéro de référence unique
                reference_number = f"EVT-{methode.upper()}-{datetime.now().strftime('%y%m%d')}-"
                
                # Créer l'enregistrement de réservation
                booking = {
                    'user_id': request.user['_id'],
                    'name': booking_data["name"],
                    'email': booking_data["email"],
                    'num_seats': booking_data["num_seats"],
                    'event_title': event["title"],
                    'payment_method': methode,
                    'payment_phone': numero,
                    'payment_status': 'confirmed',
                    'reference_number': reference_number,
                    'created_at': datetime.utcnow(),
                }
                
                # Mettre à jour le nombre de places restantes
                event_collection.update_one(
                    {"_id": ObjectId(event_id)}, 
                    {
                        "$set": {"remaining_seat": place_restante},
                        "$push": {"bookings": booking}
                    }
                )
                booking_data['reference_number'] = reference_number
                booking_data['payment_method'] = methode
                booking_data['payment_status'] = 'confirmed'
                request.session['booking_data'] = booking_data
                
                # Rediriger vers la page de confirmation
                return redirect('booking_confirmation', event_id=event_id)
            else:
                # Pas assez de places disponibles
                messages.error(request, "Désolé, il n'y a plus assez de places disponibles.")
        else:
            # Données de paiement invalides
            messages.error(request, "Veuillez fournir un numéro de téléphone valide.")

    # Si nous arrivons ici, c'est une requête GET ou le paiement a échoué
    price_per_seat = event.get("price", 0)
    total_price = int(booking_data.get("num_seats", 1)) * price_per_seat

    context = {
        'event': event,
        'booking': booking_data,
        'total_price': total_price
    }

    return render(request, 'event_manager/payment.html', context)
  
# API pour la pagination AJAX des événements
def events_paginated_api(request):
    try:
        # Récupérer la page demandée
        page = request.GET.get('page', 1)
        
        # Récupérer les paramètres de recherche et de filtre
        search_query = request.GET.get('search', '')
        type_filter = request.GET.get('type', '')
        date_filter = request.GET.get('date', '')
        city_filter = request.GET.get('city', '')
        
        # Récupérer les événements avec les mêmes filtres que dans home
        try:
            # Construction du filtre MongoDB
            filter_query = {}
            
            # Appliquer le filtre de recherche (sur le titre ou la description)
            if search_query:
                filter_query['$or'] = [
                    {'title': {'$regex': search_query, '$options': 'i'}},
                    {'description': {'$regex': search_query, '$options': 'i'}}
                ]
            
            # Appliquer le filtre de type
            if type_filter:
                filter_query['type'] = {'$regex': type_filter, '$options': 'i'}
            
            # Appliquer le filtre de ville
            if city_filter:
                filter_query['location'] = {'$regex': city_filter, '$options': 'i'}
            
            # Appliquer le filtre de date
            now = datetime.now()
            if date_filter == 'today':
                today_start = datetime(now.year, now.month, now.day)
                today_end = datetime(now.year, now.month, now.day, 23, 59, 59)
                filter_query['date'] = {'$gte': today_start, '$lte': today_end}
            elif date_filter == 'tomorrow':
                tomorrow = now + timezone.timedelta(days=1)
                tomorrow_start = datetime(tomorrow.year, tomorrow.month, tomorrow.day)
                tomorrow_end = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 23, 59, 59)
                filter_query['date'] = {'$gte': tomorrow_start, '$lte': tomorrow_end}
            elif date_filter == 'weekend':
                days_until_saturday = (5 - now.weekday()) % 7
                if days_until_saturday == 0 and now.hour >= 23:  # Si c'est samedi soir, on vise le WE suivant
                    days_until_saturday = 7
                next_saturday = now + timezone.timedelta(days=days_until_saturday)
                next_sunday = next_saturday + timezone.timedelta(days=1)
                weekend_start = datetime(next_saturday.year, next_saturday.month, next_saturday.day)
                weekend_end = datetime(next_sunday.year, next_sunday.month, next_sunday.day, 23, 59, 59)
                filter_query['date'] = {'$gte': weekend_start, '$lte': weekend_end}
            elif date_filter == 'month':
                month_start = datetime(now.year, now.month, 1)
                if now.month == 12:
                    next_month = datetime(now.year + 1, 1, 1)
                else:
                    next_month = datetime(now.year, now.month + 1, 1)
                filter_query['date'] = {'$gte': month_start, '$lt': next_month}
            
            # Récupérer les événements filtrés
            events = list(event_collection.find(filter_query))
            parsed_events = []
            for event in events:
                parsed_event = event.copy()
                if isinstance(event.get("date"), str):
                    try:
                        parsed_event["date"] = datetime.fromisoformat(event["date"].replace("Z", "+00:00"))
                    except Exception as e:
                        parsed_event["date"] = None
                        
                # Assurer que chaque événement a une propriété 'id' pour les templates
                if '_id' in parsed_event and 'id' not in parsed_event:
                    parsed_event['id'] = str(parsed_event['_id'])
                elif 'id' not in parsed_event:
                    # Si ni _id ni id n'existe, utiliser l'index comme fallback
                    parsed_event['id'] = events.index(event) + 1
                
                parsed_events.append(parsed_event)
            
            # Trier les événements par date (du plus proche au plus éloigné)
            parsed_events.sort(key=lambda x: x.get('date', datetime.max))
        except Exception as e:
            # Fallback sur les événements statiques en cas d'erreur
            parsed_events = get_sample_events()
        
        # Pagination : 10 événements par page
        paginator = Paginator(parsed_events, 10)
        
        try:
            events_page = paginator.page(page)
        except PageNotAnInteger:
            events_page = paginator.page(1)
        except EmptyPage:
            events_page = paginator.page(paginator.num_pages)
        
        # Rendre le HTML des événements
        events_html = render_to_string('event_manager/partials/event_cards.html', {
            'events': events_page,
        }, request=request)
        
        # Rendre le HTML de la pagination
        pagination_html = render_to_string('event_manager/partials/pagination.html', {
            'page_obj': events_page,
        }, request=request)
        
        # Retourner les données en JSON
        return JsonResponse({
            'success': True,
            'events_html': events_html,
            'pagination_html': pagination_html,
            'current_page': events_page.number,
            'total_pages': paginator.num_pages,
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
def register_for_event(request, event_id):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        num_seats = request.POST.get("num_seats")
        booking_data = {
            "name": name,
            "email": email,
            "num_seats": num_seats
        }

        request.session['booking_data'] = booking_data
        
        try:
            # Récupérer l'événement depuis la collection
            event = event_collection.find_one({"_id": ObjectId(event_id)})
            if not event:
                messages.error(request, "Événement introuvable.")
                return redirect('home')
            
            if event.get("price", 0) == 0:
                place_restante=event.get("remaining_seat")
                place_restante-=int(num_seats)
                if place_restante >=0:
                    booking = {
                       "user_id": request.user['_id'],
                        "name": name,
                        "email": email,
                        "num_seats": num_seats,
                        'created_at': datetime.utcnow(),
                    }
                    event_collection.update_one(
                        {"_id": ObjectId(event_id)},
                        {
                            "$set": {"remaining_seat": place_restante},
                            "$push": {"bookings": booking}
                        }
                    )

                    return redirect('booking_confirmation', event_id=event_id)
            
            else:
                return redirect('payment', event_id=event_id)
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la réservation : {str(e)}")
            return redirect('event_detail', event_id=event_id)


    return redirect('event_detail', event_id=event_id)  # fallback

@login_required
def booking_confirmation(request, event_id):
    try:
        event = event_collection.find_one({"_id": ObjectId(event_id)})
        if not event:
            raise Http404("Événement introuvable.")
    except Exception as e:
        raise Http404(f"Erreur : {str(e)}")

    booking_data = request.session.get('booking_data')

    if not booking_data:
        raise Http404("Aucune donnée de réservation trouvée.")

    price_per_seat = event.get("price", 0)
    total_price = int(booking_data.get("num_seats", 1)) * price_per_seat
    
    # Création du contenu du QR code
    booking_id = booking_data.get('id', 'TEMP-' + str(ObjectId()))
    reference_number = booking_data.get('reference_number', 'EVT-2023-') + str(booking_id)
    
    qr_data = {
        'event_id': str(event.get('_id')),
        'event_title': event.get('title'),
        'booking_id': booking_id,
        'reference_number': reference_number,
        'attendee_name': booking_data.get('name'),
        'num_seats': booking_data.get('num_seats'),
        'date': event.get('date').isoformat() if isinstance(event.get('date'), datetime) else str(event.get('date'))
    }
    
    # Génération du QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(json.dumps(qr_data))
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    # Conversion de l'image en base64 pour l'affichage
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    context = {
        'event': event,
        'booking': booking_data,
        'total_price': total_price,
        'qr_code_base64': qr_code_base64,
        'reference_number': reference_number
    }

    return render(request, 'event_manager/booking_confirmation.html', context)
  

@csrf_exempt
@login_required
def toggle_like(request):
    if request.method == "POST":
        data = json.loads(request.body)
        event_id_str = data.get("event_id")
        
        # Utiliser l'ID de l'utilisateur authentifié au lieu de celui envoyé dans les données
        # Pour MongoDB, l'ID est stocké dans request.user['_id']
        if not request.is_authenticated:
            return JsonResponse({"error": "User not authenticated"}, status=401)
            
        # Récupérer l'ID de l'utilisateur depuis l'objet request.user (MongoDB)
        user_id = str(request.user['_id'])
        username = str(request.user['username'])
        try:
            event_id_obj = ObjectId(event_id_str)
        except:
            return JsonResponse({"error": "Invalid event_id"}, status=400)


        # Récupérer l'événement
        event = event_collection.find_one({"_id": event_id_obj})
        if not event:
            return JsonResponse({"error": "Event not found"}, status=404)

        # Récupérer la liste des likes (ou initialiser si elle n'existe pas)
        likes = event.get('likes', [])
        
        existing_like = None
        for like in likes:
            if (like['user']).get('user_id') == user_id:
                existing_like = like
                break

        if existing_like:
            # Unlike 
            event_collection.update_one(
                {"_id": event_id_obj},
                {"$pull": {"likes": {"user.user_id": user_id}}}
            )
            
            event = event_collection.find_one({"_id": event_id_obj})
            likes = event.get("likes", [])
            likes_count = len(likes)
            return JsonResponse({"status": "unliked", "likes_count": likes_count})

        else:
            # Like
            new_like = {
                "user": {
                    "user_id": user_id,
                    "username": username,
                },
                "liked_at": datetime.now(),
            }
            
            event_collection.update_one(
                {"_id": event_id_obj},
                {"$push": {"likes": new_like}}
            )
            event = event_collection.find_one({"_id": event_id_obj})
            likes = event.get("likes", [])
            likes_count = len(likes)

    return JsonResponse({"status": "liked", "likes_count": likes_count})


@login_required
def invitation(request, event_id):
    event = event_collection.find_one({'_id': ObjectId(event_id)})

    if not event:
        return render(request, '404.html', status=404)

    event['id_str'] = str(event['_id'])

    event_url = request.build_absolute_uri(
        reverse('event_detail', kwargs={'event_id': str(event['_id'])})
    )
    context = {
        'event': event,
        'event_url': event_url,
    }

    return render(request, 'event_manager/invitation.html', context)


@login_required
def send_invitations(request, event_id):
    if request.method == 'POST':
        event = event_collection.find_one({'_id': ObjectId(event_id)})

        if not event:
            return render(request, '404.html', status=404)

        raw_contacts = request.POST.get('friends', '')
        contacts = [c.strip() for c in raw_contacts.split(',') if c.strip()]

        saved = 0
        for contact in contacts:
            # Optionnel : envoyer email
            if '@' in contact:  # Simple détection d'email
                try:
                    send_mail(
                        subject=f"Invitation à l'événement {event.get('title', '')}",
                        message=f"Vous êtes invité à participer à l’événement : {event.get('title', '')}",
                        from_email='votre_adresse@exemple.com',
                        recipient_list=[contact],
                        fail_silently=True,
                    )
                except Exception as e:
                    print(f"Erreur d'envoi à {contact} : {e}")

            saved += 1

        messages.success(request, f"{saved} invitations ont été envoyées et enregistrées.")
       
    return redirect('invitation', event_id=event_id)


def reservation (request,event_id):
    event=event_collection.find_one({"_id": ObjectId(event_id)})
    reservations = list(event.get('bookings', []))
    place_vendues=int(event["total_seats"])-int(event["remaining_seat"])
    total=int(event["total_seats"])
    return render(request,"event_manager/reservations.html",{'reservations':reservations,"evenement":event,"place_vendues":place_vendues,"total":total})


@login_required
def view_ticket(request, event_id):
    """Affiche le billet pour l'utilisateur connecté pour un événement donné"""
    try:
        # Convertir event_id en ObjectId
        event_id_obj = ObjectId(event_id)
        current_user_id = ObjectId(str(request.user.get('_id')))
        
        # Récupérer l'événement avec la réservation de l'utilisateur
        event = event_collection.find_one({
            "_id": event_id_obj,
            "bookings.user_id": current_user_id
        })
        
        if not event:
            messages.error(request, "Aucune réservation trouvée pour cet événement.")
            return redirect('profile')
        
        # Trouver la réservation de l'utilisateur
        user_booking = None
        booking_index = None
        
        for i, booking in enumerate(event.get('bookings', [])):
            if str(booking.get('user_id')) == str(current_user_id):
                user_booking = booking
                booking_index = i
                break
        
        if not user_booking:
            messages.error(request, "Votre réservation n'a pas été trouvée.")
            return redirect('profile')
        
        # Générer un numéro de référence si non existant
        reference_number = user_booking.get('reference_number')
        if not reference_number:
            reference_number = f"EVT-{datetime.now().strftime('%Y%m')}-{str(event_id_obj)[-6:]}-{booking_index}"
            
            # Mettre à jour la réservation avec le numéro de référence
            event_collection.update_one(
                {"_id": event_id_obj},
                {"$set": {f"bookings.{booking_index}.reference_number": reference_number}}
            )
            user_booking['reference_number'] = reference_number
        
        # Préparer les données pour le QR code
        qr_data = {
            "event": event.get('description', 'Événement'),
            "reference": reference_number,
            "name": user_booking.get('name'),
            "email": user_booking.get('email'),
            "seats": user_booking.get('num_seats'),
            "date": event.get('date').strftime('%Y-%m-%d %H:%M') if isinstance(event.get('date'), datetime) else str(event.get('date')),
            "location": event.get('location')
        }
        
        # Générer le QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(json.dumps(qr_data))
        qr.make(fit=True)
        
        # Créer une image à partir du QR code
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convertir l'image en base64 pour l'affichage
        buffer = io.BytesIO()
        img.save(buffer)
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        # Calculer le prix total
        total_price = float(event.get('price', 0)) * int(user_booking.get('num_seats', 1))
        
        # Contexte pour le template
        context = {
            'event': event,
            'booking': user_booking,
            'qr_code_base64': qr_code_base64,
            'reference_number': reference_number,
            'total_price': total_price,
            'booking_index': booking_index,
            'event_id': str(event_id_obj)
        }
        
        return render(request, 'event_manager/view_ticket.html', context)
        
    except Exception as e:
        messages.error(request, f"Une erreur est survenue: {str(e)}")
        return redirect('profile')


@login_required
def delete_comment(request, event_id, comment_index):
    """Permet à un utilisateur de supprimer son propre commentaire"""
    try:
        # Vérifier que les paramètres ne sont pas vides
        if not event_id or comment_index is None:
            messages.error(request, "Paramètres manquants pour la suppression.")
            return redirect(request.META.get('HTTP_REFERER', 'home'))
        
        # Convertir l'event_id en ObjectId et comment_index en int
        try:
            event_id_obj = ObjectId(event_id)
            comment_idx = int(comment_index)
        except Exception as e:
            messages.error(request, f"Format de paramètres invalide: {str(e)}")
            return redirect(request.META.get('HTTP_REFERER', 'home'))
        
        # Récupérer l'événement
        event = event_collection.find_one({"_id": event_id_obj})
        if not event:
            messages.error(request, "Cet événement n'existe pas.")
            return redirect(request.META.get('HTTP_REFERER', 'home'))
        
        # Vérifier que l'index du commentaire est valide
        comments = event.get('comments', [])
        if comment_idx < 0 or comment_idx >= len(comments):
            messages.error(request, "Commentaire non trouvé.")
            return redirect('event_detail', event_id=event_id)
        
        # Vérifier que l'utilisateur connecté est l'auteur du commentaire
        comment_to_delete = comments[comment_idx]
        if comment_to_delete.get('user') != request.user.get('username'):
            messages.error(request, "Vous ne pouvez pas supprimer ce commentaire.")
            return redirect('event_detail', event_id=event_id)
        
        # Supprimer le commentaire en utilisant l'index
        event_collection.update_one(
            {"_id": event_id_obj},
            {"$unset": {f"comments.{comment_idx}": 1}}
        )
        
        # Nettoyer les éléments null du tableau
        event_collection.update_one(
            {"_id": event_id_obj},
            {"$pull": {"comments": None}}
        )
        
        messages.success(request, "Commentaire supprimé avec succès.")
        return redirect('event_detail', event_id=event_id)
        
    except Exception as e:
        messages.error(request, f"Une erreur est survenue lors de la suppression du commentaire: {str(e)}")
        return redirect(request.META.get('HTTP_REFERER', 'home'))


# Fonctions pour la réinitialisation de mot de passe
def password_reset_view(request):
    """Vue pour demander une réinitialisation de mot de passe"""
    if request.method == 'POST':
        email = request.POST.get('email')
        
        # Vérifier si l'utilisateur existe
        user = user_collection.find_one({"email": email})
        
        if user:
            # Générer un token unique pour la réinitialisation
            uid = str(user['_id'])
            token = default_token_generator.make_token(MongoUser(user))
            
            # Encoder l'ID utilisateur pour l'URL
            uidb64 = urlsafe_base64_encode(force_bytes(uid))
            
            # Construire l'URL de réinitialisation
            reset_url = request.build_absolute_uri(
                reverse('password_reset_confirm', kwargs={'uidb64': uidb64, 'token': token})
            )
            
            # Envoyer l'email
            subject = 'Réinitialisation de votre mot de passe Eventure'
            message = f"Bonjour {user.get('first_name', '')},\n\n"
            message += f"Vous avez demandé une réinitialisation de votre mot de passe. "
            message += f"Veuillez cliquer sur le lien suivant pour définir un nouveau mot de passe :\n\n"
            message += f"{reset_url}\n\n"
            message += f"Si vous n'avez pas demandé cette réinitialisation, veuillez ignorer cet email.\n\n"
            message += f"Cordialement,\nL'équipe Eventure"
            
            try:
                send_mail(
                    subject,
                    message,
                    'noreply@eventure.com',  # Adresse d'expéditeur
                    [email],
                    fail_silently=False,
                )
                return redirect('password_reset_done')
            except Exception as e:
                return render(request, 'event_manager/password_reset.html', {
                    'error': f"Erreur lors de l'envoi de l'email: {str(e)}"
                })
        else:
            # Ne pas révéler que l'utilisateur n'existe pas pour des raisons de sécurité
            # Rediriger comme si tout s'était bien passé
            return redirect('password_reset_done')
    
    return render(request, 'event_manager/password_reset.html')


def password_reset_done_view(request):
    """Vue affichée après la demande de réinitialisation"""
    return render(request, 'event_manager/password_reset_done.html')


def password_reset_confirm_view(request, uidb64, token):
    """Vue pour définir un nouveau mot de passe"""
    try:
        # Décoder l'ID utilisateur
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = user_collection.find_one({"_id": ObjectId(uid)})
        
        # Vérifier que l'utilisateur existe et que le token est valide
        if user and default_token_generator.check_token(MongoUser(user), token):
            if request.method == 'POST':
                password = request.POST.get('password')
                password_confirm = request.POST.get('password_confirm')
                
                # Vérifier que les mots de passe correspondent
                if password != password_confirm:
                    return render(request, 'event_manager/password_reset_confirm.html', {
                        'error': 'Les mots de passe ne correspondent pas.'
                    })
                
                # Mettre à jour le mot de passe
                hashed_password = make_password(password)
                user_collection.update_one(
                    {"_id": ObjectId(uid)},
                    {"$set": {"password": hashed_password}}
                )
                
                return redirect('password_reset_complete')
            
            return render(request, 'event_manager/password_reset_confirm.html')
        else:
            return render(request, 'event_manager/password_reset_confirm.html', {
                'error': 'Le lien de réinitialisation est invalide ou a expiré.'
            })
    except Exception as e:
        return render(request, 'event_manager/password_reset_confirm.html', {
            'error': f"Une erreur est survenue: {str(e)}"
        })


def password_reset_complete_view(request):
    """Vue affichée après la réinitialisation réussie du mot de passe"""
    return render(request, 'event_manager/password_reset_complete.html')


# Gestionnaire d'erreur 404 personnalisé
def handler404(request, exception):
    return render(request, '404.html', status=404)
