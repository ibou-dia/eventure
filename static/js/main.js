// Fonctions utilitaires pour le site de réservation d'événements

document.addEventListener('DOMContentLoaded', function() {
    // Animation de la navbar au scroll
    window.addEventListener('scroll', function() {
        const navbar = document.querySelector('.navbar');
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });
    
    // Animation d'entrée pour les cartes d'événements
    const animateCards = () => {
        const cards = document.querySelectorAll('.event-card');
        cards.forEach((card, index) => {
            // Ajouter une animation décalée pour chaque carte
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            card.style.transitionDelay = `${index * 0.1}s`;
            
            setTimeout(() => {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, 100);
        });
    };
    
    // Appeler l'animation des cartes
    animateCards();
    
    // Gestionnaire de messages flash
    const messages = document.querySelectorAll('.message');
    messages.forEach(message => {
        // Ajouter un bouton de fermeture à chaque message
        const closeBtn = document.createElement('button');
        closeBtn.innerHTML = '&times;';
        closeBtn.className = 'message-close';
        closeBtn.onclick = function() {
            message.style.opacity = '0';
            message.style.transform = 'translateY(-10px)';
            setTimeout(() => {
                message.remove();
            }, 300);
        };
        message.appendChild(closeBtn);
        
        // Fermeture automatique après 5 secondes
        setTimeout(() => {
            message.style.opacity = '0';
            message.style.transform = 'translateY(-10px)';
            setTimeout(() => {
                message.remove();
            }, 300);
        }, 5000);
    });
    
    // Animation des formulaires
    const formInputs = document.querySelectorAll('input, textarea, select');
    formInputs.forEach(input => {
        // Ajouter une classe active lorsque le champ est focusé ou contient une valeur
        input.addEventListener('focus', () => {
            input.parentElement.classList.add('input-active');
        });
        
        input.addEventListener('blur', () => {
            if (!input.value) {
                input.parentElement.classList.remove('input-active');
            }
        });
        
        // Vérifier si le champ a déjà une valeur au chargement
        if (input.value) {
            input.parentElement.classList.add('input-active');
        }
    });
});

// Fonctions API simulées (à remplacer par de vrais appels API avec Django)
const EventAPI = {
    // Récupérer tous les événements
    getEvents: function() {
        console.log('API: Récupération des événements');
        // Simuler un appel API
        return new Promise(resolve => {
            setTimeout(() => {
                // Ces données seraient normalement retournées par le backend
                resolve([]);
            }, 300);
        });
    },
    
    // Récupérer un événement par ID
    getEventById: function(eventId) {
        console.log(`API: Récupération de l'événement #${eventId}`);
        return new Promise(resolve => {
            setTimeout(() => {
                // Ces données seraient normalement retournées par le backend
                resolve(null);
            }, 300);
        });
    },
    
    // Récupérer les commentaires d'un événement
    getEventComments: function(eventId) {
        console.log(`API: Récupération des commentaires pour l'événement #${eventId}`);
        return new Promise(resolve => {
            setTimeout(() => {
                // Ces données seraient normalement retournées par le backend
                resolve([]);
            }, 300);
        });
    },
    
    // Ajouter un like à un événement
    likeEvent: function(eventId) {
        console.log(`API: Like de l'événement #${eventId}`);
        return new Promise(resolve => {
            setTimeout(() => {
                // La réponse contiendrait normalement le nouveau nombre de likes
                resolve({ success: true, likes_count: 10 });
            }, 300);
        });
    },
    
    // Annuler un like sur un événement
    unlikeEvent: function(eventId) {
        console.log(`API: Unlike de l'événement #${eventId}`);
        return new Promise(resolve => {
            setTimeout(() => {
                // La réponse contiendrait normalement le nouveau nombre de likes
                resolve({ success: true, likes_count: 9 });
            }, 300);
        });
    },
    
    // Ajouter un commentaire
    addComment: function(eventId, commentData) {
        console.log(`API: Ajout d'un commentaire à l'événement #${eventId}`, commentData);
        return new Promise(resolve => {
            setTimeout(() => {
                resolve({ success: true });
            }, 300);
        });
    },
    
    // Réserver des places pour un événement
    registerForEvent: function(eventId, registrationData) {
        console.log(`API: Réservation pour l'événement #${eventId}`, registrationData);
        return new Promise(resolve => {
            setTimeout(() => {
                resolve({ success: true });
            }, 300);
        });
    },
    
    // Créer un nouvel événement
    createEvent: function(eventData) {
        console.log('API: Création d\'un nouvel événement', eventData);
        return new Promise(resolve => {
            setTimeout(() => {
                resolve({ success: true, event_id: 123 });
            }, 300);
        });
    }
};

// Fonctions d'authentification simulées (à remplacer)
const AuthAPI = {
    // Vérifier si l'utilisateur est connecté
    isAuthenticated: function() {
        return false; // Simuler un utilisateur non connecté
    },
    
    // Connexion
    login: function(credentials) {
        console.log('API: Tentative de connexion', credentials);
        return new Promise(resolve => {
            setTimeout(() => {
                resolve({ success: true });
            }, 300);
        });
    },
    
    // Inscription
    register: function(userData) {
        console.log('API: Inscription d\'un nouvel utilisateur', userData);
        return new Promise(resolve => {
            setTimeout(() => {
                resolve({ success: true });
            }, 300);
        });
    },
    
    // Déconnexion
    logout: function() {
        console.log('API: Déconnexion');
        return new Promise(resolve => {
            setTimeout(() => {
                resolve({ success: true });
            }, 300);
        });
    }
};

// Exporter les API pour utilisation dans d'autres scripts
window.EventAPI = EventAPI;
window.AuthAPI = AuthAPI;
