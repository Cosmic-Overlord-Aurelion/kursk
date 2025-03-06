from django.contrib import admin
from .models import (
    User, Friendship, Message, News, NewsPhoto,
    Event, EventRegistration,
    Place, PlaceRating,
    Comment
)

class NewsPhotoInline(admin.TabularInline):
    """
    Позволяет загружать сразу несколько фото к новости в админке.
    """
    model = NewsPhoto
    extra = 5

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    """
    Классическая админка для News с инлайн-фото
    """
    inlines = [NewsPhotoInline]
    # Добавляем 'likes', если это поле есть в модели News
    list_display = ('id', 'title', 'created_at', 'views_count', 'likes')
    search_fields = ('title', 'content')
    ordering = ('-created_at',)

@admin.register(NewsPhoto)
class NewsPhotoAdmin(admin.ModelAdmin):
    """
    Админка для просмотра и поиска по фото
    """
    list_display = ('id', 'news', 'uploaded_at')
    search_fields = ('news__title',)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """
    Админка для комментариев.
    list_display и search_fields можно настроить под свои нужды.
    """
    list_display = (
        'id', 'user', 'entity_type', 'entity_id',
        'parent_comment_id', 'content', 'created_at'
    )
    search_fields = ('content', 'user__username')
    list_filter = ('entity_type',)

# Остальные модели
admin.site.register(User)
admin.site.register(Friendship)
admin.site.register(Message)
admin.site.register(Event)
admin.site.register(EventRegistration)
admin.site.register(Place)
admin.site.register(PlaceRating)
