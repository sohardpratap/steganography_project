from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('encrypt/', views.encrypt, name='encrypt'),  # Encrypt page
    path('decrypt/', views.decrypt, name='decrypt'),  # Decrypt page
    path('learn/', views.learn, name='learn'),  # Learn page
]
