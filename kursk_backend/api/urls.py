from django.urls import path
from .views import (
    register_user, list_users, user_detail, update_user_avatar,
    news_list, create_news, news_detail, list_friendships,
    add_friend, accept_friend, remove_friend, list_messages,
    send_message, get_messages_between, list_events, create_event,
    register_for_event, list_places, create_place, rate_place,
    approve_place, create_comment, list_comments, list_news_photos,
    add_news_photos, list_notifications, mark_notification_read,
    list_user_activity, add_user_activity, verify_email, login_user,
    request_password_reset, confirm_password_reset, check_user_exists,
    add_like, add_view, delete_comment, update_comment, toggle_comment_like,
    get_latest_comment, event_detail, add_event_photos, delete_event, update_event_preview, my_events
)

urlpatterns = [
    path('register/', register_user, name='register_user'),
    path('users/', list_users, name='list_users'),
    path('users/<int:pk>/', user_detail, name='user_detail'),
    path('users/<int:pk>/avatar/', update_user_avatar, name='update_user_avatar'),

    path('news/', news_list, name='news_list'),
    path('news/create/', create_news, name='create_news'),
    path('news/<int:pk>/', news_detail, name='news_detail'),
    path('news/<int:pk>/photos/', list_news_photos, name='list_news_photos'),
    path('news/<int:pk>/photos/add/', add_news_photos, name='add_news_photos'),
    path('news/<int:pk>/like/', add_like, name='add_like'),
    path('news/<int:pk>/add_view/', add_view, name='add_view'),

    # Друзья
    path('friendships/', list_friendships, name='list_friendships'),
    path('friendships/add/', add_friend, name='add_friend'),
    path('friendships/accept/', accept_friend, name='accept_friend'),
    path('friendships/remove/', remove_friend, name='remove_friend'),

    # Сообщения
    path('messages/', list_messages, name='list_messages'),
    path('messages/send/', send_message, name='send_message'),
    path('messages/between/<int:user1>/<int:user2>/', get_messages_between, name='get_messages_between'),

    # События
    path('events/', list_events, name='list_events'),
    path('events/create/', create_event, name='create_event'),
    path('events/<int:pk>/register/', register_for_event, name='register_for_event'),
    path('events/<int:pk>/', event_detail, name='event_detail'),  # Оставляем для GET
    path('events/<int:pk>/delete/', delete_event, name='delete_event'),  # Новый путь для DELETE
    path('events/<int:pk>/photos/add/', add_event_photos, name='add_event_photos'),
    path('events/<int:pk>/update_preview/', update_event_preview, name='update_event_preview'),
    path('events/my_events/', my_events, name='my_events'),

    # Места
    path('places/', list_places, name='list_places'),
    path('places/create/', create_place, name='create_place'),
    path('places/rate/', rate_place, name='rate_place'),
    path('places/<int:pk>/approve/', approve_place, name='approve_place'),

    # Комментарии
    path('comments/', list_comments, name='list_comments'),
    path('comments/create/', create_comment, name='create_comment'),
    path('comments/<int:comment_id>/delete/', delete_comment, name='delete_comment'),
    path('comments/<int:comment_id>/update/', update_comment, name='update_comment'),
    path('comments/<int:comment_id>/like_toggle/', toggle_comment_like, name='toggle_comment_like'),
    path('comments/latest/<int:news_id>/', get_latest_comment, name='get_latest_comment'),

    # Уведомления
    path('notifications/', list_notifications, name='list_notifications'),
    path('notifications/mark_read/', mark_notification_read, name='mark_notification_read'),


    # Активность пользователя
    path('activity/', list_user_activity, name='list_user_activity'),
    path('activity/add/', add_user_activity, name='add_user_activity'),

    # Аутентификация
    path('verify_email/', verify_email, name='verify_email'),
    path('login/', login_user, name='login_user'),
    path('check_user_exists/', check_user_exists, name='check_user_exists'),
    path('password-reset/', request_password_reset, name='request_password_reset'),
    path('password-reset/confirm/', confirm_password_reset, name='confirm_password_reset'),
]