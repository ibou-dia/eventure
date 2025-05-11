def auth_context_processor(request):
    """
    Context processor qui ajoute les variables d'authentification à tous les templates.
    """
    return {
        'is_authenticated': getattr(request, 'is_authenticated', False),
        'user': getattr(request, 'user', None),
    }
