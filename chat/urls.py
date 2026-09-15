from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.chat_home, name='index'),

    path('send/', views.send_message_api, name='send_message'),

    path('messages/', views.get_new_messages_api, name='get_messages'),

    path(
        'delete-for-me/<int:message_id>/',
        views.delete_for_me,
        name='delete_for_me'
    ),

    path(
        'delete-for-everyone/<int:message_id>/',
        views.delete_for_everyone,
        name='delete_for_everyone'
    ),

    path(
    'delete-user-permanently/<int:user_id>/',
    views.delete_user_permanently,
    name='delete_user_permanently'
    ),
]