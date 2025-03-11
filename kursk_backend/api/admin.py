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
    inlines = [NewsPhotoInline]
    list_display = ('id', 'title', 'subheader', 'created_at', 'views_count', 'likes')
    search_fields = ('title', 'subheader', 'full_text')
    ordering = ('-created_at',)


@admin.register(NewsPhoto)
class NewsPhotoAdmin(admin.ModelAdmin):
    list_display = ('id', 'news', 'uploaded_at')
    search_fields = ('news__title',)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """
    Админка для комментариев.
    list_display и search_fields можно настроить под свои нужды.
    """
    list_display = (
        'id', 'user', 'get_content_type', 'object_id',
        'get_parent_comment_id', 'content', 'created_at'
    )
    search_fields = ('content', 'user__username')
    list_filter = ('content_type',)

    def get_content_type(self, obj):
        return obj.content_type.model if obj.content_type else None
    get_content_type.short_description = "Content Type"

    def get_parent_comment_id(self, obj):
        return obj.parent_comment.id if obj.parent_comment else None
    get_parent_comment_id.short_description = "Parent Comment ID"

admin.site.register(User)
admin.site.register(Friendship)
admin.site.register(Message)
admin.site.register(Event)
admin.site.register(EventRegistration)
admin.site.register(Place)
admin.site.register(PlaceRating)
