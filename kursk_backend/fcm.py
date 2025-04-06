import firebase_admin
from firebase_admin import credentials, messaging

# Инициализация Firebase (только один раз)
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase-credentials.json")
    firebase_admin.initialize_app(cred)

def send_push_notification(token: str, title: str, body: str):
    """
    Отправка push-уведомления одному получателю.
    :param token: FCM-токен устройства
    :param title: Заголовок уведомления
    :param body: Текст уведомления
    """
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token=token,
    )
    try:
        response = messaging.send(message)
        print(f"✅ Успешно отправлено: {response}")
        return response
    except Exception as e:
        print(f"❌ Ошибка при отправке: {e}")
        return None
