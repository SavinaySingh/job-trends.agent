from django.urls import path
from . import views

urlpatterns = [
    path("", views.chat_page, name="chat_page"),  # Ensure this matches
    path("ask/", views.main_processor, name="main_processor"),
]
