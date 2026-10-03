from django.urls import path

from .views import chat, process_file
urlpatterns = [
    path(
        "chat/",
        chat,
        name="aidy_chat"
    ),

    path(
        "file/",
        process_file,
        name="aidy_process_file"
    ),
]