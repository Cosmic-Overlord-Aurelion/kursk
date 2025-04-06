from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import send_mail
import random
import threading


from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import (
    User, Friendship, Message, News,
    NewsPhoto,          
    Event, EventRegistration,
    Place, PlaceRating,
    Comment,
    Notification,         
    UserActivity
)

from .serializers import (
    UserSerializer, FriendshipSerializer, MessageSerializer,
    NewsSerializer, NewsPhotoSerializer,
    EventSerializer, EventRegistrationSerializer,
    PlaceSerializer, PlaceRatingSerializer,
    CommentSerializer, NotificationSerializer,
    UserActivitySerializer
)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
import random
from django.utils import timezone
from django.contrib.auth.hashers import make_password
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .models import User
import logging
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Comment
from .serializers import CommentSerializer
logger = logging.getLogger(__name__)

import random
import logging
import threading
import smtplib

from django.db.models import Q, Count, F, Value, FloatField, ExpressionWrapper, Case, When
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import send_mail
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token

from .models import (
    User, Friendship, Message, News, NewsPhoto, NewsLike,
    Event, EventRegistration, Place, PlaceRating, Comment,
    Notification, UserActivity
)
from .serializers import (
    UserSerializer, FriendshipSerializer, MessageSerializer, NewsSerializer,
    NewsPhotoSerializer, EventSerializer, EventRegistrationSerializer,
    PlaceSerializer, PlaceRatingSerializer, CommentSerializer,
    NotificationSerializer, UserActivitySerializer
)

logger = logging.getLogger(__name__)

def send_verification_email(email, username, verification_code):
    """Отправка email с кодом подтверждения."""
    SMTP_SERVER = "smtp.yandex.ru"
    SMTP_PORT = 465
    SENDER_EMAIL = "dylanbob0@yandex.ru"
    SENDER_PASSWORD = "qundmssnkzvpurqq"

    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = email
        msg["Subject"] = "Подтверждение почты"

        body = (
            f"Здравствуйте, {username}!\n\n"
            f"Ваш код подтверждения: {verification_code}\n\n"
            "Введите этот код в приложении, чтобы завершить регистрацию."
        )
        msg.attach(MIMEText(body, "plain", "utf-8"))

        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, email, msg.as_string())
        server.quit()
        logger.info(f"✅ Код подтверждения успешно отправлен на {email}")
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке email: {e}")


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')

    if not username or not email or not password:
        return Response({'error': 'Не все поля заполнены'}, status=status.HTTP_400_BAD_REQUEST)

    if len(password) < 6:
        return Response({'error': 'Пароль должен содержать минимум 6 символов'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Такой username уже существует'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=email).exists():
        return Response({'error': 'Этот e-mail уже зарегистрирован'}, status=status.HTTP_400_BAD_REQUEST)

    verification_code = str(random.randint(100000, 999999))

    try:
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        user.is_email_confirmed = False
        user.email_verification_code = verification_code
        user.created_at = timezone.now()
        user.save()

        # Создаём токен сразу после регистрации
        token = Token.objects.create(user=user)

        # Отправляем код подтверждения на email (в отдельном потоке можно запустить, если нужно)
        threading.Thread(target=send_verification_email, args=(email, username, verification_code)).start()

        return Response({
            'message': 'Код подтверждения отправлен на e-mail.',
            'user_id': user.id,
            'token': token.key
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"❌ Ошибка при создании пользователя: {e}")
        return Response({'error': 'Ошибка при регистрации. Попробуйте позже.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    print("DEBUG: login_user called")
    print("DEBUG: Request headers:", dict(request.headers))
    print("DEBUG: Request data:", request.data)
    email = request.data.get('email')
    password = request.data.get('password')
    if not email or not password:
        return Response({'error': 'Не все поля заполнены'}, status=400)
    try:
        user = User.objects.get(email=email)
        if not user.is_email_confirmed:
            return Response({'error': 'Email не подтверждён'}, status=403)
        if check_password(password, user.password):
            token, created = Token.objects.get_or_create(user=user)
            print("DEBUG: Token for user", user.id, ":", token.key, "created:", created)
            return Response({
                'message': 'Успешный вход',
                'user_id': user.id,
                'token': token.key
            }, status=200)
        return Response({'error': 'Неверный пароль'}, status=400)
    except User.DoesNotExist:
        return Response({'error': 'Нет такого пользователя'}, status=404)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):
    user_id = request.data.get('user_id')
    code = request.data.get('code')

    if not user_id or not code:
        return Response({"error": "Не все поля заполнены"}, status=400)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "Пользователь не найден"}, status=404)

    if user.email_verification_code == code:
        user.is_email_confirmed = True
        user.email_verification_code = None
        user.updated_at = timezone.now()
        user.save()
        return Response({"message": "E-mail подтверждён! Теперь можно войти."}, status=200)

    return Response({"error": "Неверный код"}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_like(request, pk):
    try:
        news_obj = News.objects.get(pk=pk)
    except News.DoesNotExist:
        return Response({'error': 'Новость не найдена'}, status=404)

    user = request.user

    if news_obj.likes.filter(id=user.id).exists():

        news_obj.likes.remove(user)
        message = 'Лайк удалён'
        is_liked = False
    else:
        news_obj.likes.add(user)
        message = 'Лайк добавлен'
        is_liked = True

    likes_count = news_obj.likes.count()

    return Response({
        'message': message,
        'likes': likes_count,
        'is_liked': is_liked
    }, status=200)

@api_view(['POST'])
def add_view(request, pk):
    try:
        news_obj = News.objects.get(pk=pk)
    except News.DoesNotExist:
        return Response({'error': 'News not found'}, status=status.HTTP_404_NOT_FOUND)
    
    news_obj.views_count = F('views_count') + 1
    news_obj.save()
    news_obj.refresh_from_db()  
    
    return Response({'views_count': news_obj.views_count}, status=status.HTTP_200_OK)

@api_view(['POST'])
def confirm_password_reset(request):
    email = request.data.get('email')
    reset_code = request.data.get('reset_code')
    new_password = request.data.get('new_password')

    if not email or not reset_code or not new_password:
        return Response({'error': 'Не все поля заполнены'}, status=400)

    try:
        user = User.objects.get(email=email)

        if user.password_reset_code != reset_code:
            return Response({'error': 'Неверный код'}, status=400)

        if user.password_reset_expires < timezone.now():
            return Response({'error': 'Код истёк'}, status=400)

        user.password = make_password(new_password)
        user.password_reset_code = None
        user.password_reset_expires = None
        user.save()

        return Response({'message': 'Пароль успешно изменён'}, status=200)

    except User.DoesNotExist:
        return Response({'error': 'Нет пользователя с таким email'}, status=404)


@api_view(['PUT', 'PATCH'])
def update_user_avatar(request, pk):
    try:
        user_obj = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({'error': 'Not found'}, status=404)

    serializer = UserSerializer(user_obj, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save(updated_at=timezone.now())
        return Response(serializer.data, status=200)
    return Response(serializer.errors, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])  
def list_users(request):
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data, status=200)

from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes
)
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .serializers import UserSerializer
from django.utils import timezone
from api.authentication import CustomTokenAuthentication  # Импортируем кастомный класс

User = get_user_model()

@api_view(['GET', 'PUT', 'DELETE'])
@authentication_classes([CustomTokenAuthentication, SessionAuthentication])  # Заменяем TokenAuthentication
@permission_classes([IsAuthenticated])
def user_detail(request, pk):
    print("DEBUG: user_detail called with pk =", pk)
    print("DEBUG: Request headers:", dict(request.headers))
    print("DEBUG: Authenticated user:", request.user, "is_authenticated:", request.user.is_authenticated)
    try:
        user_obj = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({'error': 'Пользователь не найден'}, status=404)

    if request.method == 'GET':
        print("DEBUG: Handling GET for /api/users/", pk)
        return Response({
            'id': user_obj.id,
            'username': user_obj.username,
            'avatar': user_obj.avatar.url if user_obj.avatar else None
        }, status=200)

    elif request.method == 'PUT':
        print("DEBUG: Handling PUT for /api/users/", pk)
        data = request.data.copy()
        data['updated_at'] = str(timezone.now())
        ser = UserSerializer(user_obj, data=data, partial=True)
        if ser.is_valid():
            ser.save()
            return Response(ser.data, status=200)
        return Response(ser.errors, status=400)

    elif request.method == 'DELETE':
        print("DEBUG: Handling DELETE for /api/users/", pk)
        user_obj.delete()
        return Response({'message': 'Пользователь удалён'}, status=204)
from .serializers import NewsListSerializer, NewsDetailSerializer

@api_view(['GET'])
def news_list(request):
    print("DEBUG: news_list called")
    print("DEBUG: Request headers:", dict(request.headers))
    qs = News.objects.prefetch_related('photos').all()
    sort_param = request.GET.get('sort')
    
    if sort_param == 'date_asc':
        qs = qs.order_by('created_at')
    elif sort_param == 'date_desc':
        qs = qs.order_by('-created_at')
    elif sort_param == 'popular':
        qs = qs.annotate(
            comment_count=Count('comments')
        ).annotate(
            rating=ExpressionWrapper(
                F('views_count') * 0.3 + F('likes') * 1.5 + F('comment_count') * 1.0,
                output_field=FloatField()
            )
        ).order_by('-rating')
    elif sort_param == 'recommended':
        qs = qs.annotate(
            comment_count=Count('comments')
        ).annotate(
            rating=ExpressionWrapper(
                F('views_count') * 0.5 + F('likes') * 1.5 + F('comment_count') * 1.0 +
                Case(
                    When(created_at__date=timezone.now().date(), then=Value(10)),
                    default=Value(0),
                    output_field=FloatField()
                ),
                output_field=FloatField()
            )
        ).order_by('-rating')
    else:
        qs = qs.order_by('-created_at')
    
    ser = NewsListSerializer(qs, many=True)
    print("DEBUG: news_list response data:", ser.data)
    return Response(ser.data, status=200)



@api_view(['POST'])
def create_news(request):
    author_id = request.data.get('author_id')
    title = request.data.get('title')
    subheader = request.data.get('subheader')
    full_text = request.data.get('full_text')

    try:
        author = User.objects.get(id=author_id)
        if author.role != 'admin':
            return Response({'error': 'Только admin может публиковать новости'}, status=403)
    except User.DoesNotExist:
        return Response({'error': 'Пользователь не найден'}, status=404)

    data = {
        'title': title,
        'subheader': subheader,
        'full_text': full_text,
        'author': author_id,
        'created_at': timezone.now()
    }
    s = NewsDetailSerializer(data=data)
    if s.is_valid():
        news_obj = s.save(author=author)
        return Response(NewsDetailSerializer(news_obj).data, status=201)
    return Response(s.errors, status=400)


from django.contrib.contenttypes.models import ContentType

@api_view(['GET', 'PUT', 'DELETE'])
def news_detail(request, pk):
    try:
        news_obj = News.objects.get(pk=pk)
    except News.DoesNotExist:
        return Response({'error': 'Новость не найдена'}, status=404)

    if request.method == 'GET':
        ser = NewsDetailSerializer(news_obj)
        data = ser.data
        news_ct = ContentType.objects.get_for_model(News)
        comment_count = Comment.objects.filter(content_type=news_ct, object_id=news_obj.id).count()
        data['comment_count'] = comment_count
        return Response(data, status=200)

    elif request.method == 'PUT':
        ser = NewsDetailSerializer(news_obj, data=request.data, partial=True)
        if ser.is_valid():
            ser.save()
            return Response(ser.data, status=200)
        return Response(ser.errors, status=400)

    elif request.method == 'DELETE':
        news_obj.delete()
        return Response({'message': 'Новость удалена'}, status=204)




@api_view(['GET'])
def list_news_photos(request, pk):
    try:
        news_obj = News.objects.get(pk=pk)
    except News.DoesNotExist:
        return Response({'error': 'News not found'}, status=404)

    photos = NewsPhoto.objects.filter(news=news_obj)
    ser = NewsPhotoSerializer(photos, many=True)
    return Response(ser.data, status=200)


@api_view(['POST'])
def add_news_photos(request, pk):
    try:
        news_obj = News.objects.get(pk=pk)
    except News.DoesNotExist:
        return Response({'error': 'News not found'}, status=404)

    if 'photos' not in request.FILES:
        return Response({'error': 'No photo files provided'}, status=400)

    photos = request.FILES.getlist('photos')  # Получаем список файлов
    created_photos = []

    for photo_file in photos:
        new_photo = NewsPhoto.objects.create(news=news_obj, photo=photo_file)
        created_photos.append(new_photo)

    ser = NewsPhotoSerializer(created_photos, many=True)
    return Response(ser.data, status=201)


@api_view(['GET'])
def list_friendships(request):
    qs = Friendship.objects.all()
    ser = FriendshipSerializer(qs, many=True)
    return Response(ser.data, status=200)


@api_view(['POST'])
def add_friend(request):
    user_id = request.data.get('user_id')
    friend_id = request.data.get('friend_id')
    if not user_id or not friend_id:
        return Response({'error': 'Нужно user_id и friend_id'}, status=400)

    if Friendship.objects.filter(user_id=user_id, friend_id=friend_id).exists():
        return Response({'error': 'Уже отправляли заявку'}, status=400)

    fr = Friendship.objects.create(
        user_id=user_id,
        friend_id=friend_id,
        status='pending',
        created_at=timezone.now()
    )
    return Response(FriendshipSerializer(fr).data, status=201)


@api_view(['POST'])
def accept_friend(request):
    friendship_id = request.data.get('friendship_id')
    if friendship_id:
        try:
            fr = Friendship.objects.get(id=friendship_id)
        except Friendship.DoesNotExist:
            return Response({'error': 'Заявка не найдена'}, status=404)
    else:
        user_id = request.data.get('user_id')
        friend_id = request.data.get('friend_id')
        try:
            fr = Friendship.objects.get(user_id=user_id, friend_id=friend_id)
        except Friendship.DoesNotExist:
            return Response({'error': 'Заявка не найдена'}, status=404)

    fr.status = 'accepted'
    fr.accepted_at = timezone.now()
    fr.save()
    return Response(FriendshipSerializer(fr).data, status=200)


@api_view(['DELETE'])
def remove_friend(request):
    friendship_id = request.data.get('friendship_id')
    if friendship_id:
        try:
            fr = Friendship.objects.get(id=friendship_id)
        except Friendship.DoesNotExist:
            return Response({'error': 'Не найдено'}, status=404)
    else:
        user_id = request.data.get('user_id')
        friend_id = request.data.get('friend_id')
        try:
            fr = Friendship.objects.get(user_id=user_id, friend_id=friend_id)
        except Friendship.DoesNotExist:
            return Response({'error': 'Не найдено'}, status=404)

    fr.delete()
    return Response({'message': 'Удалено'}, status=204)

@api_view(['GET'])
def list_messages(request):
    qs = Message.objects.all().order_by('sent_at')
    ser = MessageSerializer(qs, many=True)
    return Response(ser.data, status=200)

@api_view(['POST'])
@permission_classes([IsAuthenticated]) 
def send_message(request):
    sender = request.user 
    receiver_id = request.data.get('receiver_id')
    content = request.data.get('content')

    if not receiver_id or not content:
        return Response({'error': 'Не все поля заполнены'}, status=400)

    try:
        receiver = User.objects.get(id=receiver_id)
        message = Message.objects.create(sender=sender, receiver=receiver, content=content)
        return Response({'message': 'Сообщение отправлено', 'message_id': message.id}, status=201)
    except User.DoesNotExist:
        return Response({'error': 'Получатель не найден'}, status=404)

@api_view(['GET'])
def get_messages_between(request, user1, user2):
    qs = Message.objects.filter(
        Q(from_user_id=user1, to_user_id=user2) |
        Q(from_user_id=user2, to_user_id=user1)
    ).order_by('sent_at')
    ser = MessageSerializer(qs, many=True)
    return Response(ser.data, status=200)

import logging
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Comment

# Настраиваем логирование
logger = logging.getLogger(__name__)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_comment(request, comment_id):
    logger.debug(f"Received delete_comment request for comment_id={comment_id}, user={request.user}")
    
    try:
        comment = Comment.objects.get(pk=comment_id)
    except Comment.DoesNotExist:
        logger.warning(f"Comment with id={comment_id} does not exist in the database")
        return Response({"detail": "Комментарий не найден"}, status=404)

    if comment.is_deleted:
        logger.debug(f"Comment with id={comment_id} is already deleted (is_deleted=True)")
        return Response(status=204)  # Убираем тело ответа

    if comment.user != request.user and not request.user.is_superuser:
        logger.warning(f"User {request.user} does not have permission to delete comment {comment_id}")
        return Response({"detail": "Нет прав на удаление"}, status=403)

    comment.is_deleted = True
    comment.deleted_at = timezone.now()
    comment.deleted_by = request.user
    comment.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])
    logger.debug(f"Comment {comment_id} marked as deleted by user {request.user}")

    return Response(status=204)


from datetime import timedelta
from django.utils import timezone
from django.db.models import Count

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([AllowAny])
def list_events(request):
    filter_param = request.GET.get('filter')
    now = timezone.now()
    logger.debug(f"Current time: {now}, Filter: {filter_param}")
    qs = Event.objects.filter(status="approved")
    logger.debug(f"Initial queryset count: {qs.count()}")

    if filter_param == "popular":
        qs = qs.annotate(registrations_count=Count('registrations')).order_by('-registrations_count')
    elif filter_param == "upcoming":
        qs = qs.filter(
            end_datetime__gte=now,
            start_datetime__lte=now + timedelta(weeks=3)  
        ).order_by('start_datetime')
    elif filter_param == "planned":
        qs = qs.filter(
            end_datetime__gte=now,  
            start_datetime__gte=now + timedelta(weeks=3),  
            start_datetime__lte=now + timedelta(weeks=10)  
        ).order_by('start_datetime')
    else:
        qs = qs.order_by('-created_at')

    logger.debug(f"Filtered queryset count: {qs.count()}")
    for event in qs:
        logger.debug(
            f"Event: {event.title}, Start: {event.start_datetime}, "
            f"End: {event.end_datetime}, Registrations: {getattr(event, 'registrations_count', 'N/A')}"
        )

    serializer = EventSerializer(qs, many=True)
    return Response(serializer.data, status=200)

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_event(request):

    serializer = EventSerializer(data=request.data, context={'request': request})

    # Проверка валидации
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Сохраняем мероприятие со статусом 'pending' и организатором == текущий user
    event = serializer.save(status='pending', organizer=request.user)

    # -- 1. Отправляем email в отдельном потоке
    def _send_email_about_pending_event(user_email, event_title):
        subject = f"Вы подали мероприятие: {event_title}"
        body = (
            f"Здравствуйте! Ваше мероприятие «{event_title}» отправлено на модерацию.\n\n"
            "Ожидайте, когда администратор его рассмотрит. "
            "После модерации вы получите новое уведомление."
        )
        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,  # У вас в settings.py
                recipient_list=[user_email],
                fail_silently=True,  # Чтобы не ронять процесс при ошибках
            )
        except Exception as e:
            logger.error(f"[create_event] Ошибка при отправке email: {e}")

    threading.Thread(
        target=_send_email_about_pending_event,
        args=(request.user.email, event.title)
    ).start()

    # -- 2. Создаём уведомление
    Notification.objects.create(
        user=request.user,
        type='event_submitted',  # Произвольный тип, чтобы различать типы уведомлений
        message=(
            f"Ваше мероприятие '{event.title}' отправлено на модерацию. "
            "Статус: 'pending'. Ожидайте результатов проверки."
        ),
        entity_type='event',  
        entity_id=event.id
    )

    # -- 3. Возвращаем ответ
    return Response(
        EventSerializer(event, context={'request': request}).data,
        status=status.HTTP_201_CREATED
    )

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated

from .authentication import CustomTokenAuthentication
from .serializers import EventRegistrationSerializer
from .models import Event, EventRegistration, Notification

import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logger = logging.getLogger(__name__)


@api_view(['POST', 'DELETE'])
@authentication_classes([CustomTokenAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def register_for_event(request, pk):
    try:
        event = Event.objects.get(id=pk)
    except Event.DoesNotExist:
        return Response({"error": "Мероприятие не найдено"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'POST':
        # Проверка, зарегистрирован ли уже
        already_registered = EventRegistration.objects.filter(event=event, user=request.user).exists()
        if already_registered:
            return Response({"error": "Вы уже зарегистрированы на это мероприятие"}, status=status.HTTP_400_BAD_REQUEST)

        # Проверка лимита
        if event.max_participants and event.max_participants > 0:
            current_count = EventRegistration.objects.filter(event=event).count()
            if current_count >= event.max_participants:
                return Response({
                    "error": "Достигнут лимит участников для этого мероприятия."
                }, status=status.HTTP_400_BAD_REQUEST)

        # Данные
        data = {
            'event': pk,
            'user': request.user.id,
            'registered_at': timezone.now()
        }

        serializer = EventRegistrationSerializer(data=data)
        if serializer.is_valid():
            registration = serializer.save()

            # 🔔 Уведомление организатору
            if request.user != event.organizer:
                Notification.objects.create(
                    user=event.organizer,
                    type='event_joined',
                    message=f"{request.user.username} записался на ваше мероприятие «{event.title}»",
                    entity_type='event',
                    entity_id=event.id,
                )

            # Отправка email
            threading.Thread(
                target=send_event_registration_email,
                args=(request.user, event)
            ).start()

            return Response(
                EventRegistrationSerializer(registration).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        # Отмена участия
        registration = EventRegistration.objects.filter(event=event, user=request.user).first()
        if not registration:
            return Response({"error": "Вы не зарегистрированы на это мероприятие"}, status=status.HTTP_400_BAD_REQUEST)

        registration.delete()

        # 🔔 Уведомление организатору о выходе
        if request.user != event.organizer:
            Notification.objects.create(
                user=event.organizer,
                type='event_left',
                message=f"{request.user.username} отменил участие в мероприятии «{event.title}»",
                entity_type='event',
                entity_id=event.id,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)


def send_event_registration_email(user, event):
    SMTP_SERVER = "smtp.yandex.ru"
    SMTP_PORT = 465
    SENDER_EMAIL = "dylanbob0@yandex.ru"
    SENDER_PASSWORD = "qundmssnkzvpurqq"

    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = user.email
        msg["Subject"] = f"Регистрация на мероприятие «{event.title}»"

        body = (
            f"Здравствуйте, {user.username}!\n\n"
            f"Вы успешно зарегистрировались на мероприятие: {event.title}.\n"
            f"Дата: {event.start_datetime.strftime('%d.%m.%Y %H:%M')} - {event.end_datetime.strftime('%d.%m.%Y %H:%M')}\n"
            f"Адрес: {event.address or 'не указан'}\n\n"
            f"Спасибо, что участвуете в жизни сообщества!"
        )
        msg.attach(MIMEText(body, "plain", "utf-8"))

        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, user.email, msg.as_string())
        server.quit()
        logger.info(f"📧 Email-уведомление о регистрации отправлено на {user.email}")
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке письма: {e}")


@api_view(['GET'])
def list_places(request):
    qs = Place.objects.all().order_by('-created_at')
    ser = PlaceSerializer(qs, many=True)
    return Response(ser.data, status=200)


@api_view(['POST'])
def create_place(request):
    data = request.data.copy()
    data['created_at'] = str(timezone.now())

    s = PlaceSerializer(data=data)
    if s.is_valid():
        place = s.save()
        return Response(PlaceSerializer(place).data, status=201)
    return Response(s.errors, status=400)


@api_view(['POST'])
def rate_place(request):
    data = request.data.copy()
    data['created_at'] = str(timezone.now())
    s = PlaceRatingSerializer(data=data)
    if s.is_valid():
        rating_obj = s.save()
        return Response(PlaceRatingSerializer(rating_obj).data, status=201)
    return Response(s.errors, status=400)


@api_view(['POST'])
def approve_place(request, pk):
    try:
        place_obj = Place.objects.get(pk=pk)
    except Place.DoesNotExist:
        return Response({'error': 'Place not found'}, status=404)
    
    if not request.user.is_authenticated:
        return Response({'error': 'Вы не авторизованы'}, status=401)

    if request.user.role != 'admin':
        return Response({'error':'Only admin can approve places'}, status=403)

    place_obj.is_approved = 1
    place_obj.save()
    return Response({'message': 'Place approved'}, status=200)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_comment(request):
    data = request.data.copy()
    data['created_at'] = timezone.now()

    serializer = CommentSerializer(data=data, context={'request': request})
    if serializer.is_valid():
        comment = serializer.save()

        # 🔔 Уведомления только для мероприятий
        if comment.content_type.model == 'event':
            from .models import Event, Notification

            try:
                event = Event.objects.get(id=comment.object_id)
            except Event.DoesNotExist:
                pass
            else:
                # Если корневой комментарий, уведомляем организатора события
                if not comment.parent_comment and request.user != event.organizer:
                    Notification.objects.create(
                        user=event.organizer,
                        type='event_comment',
                        message=f"{request.user.username} оставил комментарий к вашему мероприятию '{event.title}'",
                        entity_type='event',
                        entity_id=event.id,
                    )
                # Если это ответ на другой комментарий
                elif comment.parent_comment and request.user != comment.parent_comment.user:
                    Notification.objects.create(
                        user=comment.parent_comment.user,
                        type='event_comment_reply',
                        message=f"{request.user.username} ответил на ваш комментарий в мероприятии '{event.title}'",
                        entity_type='event',
                        entity_id=event.id,
                    )

        return Response(
            CommentSerializer(comment, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
            content_type="application/json"
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.pagination import PageNumberPagination
from django.contrib.contenttypes.models import ContentType
from .serializers import CommentSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.pagination import PageNumberPagination
from django.contrib.contenttypes.models import ContentType
from .serializers import CommentSerializer

class CommentPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def list_comments(request):
    entity_type_param = request.GET.get('entity_type')
    entity_id_param = request.GET.get('entity_id')

    qs = Comment.objects.filter(is_deleted=False)
    qs = qs.select_related('user').prefetch_related('comment_likes', 'replies')

    if entity_type_param:
        try:
            ct = ContentType.objects.get(model=entity_type_param.lower())
            qs = qs.filter(content_type=ct)
        except ContentType.DoesNotExist:
            return Response({"error": "Invalid entity_type"}, status=400)
    if entity_id_param:
        qs = qs.filter(object_id=entity_id_param)

    # Фильтруем только корневые комментарии
    qs = qs.filter(parent_comment_id__isnull=True).order_by('-created_at')

    # Пагинация
    paginator = CommentPagination()
    paginated_qs = paginator.paginate_queryset(qs, request)

    # Сериализация с учетом вложенности через CommentSerializer
    serializer = CommentSerializer(paginated_qs, many=True, context={'request': request})
    return paginator.get_paginated_response(serializer.data)

import logging
logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def get_latest_comment(request, news_id):
    try:
        news = News.objects.get(pk=news_id)
    except News.DoesNotExist:
        return Response({"error": "Новость не найдена"}, status=404)
    try:
        ct = ContentType.objects.get(model='news')
        comments = Comment.objects.filter(
            content_type=ct,
            object_id=news_id,
            is_deleted=False
        ).order_by('-created_at')
        if not comments.exists():
            return Response({"message": "Комментариев пока нет"}, status=200)
        serializer = CommentSerializer(comments, many=True, context={'request': request})
        return Response(serializer.data, status=200)
    except ContentType.DoesNotExist:
        return Response({"error": "Неверный тип сущности"}, status=400)
    except Exception as e:
        return Response({"error": str(e)}, status=400)
    
from .models import CommentLike, Notification  # добавили Notification
from django.contrib.contenttypes.models import ContentType

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_comment_like(request, comment_id):
    try:
        comment = Comment.objects.get(id=comment_id, is_deleted=False)
    except Comment.DoesNotExist:
        return Response({"detail": "Комментарий не найден или удалён"}, status=404)

    existing_like = CommentLike.objects.filter(user=request.user, comment=comment).first()
    if existing_like:
        existing_like.delete()
        message = "Лайк снят"
        liked = False
    else:
        CommentLike.objects.create(user=request.user, comment=comment)
        message = "Лайк поставлен"
        liked = True

        # Создание уведомления, если пользователь лайкнул чужой комментарий
        if comment.user != request.user:
            Notification.objects.create(
                user=comment.user,
                type='comment_liked',
                message=f"Пользователю {request.user.username} понравился ваш комментарий: «{comment.content[:50]}»",
                entity_type=comment.content_type.model,
                entity_id=comment.object_id,
            )

    current_likes = comment.comment_likes.count()
    return Response({
        "comment_id": comment_id,
        "message": message,
        "liked": liked,
        "likes_count": current_likes
    }, status=200)



logger = logging.getLogger(__name__)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_comment(request, comment_id):
    logger.debug(f"Received update_comment request for comment_id={comment_id}, user={request.user}")
    try:
        comment = Comment.objects.get(pk=comment_id, is_deleted=False)
    except Comment.DoesNotExist:
        logger.warning(f"Comment with id={comment_id} not found or deleted")
        return Response({"detail": "Комментарий не найден или удалён"}, status=404)

    if comment.user != request.user and not request.user.is_superuser:
        logger.warning(f"User {request.user} does not have permission to edit comment {comment_id}")
        return Response({"detail": "У вас нет прав на редактирование этого комментария"}, status=403)

    new_content = request.data.get('content')
    if not new_content or len(new_content.strip()) < 3:
        logger.warning(f"Invalid content provided: {new_content}")
        return Response({"detail": "Комментарий должен содержать минимум 3 символа"}, status=400)

    comment.content = new_content
    comment.save(update_fields=['content'])
    logger.debug(f"Comment {comment_id} updated with new content: {new_content}")

    # Передаём контекст с request в сериализатор
    ser = CommentSerializer(comment, context={'request': request})
    logger.debug(f"Serialized comment data: {ser.data}")
    return Response(ser.data, status=200)

@api_view(['GET'])
@authentication_classes([CustomTokenAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def list_notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    serializer = NotificationSerializer(notifications, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def mark_notification_read(request):
    notif_id = request.data.get('notification_id')
    if not notif_id:
        return Response({'error': 'No notification_id'}, status=400)

    try:
        notif = Notification.objects.get(id=notif_id)
    except Notification.DoesNotExist:
        return Response({'error': 'Уведомление не найдено'}, status=404)

    notif.read_at = timezone.now()
    notif.save()
    return Response(NotificationSerializer(notif).data, status=200)

@api_view(['GET'])
def list_user_activity(request):
    user_id = request.query_params.get('user_id')
    if user_id:
        activities = UserActivity.objects.filter(user_id=user_id).order_by('-created_at')
    else:
        activities = UserActivity.objects.all().order_by('-created_at')

    ser = UserActivitySerializer(activities, many=True)
    return Response(ser.data, status=200)


@api_view(['POST'])
def add_user_activity(request):
    data = request.data.copy()
    data['created_at'] = str(timezone.now())

    s = UserActivitySerializer(data=data)
    if s.is_valid():
        act = s.save()
        return Response(UserActivitySerializer(act).data, status=201)
    return Response(s.errors, status=400)

from django.contrib.auth.hashers import make_password

@api_view(['POST'])
def request_password_reset(request):
    email = request.data.get('email')

    if not email:
        return Response({'error': 'Введите email'}, status=400)

    try:
        user = User.objects.get(email=email)
        reset_code = str(random.randint(100000, 999999))
        user.password_reset_code = reset_code
        user.password_reset_expires = timezone.now() + timezone.timedelta(minutes=10)
        user.save()

        # Запускаем отправку письма в отдельном потоке
        threading.Thread(target=send_reset_email, args=(email, user.username, reset_code)).start()

        return Response({'message': 'Код сброса отправлен на email'}, status=200)

    except User.DoesNotExist:
        return Response({'error': 'Нет пользователя с таким email'}, status=404)


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

@api_view(['GET'])
@permission_classes([AllowAny])
def check_user_exists(request):
    email = request.query_params.get('email')
    if not email:
        return Response({'error': 'Email parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user = User.objects.get(email=email)
        return Response({'exists': True, 'user_id': user.id}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({'exists': False}, status=status.HTTP_404_NOT_FOUND)

    
def send_reset_email(email, username, reset_code):
    SMTP_SERVER = "smtp.yandex.ru"
    SMTP_PORT = 465
    SENDER_EMAIL = "dylanbob0@yandex.ru"
    SENDER_PASSWORD = "qundmssnkzvpurqq"

    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = email
        msg["Subject"] = "Сброс пароля"

        body = f"Здравствуйте, {username}!\n\nВаш код сброса пароля: {reset_code}\n\nВведите этот код в приложении, чтобы сбросить пароль."
        msg.attach(MIMEText(body, "plain", "utf-8"))

        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, email, msg.as_string())
        server.quit()
        logger.info(f"Reset email sent successfully to {email}")
    except Exception as e:
        logger.error(f"Ошибка при отправке reset email: {e}")

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_event(request, pk):
    try:
        event = Event.objects.get(pk=pk)
    except Event.DoesNotExist:
        return Response({'error': 'Мероприятие не найдено'}, status=404)
    
    # Проверяем, что запрашивающий пользователь является организатором
    if event.organizer != request.user:
        return Response({'error': 'Вы не можете удалить это мероприятие'}, status=403)
    
    event.delete()
    return Response({'message': 'Мероприятие удалено'}, status=204)

from .serializers import EventDetailSerializer, EventPhoto, EventPhotoSerializer
from .models import EventView  # не забудь импорт

@api_view(['GET', 'DELETE'])
@permission_classes([IsAuthenticated])  # Добавляем авторизацию для DELETE
def event_detail(request, pk):
    try:
        event = Event.objects.get(pk=pk)
    except Event.DoesNotExist:
        return Response({'error': 'Событие не найдено'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        if event.status != 'approved':
            return Response({'error': 'Событие не одобрено'}, status=status.HTTP_403_FORBIDDEN)

        if request.user.is_authenticated:
            already_viewed = EventView.objects.filter(event=event, user=request.user).exists()
            if not already_viewed:
                EventView.objects.create(event=event, user=request.user)
                event.views_count = F('views_count') + 1
                event.save(update_fields=['views_count'])
                event.refresh_from_db()

        serializer = EventDetailSerializer(event, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


    elif request.method == 'DELETE':
        if not request.user.is_authenticated:
            return Response({'error': 'Требуется аутентификация'}, status=status.HTTP_401_UNAUTHORIZED)
        if event.organizer != request.user:
            return Response({'error': 'Вы не можете удалить это мероприятие'}, status=status.HTTP_403_FORBIDDEN)
        event.delete()
        return Response({'message': 'Мероприятие удалено'}, status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_event_photos(request, pk):
    """Загрузка дополнительных фотографий к событию."""
    try:
        event = Event.objects.get(pk=pk)
    except Event.DoesNotExist:
        return Response({'error': 'Событие не найдено'}, status=404)

    # Проверяем, передал ли пользователь файлы:
    if 'photos' not in request.FILES:
        return Response({'error': 'Нет файлов photos'}, status=400)

    # Получаем список загружаемых файлов:
    photos = request.FILES.getlist('photos')
    
    created_objs = []
    for photo_file in photos:
        new_photo = EventPhoto.objects.create(
            event=event,
            photo=photo_file
        )
        created_objs.append(new_photo)

    # Сериализаторим добавленные фото, чтобы вернуть их в ответе
    serializer = EventPhotoSerializer(created_objs, many=True)
    return Response(serializer.data, status=201)
from django.shortcuts import get_object_or_404
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@authentication_classes([CustomTokenAuthentication])
def delete_event(request, pk):

    print(f"DEBUG: delete_event called for event_id={pk}")
    print(f"DEBUG: Authenticated user: {request.user.username} ({request.user.email})")

    # Находим мероприятие
    event = get_object_or_404(Event, id=pk)
    print(f"DEBUG: Found event: {event.title}")

    # Проверяем, является ли текущий пользователь организатором мероприятия
    if event.organizer != request.user:
        print(f"DEBUG: User {request.user.username} is not the organizer of event {pk}")
        return Response(
            {"detail": "You are not the organizer of this event."},
            status=status.HTTP_403_FORBIDDEN
        )

    # Удаляем мероприятие
    event.delete()
    print(f"DEBUG: Event {pk} deleted successfully")
    return Response(status=status.HTTP_204_NO_CONTENT)  

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
@authentication_classes([CustomTokenAuthentication])
def update_event_preview(request, pk):
    """
    Обновляет превью-изображение мероприятия.
    """
    try:
        event = Event.objects.get(pk=pk)
    except Event.DoesNotExist:
        return Response({'error': 'Событие не найдено'}, status=status.HTTP_404_NOT_FOUND)

    # Проверяем, что пользователь — организатор
    if event.organizer != request.user:
        return Response({'error': 'Вы не можете обновить это мероприятие'}, status=status.HTTP_403_FORBIDDEN)

    # Проверяем, передан ли файл
    if 'image' not in request.FILES:
        return Response({'error': 'Изображение не предоставлено'}, status=status.HTTP_400_BAD_REQUEST)

    # Обновляем поле image
    event.image = request.FILES['image']
    event.save(update_fields=['image'])

    serializer = EventSerializer(event)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([CustomTokenAuthentication, SessionAuthentication])
def my_events(request):
    user = request.user
    qs = Event.objects.filter(organizer=user).order_by('-created_at')
    serializer = EventSerializer(qs, many=True, context={'request': request})
    return Response(serializer.data, status=200)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_notification(request, pk):
    try:
        notification = Notification.objects.get(pk=pk, user=request.user)
    except Notification.DoesNotExist:
        return Response({"error": "Уведомление не найдено"}, status=status.HTTP_404_NOT_FOUND)

    notification.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

from .models import FCMToken
from .serializers import FCMTokenSerializer
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_fcm_token(request):
    token = request.data.get('token')
    if not token:
        return Response({'error': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)

    fcm_token, created = FCMToken.objects.get_or_create(
        user=request.user,
        defaults={'token': token}
    )
    if not created:
        fcm_token.token = token
        fcm_token.save()

    serializer = FCMTokenSerializer(fcm_token)
    return Response(serializer.data, status=status.HTTP_201_CREATED)