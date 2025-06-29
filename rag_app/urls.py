from django.urls import path
from . import views
from .views import upload_file, log_feedback

urlpatterns = [
    path("", views.chat_page, name="chat_page"),
    path("upload/", upload_file, name="upload_file"),
    path("log_feedback/", log_feedback, name="log_feedback"),
]
