
from django.urls import path
from .views import register_user, news_list, create_news

urlpatterns = [
    path('register', register_user, name='register_user'),  
    path('news', news_list, name='news_list'),            
    path('news/create', create_news, name='create_news'),  
]
