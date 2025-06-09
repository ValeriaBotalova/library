from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='reg'),
    path('profile/', views.profile, name='profile'),
    path('books/', views.books, name='books'),
    path('loans/', views.my_loans, name='my_loans'),
    path('fines/', views.my_fines, name='my_fines'),
    path('guide/', views.guide, name='guide'),
    path('logout/', views.logout_view, name='logout'),
    path('reserve/<int:book_id>/', views.reserve_book, name='reserve_book'),
    path('cancel/<int:loan_id>/', views.cancel_reservation, name='cancel_reservation'),
    path('return/<int:loan_id>/', views.return_book, name='return_book'),
]
