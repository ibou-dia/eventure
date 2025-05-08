// Script pour la barre de recherche et les filtres

document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('search-input');
    const searchBar = document.querySelector('.search-bar');
    const filterOptions = document.querySelectorAll('.filter-group select');
    const filterTags = document.querySelector('.filter-tags');
    
    // Animation d'entrée des éléments
    gsap.from('.events-filter', {
        y: 30,
        opacity: 0,
        duration: 0.8,
        ease: 'power3.out'
    });
    
    // Focus effect pour la barre de recherche
    if (searchInput) {
        searchInput.addEventListener('focus', function() {
            searchBar.classList.add('active');
        });
        
        searchInput.addEventListener('blur', function() {
            if (this.value.length === 0) {
                searchBar.classList.remove('active');
            }
        });
        
        // Suggestions de recherche avec un petit délai
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value.trim().toLowerCase();
            
            searchTimeout = setTimeout(() => {
                if (query.length > 2) {
                    // Ici on pourrait appeler une API pour obtenir des suggestions
                    console.log('Recherche en cours pour:', query);
                    
                    // Animation du bouton de recherche
                    const searchButton = searchBar.querySelector('button');
                    gsap.to(searchButton, {
                        scale: 1.05,
                        duration: 0.3,
                        yoyo: true,
                        repeat: 1
                    });
                }
            }, 300);
        });
    }
    
    // Gestion des filtres
    if (filterOptions.length > 0) {
        filterOptions.forEach(select => {
            select.addEventListener('change', function() {
                const value = this.value;
                const text = this.options[this.selectedIndex].text;
                const type = this.parentElement.querySelector('i').className.split(' ')[1];
                
                if (value) {
                    // Vérifier si le tag existe déjà
                    const existingTag = document.querySelector(`.filter-tag[data-value="${value}"]`);
                    
                    if (!existingTag) {
                        // Créer un nouveau tag
                        const tag = document.createElement('div');
                        tag.className = 'filter-tag';
                        tag.dataset.value = value;
                        tag.innerHTML = `${text} <i class="fas fa-times"></i>`;
                        
                        // Animation d'entrée
                        tag.style.opacity = '0';
                        tag.style.transform = 'translateY(10px)';
                        
                        // Ajouter le tag au conteneur
                        filterTags.appendChild(tag);
                        
                        // Animation
                        setTimeout(() => {
                            tag.style.opacity = '1';
                            tag.style.transform = 'translateY(0)';
                        }, 10);
                        
                        // Ajouter un événement pour supprimer le tag
                        tag.querySelector('i').addEventListener('click', function(e) {
                            e.stopPropagation();
                            
                            // Animation de sortie
                            tag.style.opacity = '0';
                            tag.style.transform = 'translateY(-10px)';
                            
                            // Supprimer le tag après l'animation
                            setTimeout(() => {
                                tag.remove();
                                
                                // Réinitialiser le select
                                const selects = document.querySelectorAll('.filter-group select');
                                selects.forEach(s => {
                                    if (s.value === value) {
                                        s.value = '';
                                        // Animation du select
                                        gsap.from(s, {
                                            x: 5,
                                            duration: 0.3,
                                            ease: 'power2.out'
                                        });
                                    }
                                });
                            }, 300);
                        });
                    }
                }
            });
        });
        
        // Gestion des clics sur les tags existants
        document.addEventListener('click', function(e) {
            if (e.target.closest('.filter-tag')) {
                const tag = e.target.closest('.filter-tag');
                
                // Si on clique sur le x, on ne fait rien car c'est géré ailleurs
                if (e.target.tagName === 'I') return;
                
                // Animation du tag
                gsap.to(tag, {
                    scale: 1.1,
                    duration: 0.2,
                    yoyo: true,
                    repeat: 1
                });
            }
        });
    }
    
    // Gestion du bouton de recherche
    const searchButton = document.querySelector('.search-bar button');
    if (searchButton) {
        searchButton.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Animation du bouton au clic
            gsap.to(this, {
                scale: 0.95,
                duration: 0.1,
                onComplete: () => {
                    gsap.to(this, {
                        scale: 1,
                        duration: 0.2
                    });
                }
            });
            
            // Ici on pourrait soumettre la recherche
            const query = searchInput.value.trim();
            if (query) {
                console.log('Recherche soumise pour:', query);
                
                // Collection de tous les filtres actifs
                const activeTags = document.querySelectorAll('.filter-tag:not(.active)');
                const filters = Array.from(activeTags).map(tag => tag.dataset.value);
                
                console.log('Filtres actifs:', filters);
                
                // Simuler une recherche
                simulateSearch(query, filters);
            }
        });
    }
    
    // Fonction pour simuler une recherche (à des fins de démonstration)
    function simulateSearch(query, filters) {
        // Trouver la grille d'événements
        const eventsGrid = document.querySelector('.events-grid');
        
        if (eventsGrid) {
            // Animation de chargement
            gsap.to(eventsGrid, {
                opacity: 0.5,
                duration: 0.3
            });
            
            // Ajouter un indicateur de chargement
            const loader = document.createElement('div');
            loader.className = 'search-loader';
            loader.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Recherche en cours...';
            loader.style.position = 'absolute';
            loader.style.top = '50%';
            loader.style.left = '50%';
            loader.style.transform = 'translate(-50%, -50%)';
            loader.style.backgroundColor = 'rgba(255, 255, 255, 0.9)';
            loader.style.padding = '15px 25px';
            loader.style.borderRadius = '30px';
            loader.style.boxShadow = 'var(--box-shadow)';
            loader.style.zIndex = '10';
            loader.style.opacity = '0';
            
            eventsGrid.style.position = 'relative';
            eventsGrid.appendChild(loader);
            
            // Afficher le loader
            gsap.to(loader, {
                opacity: 1,
                duration: 0.3
            });
            
            // Simuler un délai de recherche
            setTimeout(() => {
                // Masquer le loader
                gsap.to(loader, {
                    opacity: 0,
                    duration: 0.3,
                    onComplete: () => {
                        loader.remove();
                    }
                });
                
                // Restaurer l'opacité de la grille
                gsap.to(eventsGrid, {
                    opacity: 1,
                    duration: 0.5
                });
                
                // Animer les cartes d'événements comme si elles étaient filtrées
                const eventCards = eventsGrid.querySelectorAll('.event-card');
                
                eventCards.forEach((card, index) => {
                    // Animation des cartes avec un délai croissant
                    gsap.from(card, {
                        y: 20,
                        opacity: 0,
                        duration: 0.4,
                        delay: index * 0.1,
                        ease: 'back.out(1.2)'
                    });
                });
                
                // Mettre à jour le titre de la section
                const sectionTitle = document.querySelector('.section-title');
                if (sectionTitle) {
                    sectionTitle.textContent = `Résultats pour "${query}"`;
                    gsap.from(sectionTitle, {
                        y: -10,
                        opacity: 0,
                        duration: 0.5
                    });
                }
            }, 1500);
        }
    }
});
