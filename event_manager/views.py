from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from .models import event_collection
from datetime import datetime
from django.db.models import Count
from django.utils import timezone


# Pour simuler des données en attendant une intégration complète
def get_sample_events():
    # Si la base de données est vide, créons quelques événements fictifs
    if Event.objects.count() == 0:
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
    return Event.objects.all().annotate(likes_count=Count('likes'))

# Vues principales
def home(request):
    # events = get_sample_events()
    events =event_collection.find()
    parsed_events = []
    for event in events:
        parsed_event = event.copy()
        if isinstance(event.get("date"), str):
            try:
                parsed_event["date"] = datetime.fromisoformat(event["date"].replace("Z", "+00:00"))
            except Exception as e:
                parsed_event["date"] = None  # ou garde la chaîne originale
        parsed_events.append(parsed_event)
    return render(request, 'event_manager/home.html', {'events': parsed_events})

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
        # Mode base de données
        event = get_object_or_404(Event, pk=event_id)
        comments = event.comments.all().order_by('-created_at')
    
    return render(request, 'event_manager/event_detail.html', {
        'event': event,
        'comments': comments
    })

@login_required
def create_event(request):
    if request.method == 'POST':
        # Dans un contexte réel, on utiliserait un formulaire Django
        title = request.POST.get('title')
        description = request.POST.get('description')
        date_str = request.POST.get('date')
        location = request.POST.get('location')
        total_seats = int(request.POST.get('total_seats', 0))
        price = float(request.POST.get('price', 0))
        
        # Validation simplifiée
        if not all([title, description, date_str, location, total_seats >= 0]):
            messages.error(request, 'Veuillez remplir tous les champs correctement.')
            return render(request, 'event_manager/create_event.html')
        
        # En mode statique, rediriger simplement vers la page d'accueil
        # Simuler la création réussie
        messages.success(request, 'Événement créé avec succès!')
        return redirect('home')
        
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
        messages.success(request, 'Réservation effectuée avec succès!')
        return redirect('event_detail', event_id=event_id)
    
    # Si ce n'est pas un POST, rediriger vers la page de détails
    return redirect('event_detail', event_id=event_id)

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
