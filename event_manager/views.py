from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from .models import event_collection
from datetime import datetime
from django.db.models import Count
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.template.loader import render_to_string
from bson.objectid import ObjectId
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
            return sample_events
        # Si des événements existent déjà, les retourner
        events = list(event_collection.find())
        return events
    except Exception as e:
        # En cas d'erreur, retourner une liste vide
        print(f"Erreur lors de la récupération des événements: {e}")
        return []

# Vues principales
def home(request):
    # Récupérer les événements (mode statique ou base de données)
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
    # En mode statique, on retrouve l'événement dans notre liste d'exemples
    sample_events = get_sample_events()
    if isinstance(sample_events, list):
        # Mode données fictives
        event = next((e for e in sample_events if e.get('id', sample_events.index(e) + 1) == event_id), None)
        if not event:
            # Si l'ID ne correspond pas, prendre le premier (pour démo uniquement)
            event = sample_events[0]
            event['id'] = event_id
        # Simuler des commentaires
        comments = [
            {'user': 'Jean Dupont', 'content': 'Super événement !', 'created_at': timezone.now() - timezone.timedelta(days=1)},
            {'user': 'Marie Martin', 'content': 'J\'ai hâte d\'y être !', 'created_at': timezone.now() - timezone.timedelta(hours=5)},
        ]
    else:
        # Mode base de données MongoDB
        try:
            # Convertir l'ID en ObjectId si possible et récupérer l'événement
            mongo_id = try_convert_to_objectid(event_id)
            event = event_collection.find_one({"_id": mongo_id})
                
            if not event:
                # Si aucun événement n'est trouvé, utiliser un événement par défaut
                event = sample_events[0] if sample_events else {}
                event['id'] = event_id
            else:
                # Assurer que l'événement a une propriété 'id' pour les templates
                # Si MongoDB utilise des ObjectId, convertir en string
                if '_id' in event and 'id' not in event:
                    event['id'] = str(event['_id'])
            # Pour l'instant, simuler des commentaires
            comments = []
        except Exception as e:
            print(f"Erreur lors de la récupération de l'événement {event_id}: {e}")
            # En cas d'erreur, utiliser un événement par défaut
            event = sample_events[0] if sample_events else {
                'title': 'Événement non trouvé',
                'description': 'Désolé, l\'événement que vous recherchez n\'existe pas ou a été supprimé.',
                'date': timezone.now(),
                'location': 'Non disponible',
                'total_seats': 0,
                'remaining_seats': 0,
                'price': 0.00,
                'id': event_id
            }
            comments = []
    
    return render(request, 'event_manager/event_detail.html', {
        'event': event,
        'comments': comments
    })

def create_event(request):
    if request.method == 'POST':
        # Dans un contexte réel, on utiliserait un formulaire Django
        title = request.POST.get('title')
        description = request.POST.get('description')
        date_str = request.POST.get('date')
        location = request.POST.get('location')
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
                "description": description,
                "date": event_date,
                "location": location,
                "total_seats": total_seats,
                "price": price,
                'image': image_base64,
                'created_at': datetime.utcnow()
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
                # booking_data = {
                #     "event_id": event_id,
                #     "user_id": request.user.id,
                #     "name": name,
                #     "email": email,
                #     "num_seats": num_seats,
                #     "payment_status": 'completed' if event.get('price', 0) > 0 else 'pending'
                # }
                # booking_id = booking_collection.insert_one(booking_data).inserted_id
                
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
@login_required
def add_comment(request, event_id):
    if request.method == 'POST':
        content = request.POST.get('content')
        
        if not content:
            messages.error(request, 'Le commentaire ne peut pas être vide.')
        else:
            # En mode statique, simuler l'ajout d'un commentaire réussi
            messages.success(request, 'Commentaire ajouté avec succès!')
        
        return redirect('event_detail', event_id=event_id)
    
    return redirect('event_detail', event_id=event_id)

# Gestion des likes
@login_required
def like_event(request, event_id):
    # En mode statique, simuler un like réussi
    if request.is_ajax():
        return JsonResponse({'status': 'success', 'likes_count': 10})
    else:
        return redirect('event_detail', event_id=event_id)

# Pages d'authentification
def login_view(request):
    # Placeholder pour l'authentification
    return render(request, 'event_manager/login.html')

def register_view(request):
    # Placeholder pour l'inscription
    return render(request, 'event_manager/register.html')

@login_required
def profile_view(request):
    # Placeholder pour le profil utilisateur
    return render(request, 'event_manager/profile.html')



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

