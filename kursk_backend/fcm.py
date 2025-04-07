import firebase_admin
from firebase_admin import credentials, messaging
from django.contrib.auth.models import User
from api.models import FCMToken, PushNotificationSetting
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import Serializer, CharField
import logging

logger = logging.getLogger(__name__)

# Инициализация Firebase (один раз)
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase-credentials.json")
    firebase_admin.initialize_app(cred)


def send_push_notification(token: str, title: str, body: str, data: dict = None):
    """
    Отправка push-уведомления одному получателю.
    :param token: FCM-токен устройства
    :param title: Заголовок уведомления
    :param body: Текст уведомления
    :param data: Доп. данные (например, event_id)
    """
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token=token,
        data=data or {}  # Всегда словарь, даже если пустой
    )
    try:
        response = messaging.send(message)
        logger.info(f"✅ Успешно отправлено: {response}")
        return response
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке: {e}")
        return None


def send_push_if_allowed(user: User, notif_type: str, title: str, body: str, data: dict = None):
    # Карта сопоставления типа уведомления с категорией
    category_map = {
        'event_joined': 'events',
        'event_left': 'events',
        'event_comment': 'events',
        'event_comment_reply': 'events',
        'event_submitted': 'moderation',
        'event_approved': 'moderation',
        'event_rejected': 'moderation',
        'comment_liked': 'likes_comments',
        'event_reminder': 'events',
    }

    category = category_map.get(notif_type)
    if not category:
        logger.warning(f"⚠️ Тип уведомления '{notif_type}' не сопоставлен с категорией.")
        return

    settings = getattr(user, 'push_settings', None)
    if settings is None or not getattr(settings, category, False):
        logger.info(f"🔕 Push отключён для категории '{category}' у пользователя {user.username}")
        return

    token_obj = FCMToken.objects.filter(user=user).last()
    if not token_obj:
        logger.warning(f"⚠️ У пользователя {user.username} нет FCM-токена.")
        return

    try:
        response = send_push_notification(token_obj.token, title, body, data)
        logger.info(f"✅ Уведомление отправлено пользователю {user.username}: {response}")
        return response
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке push-уведомления пользователю {user.username}: {e}")
        return None


# Сериализатор для FCM-токена
class FcmTokenSerializer(Serializer):
    token = CharField(max_length=255)

# API для регистрации FCM-токена
class RegisterFcmTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = FcmTokenSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"⚠️ Неверные данные для FCM-токена: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        token = serializer.validated_data['token']
        user = request.user

        try:
            # Проверяем, существует ли токен
            fcm_token, created = FCMToken.objects.get_or_create(token=token)
            if not created:
                # Если токен существует, обновляем пользователя
                if fcm_token.user != user:
                    old_user = fcm_token.user
                    fcm_token.user = user
                    fcm_token.save()
                    logger.info(f"ℹ️ Токен {token} перепривязан от {old_user.username if old_user else 'никого'} к {user.username}")
                    return Response(
                        {"message": "Token reassigned to current user"},
                        status=status.HTTP_200_OK
                    )
                logger.info(f"ℹ️ Токен {token} уже зарегистрирован для {user.username}")
                return Response(
                    {"message": "Token already registered for this user"},
                    status=status.HTTP_200_OK
                )
            # Если токен новый, привязываем к пользователю
            fcm_token.user = user
            fcm_token.save()
            logger.info(f"✅ Токен {token} зарегистрирован для {user.username}")
            return Response(
                {"message": "Token registered successfully"},
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"❌ Ошибка при регистрации токена {token} для {user.username}: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )