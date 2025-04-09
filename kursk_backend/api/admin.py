from django.contrib import admin
from django.core.mail import send_mail
from django.conf import settings

from .models import (
    User,
    Friendship,
    Message,
    News,
    NewsPhoto,
    Event,
    EventRegistration,
    EventPhoto,
    Place,
    PlaceRating,
    Comment,
    Notification,
    Moderator,  # Добавляем Moderator
)

from .tasks import send_email_task, send_push_notification_task
from .services import notify_user, send_event_email


# Inline для загрузки нескольких фото к новости
class NewsPhotoInline(admin.TabularInline):
    """
    Позволяет загружать сразу несколько фото к новости в админке.
    """

    model = NewsPhoto
    extra = 5


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    inlines = [NewsPhotoInline]
    list_display = (
        "id",
        "title",
        "subheader",
        "created_at",
        "views_count",
        "likes_count",
    )
    search_fields = ("title", "subheader", "full_text")
    ordering = ("-created_at",)

    def likes_count(self, obj):
        return obj.likes.count()

    likes_count.short_description = "Лайки"


@admin.register(NewsPhoto)
class NewsPhotoAdmin(admin.ModelAdmin):
    list_display = ("id", "news", "uploaded_at")
    search_fields = ("news__title",)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """
    Админка для комментариев.
    """

    list_display = (
        "id",
        "user",
        "get_content_type",
        "object_id",
        "get_parent_comment_id",
        "content",
        "created_at",
    )
    search_fields = ("content", "user__username")
    list_filter = ("content_type",)

    def get_content_type(self, obj):
        return obj.content_type.model if obj.content_type else None

    get_content_type.short_description = "Content Type"

    def get_parent_comment_id(self, obj):
        return obj.parent_comment.id if obj.parent_comment else None

    get_parent_comment_id.short_description = "Parent Comment ID"


# Регистрируем модели без кастомизации
admin.site.register(User)
admin.site.register(Friendship)
admin.site.register(Message)
admin.site.register(Place)
admin.site.register(PlaceRating)


# Добавляем админку для Moderator
@admin.register(Moderator)
class ModeratorAdmin(admin.ModelAdmin):
    list_display = ("email", "status")
    fields = ("email", "status")
    list_filter = ("status",)


def approve_events(modeladmin, request, queryset):
    for event in queryset:
        if event.status != "approved":
            event.status = "approved"
            event.save()

            send_event_email(
                user=event.organizer,
                subject="Мероприятие одобрено",
                body=f"Поздравляем! Ваше мероприятие '{event.title}' было одобрено.",
            )

            notify_user(
                user=event.organizer,
                notif_type="event_approved",
                message=f"Ваше мероприятие «{event.title}» было одобрено администрацией!",
                entity_type="event",
                entity_id=event.id,
                title="Мероприятие одобрено",
                body=f"Ваше мероприятие «{event.title}» одобрено и теперь доступно другим пользователям!",
                data={"event_id": str(event.id), "type": "event_approved"},
            )

    modeladmin.message_user(request, "Выбранные мероприятия были одобрены.")


def reject_events(modeladmin, request, queryset):
    for event in queryset:
        if event.status != "rejected":
            event.status = "rejected"
            event.save()

            send_event_email(
                user=event.organizer,
                subject="Мероприятие отклонено",
                body=f"К сожалению, ваше мероприятие '{event.title}' было отклонено.",
            )

            notify_user(
                user=event.organizer,
                notif_type="event_rejected",
                message=f"К сожалению, ваше мероприятие «{event.title}» было отклонено администрацией.",
                entity_type="event",
                entity_id=event.id,
                title="Мероприятие отклонено",
                body=f"Мероприятие «{event.title}» было отклонено. Проверьте требования и попробуйте снова.",
                data={"event_id": str(event.id), "type": "event_rejected"},
            )

    modeladmin.message_user(request, "Выбранные мероприятия были отклонены.")


# Inline для загрузки нескольких фото к событию
class EventPhotoInline(admin.TabularInline):
    """
    Позволяет загружать сразу несколько фото к событию в админке.
    """

    model = EventPhoto
    extra = 5


# Обновлённый класс EventAdmin
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "organizer", "status", "created_at", "max_participants")
    list_filter = ("status", "created_at")
    search_fields = ("title", "description")
    actions = [approve_events, reject_events]
    inlines = [EventPhotoInline]
    readonly_fields = ("created_at", "updated_at", "views_count")

    fieldsets = (
        (None, {"fields": ("title", "subheader", "description", "organizer", "image")}),
        (
            "Детали мероприятия",
            {
                "fields": (
                    "start_datetime",
                    "end_datetime",
                    "address",
                    "latitude",
                    "longitude",
                )
            },
        ),
        ("Статус и лимиты", {"fields": ("status", "max_participants")}),
    )


admin.site.register(EventRegistration)
