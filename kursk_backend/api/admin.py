from django.contrib import admin
from .models import (
    User, Friendship, Message, News,
    Event, EventRegistration,
    Place, PlaceRating,
    Comment
)

admin.site.register(User)
admin.site.register(Friendship)
admin.site.register(Message)
admin.site.register(News)
# admin.site.register(NewsPhoto)         # Раскомментируйте, если есть модель
admin.site.register(Event)
admin.site.register(EventRegistration)
admin.site.register(Place)
admin.site.register(PlaceRating)
admin.site.register(Comment)
# admin.site.register(Notification)      # Раскомментируйте, если есть модель
# admin.site.register(UserActivity)      # Раскомментируйте, если есть модель
