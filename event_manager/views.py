from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from .models import event_collection, user_collection, booking_collection, comments_collection,MongoUser
from datetime import datetime
from django.db.models import Count
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.template.loader import render_to_string
from bson.objectid import ObjectId
from django.contrib.auth.hashers import check_password
from .middleware import login_required  # Utiliser notre propre décorateur login_required
from bson.binary import Binary
from datetime import datetime
import base64


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

# def event_detail(request, event_id):
#     # En mode statique, on retrouve l'événement dans notre liste d'exemples
#     sample_events = get_sample_events()
#     if isinstance(sample_events, list):
#         # Mode données fictives
#         event = next((e for e in sample_events if e.get('id', sample_events.index(e) + 1) == event_id), None)
#         if not event:
#             # Si l'ID ne correspond pas, prendre le premier (pour démo uniquement)
#             event = sample_events[0]
#             event['id'] = event_id
#         # Simuler des commentaires
#         comments = [
#             {'user': 'Jean Dupont', 'content': 'Super événement !', 'created_at': timezone.now() - timezone.timedelta(days=1)},
#             {'user': 'Marie Martin', 'content': 'J\'ai hâte d\'y être !', 'created_at': timezone.now() - timezone.timedelta(hours=5)},
#         ]
#     else:
#         # Mode base de données MongoDB
#         try:
#             # Convertir l'ID en ObjectId si possible et récupérer l'événement
#             mongo_id = try_convert_to_objectid(event_id)
#             event = event_collection.find_one({"_id": mongo_id})
                
#             if not event:
#                 # Si aucun événement n'est trouvé, utiliser un événement par défaut
#                 event = sample_events[0] if sample_events else {}
#                 event['id'] = event_id
#             else:
#                 # Assurer que l'événement a une propriété 'id' pour les templates
#                 # Si MongoDB utilise des ObjectId, convertir en string
#                 if '_id' in event and 'id' not in event:
#                     event['id'] = str(event['_id'])
#             # Pour l'instant, simuler des commentaires
#             comments = []
#         except Exception as e:
#             print(f"Erreur lors de la récupération de l'événement {event_id}: {e}")
#             # En cas d'erreur, utiliser un événement par défaut
#             event = sample_events[0] if sample_events else {
#                 'title': 'Événement non trouvé',
#                 'description': 'Désolé, l\'événement que vous recherchez n\'existe pas ou a été supprimé.',
#                 'date': timezone.now(),
#                 'location': 'Non disponible',
#                 'total_seats': 0,
#                 'remaining_seats': 0,
#                 'price': 0.00,
#                 'id': event_id
#             }
#             comments = []
    
#     return render(request, 'event_manager/event_detail.html', {
#         'event': event,
#         'comments': comments
#     })

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
    comments = list(comments_collection.find({"event_id": event_id}).sort("created_at", -1))
    
    # Pour chaque commentaire, convertir l'ObjectId en chaîne
    for comment in comments:
        comment['id'] = str(comment['_id'])
    
    


    user_has_liked = False
    if request.user.get('is_authenticated'):
        # Déterminer l'ID utilisateur en fonction du type d'objet user
        if isinstance(request.user, dict):
            user_id = str(request.user.get('_id'))
        else:
            user_id = str(request.user.id)
            
        likes = event.get('likes', [])
        user_has_liked = any(like.get('user_id') == user_id for like in likes)
    
    context = {
        'event': event,
        'comments': comments,
        'user_has_liked': user_has_liked,
        # Autres éléments du contexte
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
                "likes_count":0,
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
def register_for_event(request, event_id):
    if request.method == 'POST':
        # Traitement du formulaire de réservation
        name = request.POST.get('name')
        email = request.POST.get('email')
        num_seats = int(request.POST.get('num_seats', 1))
        
        # Validation simplifiée
        if not all([name, email, num_seats > 0]):
            messages.error(request, 'Veuillez remplir tous les champs correctement.')
            return redirect('event_detail', event_id=event_id)
        
        # En mode statique, simuler une réservation réussie
        # Dans un cas réel, nous créerions une réservation dans la base de données MongoDB
        try:
            # Vérifier si l'événement existe dans la collection
            # Convertir l'ID en ObjectId si possible
            mongo_id = try_convert_to_objectid(event_id)
            event = event_collection.find_one({"_id": mongo_id})
            
            # Si nous avons trouvé l'événement, traiter la réservation
            if event:
                # Simuler une réservation
                booking_id = 1  # Simuler un ID de réservation
                
                # Dans un environnement de production, nous ajouterions la réservation à une collection
                booking_data = {
                    "event_id": event_id,
                    "user_id": request.user.id,
                    "name": name,
                    "email": email,
                    "num_seats": num_seats,
                    "payment_status": 'completed' if event.get('price', 0) > 0 else 'pending'
                }
                booking_id = booking_collection.insert_one(booking_data).inserted_id
                
                # Rediriger vers la page de confirmation
                return redirect('booking_confirmation', event_id=event_id, booking_id=booking_id)
            else:
                # En mode statique/démo, on simule avec l'ID 1
                messages.success(request, 'Réservation effectuée avec succès!')
                return redirect('booking_confirmation', event_id=event_id, booking_id=1)
                
        except Exception as e:
            messages.error(request, f'Une erreur est survenue lors de la réservation: {str(e)}')
            return redirect('event_detail', event_id=event_id)
    
    # Si ce n'est pas un POST, rediriger vers la page de détails
    return redirect('event_detail', event_id=event_id)



# Page de confirmation de réservation
@login_required
def booking_confirmation(request, event_id, booking_id):
    # En mode statique/démo, simuler une réservation et un événement
    try:
        # Tenter de récupérer l'événement depuis MongoDB
        mongo_id = try_convert_to_objectid(event_id)
        event = event_collection.find_one({"_id": mongo_id})
        
        # Pour le moment, nous simulons les réservations
        booking = None  # Aucune collection de réservations pour l'instant

        if not event or not booking:
            # Simuler des données pour la démo
            event = {
                'title': 'Concert de Jazz',
                'description': 'Une soirée exceptionnelle avec les meilleurs artistes de jazz.',
                'date': timezone.now() + timezone.timedelta(days=10),
                'location': 'Salle Pleyel, Paris',
                'total_seats': 200,
                'remaining_seats': 150,
                'price': 25.00,
            }
            
            booking = {
                'id': booking_id,
                'name': request.user.username if hasattr(request, 'user') else 'Jean Dupont',
                'email': request.user.email if hasattr(request, 'user') else 'utilisateur@exemple.com',
                'num_seats': 2,
                'registration_date': timezone.now(),
                'payment_status': 'completed',
                'payment_status_display': 'Payé'
            }
        
        # Calculer le prix total
        if isinstance(event, dict):
            total_price = event['price'] * booking['num_seats'] if 'price' in event and 'num_seats' in booking else 0
        else:
            total_price = event.price * booking.num_seats
            
        return render(request, 'event_manager/booking_confirmation.html', {
            'event': event,
            'booking': booking,
            'total_price': total_price
        })
        
    except Exception as e:
        messages.error(request, f"Une erreur est survenue lors de l'affichage de la confirmation: {str(e)}")
        return redirect('home')

# Gestion des commentaires
# @login_required
# def add_comment(request, event_id):
#     if request.method == 'POST':
#         content = request.POST.get('content')
        
#         if not content:
#             messages.error(request, 'Le commentaire ne peut pas être vide.')
#         else:
#             # En mode statique, simuler l'ajout d'un commentaire réussi
#             messages.success(request, 'Commentaire ajouté avec succès!')
        
#         return redirect('event_detail', event_id=event_id)
    
#     return redirect('event_detail', event_id=event_id)


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
            "event_id": event_id,  # Garder l'ID comme chaîne pour faciliter les requêtes
            "user": request.user.get('username'),  # ou request.user.id selon votre système d'authentification
            "content": content,
            "created_at": datetime.now()
        }
        
        # Insérer le commentaire dans la collection
        result = comments_collection.insert_one(comment)
        
        if result.inserted_id:
            messages.success(request, 'Commentaire ajouté avec succès!')
        else:
            messages.error(request, "Erreur lors de l'ajout du commentaire.")
        
        return redirect('event_detail', event_id=event_id)
    
    return redirect('event_detail', event_id=event_id)




# Gestion des likes
# @login_required
# def like_event(request, event_id):
#     # En mode statique, simuler un like réussi
#     if request.is_ajax():
#         return JsonResponse({'status': 'success', 'likes_count': 10})
#     else:
#         return redirect('event_detail', event_id=event_id)

@login_required
def like_event(request, event_id):
    # Conversion de l'ID de l'événement en ObjectId
    event_id = ObjectId(event_id)
    
    # Récupérer l'ID et le nom d'utilisateur (en tenant compte que request.user est un dict)
    if isinstance(request.user, dict):
        user_id = str(request.user.get('_id'))
        username = request.user.get('username')
    else:
        # Si c'est un objet User Django standard
        user_id = str(request.user.id)
        username = request.user.username
    
    
    # Récupérer l'événement
    event = event_collection.find_one({"_id": event_id})
    
    # Initialiser la liste des likes si elle n'existe pas
    if not event.get('likes'):
        event_collection.update_one(
            {"_id": event_id},
            {"$set": {"likes": []}}
        )
        event['likes'] = []
    
    # Vérifier si l'utilisateur a déjà liké
    user_like = next((like for like in event.get('likes', []) 
                    if like.get('user_id') == user_id), None)
                    
    # Toggle like (ajouter ou supprimer)
    if user_like:
        # Supprimer le like
        event_collection.update_one(
            {"_id": event_id},
            {"$pull": {"likes": {"user_id": user_id}}}
        )
        action = 'unliked'
    else:
        # Ajouter le like
        like_data = {
            "user_id": user_id,
            "username": username,
            "timestamp": datetime.now()
        }
        event_collection.update_one(
            {"_id": event_id},
            {"$push": {"likes": like_data}}
        )
        action = 'liked'
    
    # Récupérer le nombre de likes mis à jour
    updated_event = event_collection.find_one({"_id": event_id})
    likes_count = len(updated_event.get('likes', []))
    
    # Répondre en fonction du type de requête
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  # Méthode plus moderne que is_ajax()
        return JsonResponse({
            'status': 'success', 
            'action': action,
            'likes_count': likes_count
        })
    else:
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
    
    # Récupérer les réservations de l'utilisateur (simuler pour l'instant)
    # Dans un cas réel, nous les récupérerions de la base de données MongoDB
    bookings = [
        {
            'id': 1,
            'event': {
                'title': 'Concert de Jazz',
                'date': timezone.now() + timezone.timedelta(days=5),
                'location': 'Salle Pleyel, Paris'
            },
            'num_seats': 2,
            'total_price': 50.00,
            'status': 'confirmed'
        },
        {
            'id': 2,
            'event': {
                'title': 'Festival de Cinéma',
                'date': timezone.now() + timezone.timedelta(days=15),
                'location': 'Cinémathèque, Lyon'
            },
            'num_seats': 1,
            'total_price': 15.00,
            'status': 'pending'
        }
    ]
    
    return render(request, 'event_manager/profile.html', {
        'user': user,
        'bookings': bookings,
        'error': error,
        'success': success,
        'filtered_events':filtered_events
    })



def pay_view(request, event_id):
    evenement = get_object_or_404(event_collection, event_id=event_id)
    return render(request, 'event_manager/pay_page.html', {'evenement': evenement})
    

# API pour la pagination AJAX des événements
def events_paginated_api(request):
    try:
        # Récupérer la page demandée
        page = request.GET.get('page', 1)
        
        # Récupérer les événements
        try:
            events = list(event_collection.find())
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

