from django.core.mail import send_mail
from django.conf import settings
from .models import Notification
from .tasks import send_email_task, send_push_notification_task


def notify_user(user, notif_type, message, entity_type=None, entity_id=None, title=None, body=None, data=None):
    """
    Создаёт внутриприложенное уведомление и, при наличии title/body, отправляет push.
    :param user: пользователь
    :param notif_type: тип уведомления (event_joined, event_rejected и т.д.)
    :param message: сообщение, которое будет сохранено в базе
    :param entity_type: тип сущности (например, 'event')
    :param entity_id: ID сущности (например, ID мероприятия)
    :param title: заголовок push-уведомления
    :param body: тело push-уведомления
    :param data: словарь с дополнительными данными (например, {'event_id': '5', 'type': 'event_joined'})
    """
    Notification.objects.create(
        user=user,
        type=notif_type,
        message=message,
        entity_type=entity_type,
        entity_id=entity_id,
    )

    if title and body:
        send_push_notification_task.delay(
            user_id=user.id,
            notif_type=notif_type,
            title=title,
            body=body,
            data=data
        )


def send_event_email(user, subject, body):
    """
    Асинхронная отправка email пользователю.
    """
    send_email_task.delay(
        subject=subject,
        body=body,
        recipient_email=user.email
    )
