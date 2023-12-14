from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('my_rentals/', views.my_rentals, name='my_rentals'),

    path('movies/', views.movies_search, name='movies'),
    path('movies/search/', views.movies_search, name='movies'),

    path('movie/<str:slug>/', views.movie, name='movie'),
    path('movie/<str:slug>/edit/', views.movie_edit, name='movie_edit'),
    path('movie-add/', views.movie_add, name='movie_add'),
    path('movie-action/<str:action>', views.movie_edited, name='movie_edited'),
    path('movie-action/<str:action>/<str:slug>', views.movie_edited, name='movie_edited'),
    path('movie/<str:slug>/delete/', views.movie_delete, name='movie_delete'),
    path('movie/<str:slug>/deleted', views.movie_deleted, name='movie_deleted'),

    path('rent/<str:slug>', views.rent, name='rent'),
    path('rentals/', views.rentals, name='rentals'),
    path('rentals/search/', views.rentals, name='rentals'),
    path('return/<str:slug>', views.return_movie, name='return_movie'),
    path('return_admin/<str:slug>', views.return_movie, name='return_admin_movie'),
    path('returned/<str:slug>/', views.returned_movie, name='returned_movie'),
    path('rent_admin/<str:slug>', views.rent_admin, name="rent_admin"),

    path('clients/', views.clients_search, name='clients_search'),
    path('clients/search', views.clients_search, name='clients_search'),
    path('client/<str:username>', views.client, name='client'),
    path('client-add/', views.client_add, name='client_add'),
    path('client-action/<str:action>', views.client_edited, name='client_edited'),
    path('client-action/<str:action>/<str:username>', views.client_edited, name='client_edited'),
    path('client/<str:username>/edit/', views.client_edit, name='client_edit'),
    path('client/<str:username>/delete/', views.client_delete, name='client_delete'),
    path('client/<str:username>/deleted', views.client_deleted, name='client_deleted')    
]