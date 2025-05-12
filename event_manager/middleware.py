from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import MongoUser

class MongoAuthMiddleware(MiddlewareMixin):
    """
    Middleware pour gérer l'authentification avec MongoDB.
    Vérifie si l'utilisateur est connecté et ajoute l'objet utilisateur à la requête.
    """
    
    def process_request(self, request):
        # Récupérer l'ID utilisateur de la session
        user_id = request.session.get('user_id')
        
        # Ajouter un attribut is_authenticated à la requête
        request.is_authenticated = False
        request.user = None
        
        # Si l'ID utilisateur existe, récupérer l'utilisateur de MongoDB
        if user_id:
            user = MongoUser.get_user_by_id(user_id)
            
            if user:
                # Ajouter l'utilisateur à la requête
                request.user = user
                request.is_authenticated = True
            else:
                # Si l'utilisateur n'existe pas, effacer la session
                del request.session['user_id']
        
        # Pour restreindre l'accès aux vues avec décorateurs @login_required
        if hasattr(request, 'resolver_match') and request.resolver_match:
            view_func = request.resolver_match.func
            
            # Vérifier si la vue a un attribut login_required
            if getattr(view_func, 'login_required', False) and not request.is_authenticated:
                return HttpResponseRedirect(reverse('login') + '?next=' + request.path)
                
        return None

def login_required(view_func):
    """
    Décorateur pour restreindre l'accès aux vues aux utilisateurs connectés.
    """
    view_func.login_required = True
    return view_func
