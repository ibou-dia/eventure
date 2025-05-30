from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/<str:event_id>/',views.reservation,name='reservations'),
    path('payment/<str:event_id>/', views.payment, name='payment'),

    path('event/create/', views.create_event, name='create_event'),
    path('event/<str:event_id>/edit/', views.edit_event, name='edit_event'),
    path('event/<str:event_id>/delete/', views.delete_event, name='delete_event'),
    path('event/<str:event_id>/', views.event_detail, name='event_detail'),
    path('event/<str:event_id>/register/', views.register_for_event, name='register_for_event'),
    path('event/<str:event_id>/comment/', views.add_comment, name='add_comment'),
    path('comment/<str:event_id>/<int:comment_index>/delete/', views.delete_comment, name='delete_comment'),
    path('booking/<str:event_id>/confirmation/', views.booking_confirmation, name='booking_confirmation'),
    path('booking/<str:event_id>/cancel/', views.cancel_booking, name='cancel_booking'),
    path('booking/<str:event_id>/ticket/', views.view_ticket, name='view_ticket'),
    path('api/events/', views.events_paginated_api, name='events_paginated_api'),
    path('like/', views.toggle_like, name='toggle_like'),
    path('event/<str:event_id>/send/', views.send_invitations, name='send_invitations'),
    path('event/<str:event_id>/inviter/', views.invitation, name='invitation'),
    
    # URLs pour la réinitialisation de mot de passe
    path('password_reset/', views.password_reset_view, name='password_reset'),
    path('password_reset/done/', views.password_reset_done_view, name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.password_reset_confirm_view, name='password_reset_confirm'),
    path('reset/done/', views.password_reset_complete_view, name='password_reset_complete'),
]
