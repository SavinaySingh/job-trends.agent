from django.urls import path
from .views.chat_page import chat_page
from .views.upload_file import upload_file
from .views.log_feedback import log_feedback


urlpatterns = [
    path("", chat_page, name="chat_page"),
    path("upload/", upload_file, name="upload_file"),
    path("log_feedback/", log_feedback, name="log_feedback"),
]
