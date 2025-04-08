from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from fcm import send_push_if_allowed
from api.models import User, Notification, EventRegistration, Event, Message

@shared_task
def send_email_task(subject, body, recipient_email):
    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient_email],
        fail_silently=True,
    )

@shared_task
def notify_message_receiver(message_id):
    try:
        message = Message.objects.get(id=message_id)
        # Email-уведомление
        send_email_task.delay(
            subject=f"Новое сообщение от {message.from_user.username}",
            body=message.content,
            recipient_email=message.to_user.email
        )
        # Push-уведомление
        send_push_notification_task.delay(
            user_id=message.to_user.id,
            notif_type='new_message',
            title=f"Новое сообщение от {message.from_user.username}",
            body=message.content[:100],
            data={
                'type': 'new_message',
                'sender_id': str(message.from_user.id)  # Убедимся, что это строка
            }
        )
        # Создаем запись в Notification
        Notification.objects.create(
            user=message.to_user,
            type='new_message',
            message=f"Новое сообщение от {message.from_user.username}",
            entity_type='user',
            entity_id=message.from_user.id,
            created_at=timezone.now()
        )
    except Message.DoesNotExist:
        print(f"[notify_message_receiver] Ошибка: сообщение с ID {message_id} не найдено")
    except Exception as e:
        print(f"[notify_message_receiver] Неизвестная ошибка для сообщения {message_id}: {str(e)}")

@shared_task
def send_push_notification_task(user_id, notif_type, title, body, data=None):
    try:
        user = User.objects.get(id=user_id)
        if not data:
            data = {}
        # Логируем отправку для отладки
        print(f"[send_push_notification_task] Отправка push для user_id={user_id}, type={notif_type}, data={data}")
        send_push_if_allowed(
            user=user,
            notif_type=notif_type,
            title=title,
            body=body,
            data=data
        )
    except User.DoesNotExist:
        print(f"[send_push_notification_task] Ошибка: пользователь с ID {user_id} не найден")
    except Exception as e:
        print(f"[send_push_notification_task] Неизвестная ошибка для user_id={user_id}: {str(e)}")

@shared_task
def delete_old_notifications():
    threshold = timezone.now() - timedelta(days=30)
    deleted, _ = Notification.objects.filter(created_at__lt=threshold).delete()
    print(f"[delete_old_notifications] Удалено уведомлений: {deleted}")

@shared_task
def delete_expired_registrations():
    now = timezone.now()
    expired_events = Event.objects.filter(start_datetime__lt=now).values_list('id', flat=True)
    deleted, _ = EventRegistration.objects.filter(event_id__in=expired_events).delete()
    print(f"[delete_expired_registrations] Удалено регистраций: {deleted}")

@shared_task
def complete_past_events():
    now = timezone.now()
    updated = Event.objects.filter(
        start_datetime__lt=now,
        status='approved'
    ).update(status='completed')
    print(f"[complete_past_events] Автоматически завершено событий: {updated}")

@shared_task
def send_event_reminders():
    tomorrow = timezone.now() + timedelta(days=1)
    start = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)

    registrations = EventRegistration.objects.filter(
        event__start_datetime__range=(start, end)
    ).select_related('event', 'user')

    for reg in registrations:
        event = reg.event
        user = reg.user
        title = "Напоминание о мероприятии"
        body = f"Уже завтра вы участвуете в мероприятии «{event.title}»!"

        # PUSH
        send_push_notification_task.delay(
            user_id=user.id,
            notif_type='event_reminder',
            title=title,
            body=body,
            data={
                'event_id': str(event.id),
                'type': 'event_reminder'
            }
        )

        # EMAIL
        send_email_task.delay(
            subject=title,
            body=f"Напоминаем, что завтра вы участвуете в мероприятии «{event.title}», которое начнётся {event.start_datetime.strftime('%d.%m.%Y %H:%M')}",
            recipient_email=user.email
        )

    print(f"[send_event_reminders] Отправлены напоминания для {registrations.count()} регистраций.")