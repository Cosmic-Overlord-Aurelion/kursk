from django.urls import path
from .views import (

    register_user, list_users, user_detail,

    news_list, create_news, news_detail,

    list_friendships, add_friend, accept_friend, remove_friend,

    list_messages, send_message, get_messages_between,
 
    list_events, create_event, register_for_event,

    list_places, create_place, rate_place,

    create_comment, list_comments,
)

urlpatterns = [
    path('register', register_user, name='register_user'),
    path('users', list_users, name='list_users'),
    path('users/<int:pk>', user_detail, name='user_detail'),

    path('news', news_list, name='news_list'),
    path('news/create', create_news, name='create_news'),
    path('news/<int:pk>', news_detail, name='news_detail'),

    path('friendships', list_friendships, name='list_friendships'),
    path('friendships/add', add_friend, name='add_friend'),
    path('friendships/accept', accept_friend, name='accept_friend'),
    path('friendships/remove', remove_friend, name='remove_friend'),

    path('messages', list_messages, name='list_messages'),
    path('messages/send', send_message, name='send_message'),
    path('messages/between/<int:user1>/<int:user2>', get_messages_between, name='get_messages_between'),

    path('events', list_events, name='list_events'),
    path('events/create', create_event, name='create_event'),
    path('events/register', register_for_event, name='register_for_event'),

    path('places', list_places, name='list_places'),
    path('places/create', create_place, name='create_place'),
    path('places/rate', rate_place, name='rate_place'),

    path('comments', list_comments, name='list_comments'),
    path('comments/create', create_comment, name='create_comment'),
]
