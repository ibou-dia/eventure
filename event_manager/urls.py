from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('payment/<str:event_id>/', views.pay_view, name='payment'),

    path('event/create/', views.create_event, name='create_event'),
    path('event/<str:event_id>/edit/', views.edit_event, name='edit_event'),
    path('event/<str:event_id>/delete/', views.delete_event, name='delete_event'),
    path('event/<str:event_id>/', views.event_detail, name='event_detail'),
    path('event/<str:event_id>/register/', views.register_for_event, name='register_for_event'),
    path('event/<str:event_id>/comment/', views.add_comment, name='add_comment'),
    path('event/<str:event_id>/like/', views.like_event, name='like_event'),
    path('booking/<str:event_id>/<str:booking_id>/confirmation/', views.booking_confirmation, name='booking_confirmation'),
    path('api/events/', views.events_paginated_api, name='events_paginated_api'),
]
