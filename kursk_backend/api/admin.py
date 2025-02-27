from django.contrib import admin
from .models import (
    User, Friendship, Message, News, NewsPhoto,
    Event, EventRegistration,
    Place, PlaceRating,
    Comment
)

class NewsPhotoInline(admin.TabularInline):  
    model = NewsPhoto
    extra = 5  

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    inlines = [NewsPhotoInline]
    list_display = ('id', 'title', 'created_at', 'views_count')
    search_fields = ('title', 'content')
    ordering = ('-created_at',)

@admin.register(NewsPhoto)
class NewsPhotoAdmin(admin.ModelAdmin):
    list_display = ('id', 'news', 'uploaded_at')
    search_fields = ('news__title',)

admin.site.register(User)
admin.site.register(Friendship)
admin.site.register(Message)
admin.site.register(Event)
admin.site.register(EventRegistration)
admin.site.register(Place)
admin.site.register(PlaceRating)
admin.site.register(Comment)

