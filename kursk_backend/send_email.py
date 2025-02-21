import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_email(username, email, verification_code):
    SMTP_SERVER = "smtp.yandex.ru"
    SMTP_PORT = 465  # Используем SSL порт
    SENDER_EMAIL = "dylanbob0@yandex.ru"  # Твой email на Яндексе
    SENDER_PASSWORD = "qundmssnkzvpurqq"  # Пароль от твоего почтового аккаунта на Яндексе

    try:
        # Создание сообщения
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = email
        msg["Subject"] = "Подтверждение почты"

        # Тело письма
        body = f"Здравствуйте, {username}!\n\nВаш код подтверждения: {verification_code}\n\nВведите этот код в приложении, чтобы завершить регистрацию."
        msg.attach(MIMEText(body, "plain", "utf-8"))

        # Подключение к SMTP-серверу и отправка письма
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, email, msg.as_string())
        server.quit()

        print(f"Письмо отправлено на {email}")

    except Exception as e:
        print(f"Ошибка при отправке письма: {e}")

# Пример использования:
username = "yeat"
email = "aprokopov932@gmail.com"
verification_code = "123456"
send_email(username, email, verification_code)
