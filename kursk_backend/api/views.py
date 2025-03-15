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
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response({'error': 'Не все поля заполнены'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({'error': 'Нет такого пользователя'}, status=status.HTTP_404_NOT_FOUND)

    if not user.is_email_confirmed:
        return Response({'error': 'Email не подтверждён'}, status=status.HTTP_403_FORBIDDEN)

    # Проверяем пароль через стандартное поле password (хранится в зашифрованном виде)
    if check_password(password, user.password):
        # Для обеспечения уникальности токена удаляем старые
        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)
        return Response({
            'message': 'Успешный вход',
            'user_id': user.id,
            'token': token.key
        }, status=status.HTTP_200_OK)

    return Response({'error': 'Неверный пароль'}, status=status.HTTP_400_BAD_REQUEST)




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

    like, created = NewsLike.objects.get_or_create(news=news_obj, user=user)

    if not created:
        like.delete()
        message = 'Лайк удалён'
    else:
        message = 'Лайк добавлен'

    news_obj.likes = NewsLike.objects.filter(news=news_obj).count()
    news_obj.save()

    return Response({'message': message, 'likes': news_obj.likes}, status=200)

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


@api_view(['GET', 'PUT', 'DELETE'])
def user_detail(request, pk):
    try:
        user_obj = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({'error': 'Пользователь не найден'}, status=404)

    if request.method == 'GET':
        # Возвращаем только id, username, avatar
        return Response({
            'id': user_obj.id,
            'username': user_obj.username,
            'avatar': user_obj.avatar.url if user_obj.avatar else None
        }, status=200)

    elif request.method == 'PUT':
        data = request.data.copy()
        data['updated_at'] = str(timezone.now())
        ser = UserSerializer(user_obj, data=data, partial=True)
        if ser.is_valid():
            ser.save()
            return Response(ser.data, status=200)
        return Response(ser.errors, status=400)

    elif request.method == 'DELETE':
        user_obj.delete()
        return Response({'message': 'Пользователь удалён'}, status=204)

from django.db.models import Count, F, Value, FloatField, ExpressionWrapper, Case, When, Q
from django.utils import timezone
from .serializers import NewsListSerializer, NewsDetailSerializer


@api_view(['GET'])
def news_list(request):
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

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_comment(request, comment_id):
    try:
        comment = Comment.objects.get(pk=comment_id, is_deleted=False)
    except Comment.DoesNotExist:
        return Response({"detail": "Комментарий не найден или уже удалён"}, status=404)

    if comment.user != request.user and not request.user.is_superuser:
        return Response({"detail": "Нет прав на удаление"}, status=403)

    comment.is_deleted = True
    comment.deleted_at = timezone.now()
    comment.deleted_by = request.user.id
    comment.save()
    return Response({"detail": "Комментарий помечен как удалённый"}, status=204)


@api_view(['GET'])
def list_events(request):
    qs = Event.objects.all().order_by('-created_at')
    ser = EventSerializer(qs, many=True)
    return Response(ser.data, status=200)


@api_view(['POST'])
def create_event(request):
    data = request.data.copy()
    data['created_at'] = str(timezone.now())

    s = EventSerializer(data=data)
    if s.is_valid():
        ev = s.save()
        return Response(EventSerializer(ev).data, status=201)
    return Response(s.errors, status=400)


@api_view(['POST'])
def register_for_event(request):
    data = request.data.copy()
    data['registered_at'] = str(timezone.now())
    s = EventRegistrationSerializer(data=data)
    if s.is_valid():
        reg = s.save()
        return Response(EventRegistrationSerializer(reg).data, status=201)
    return Response(s.errors, status=400)

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
        return Response(
            CommentSerializer(comment).data,
            status=status.HTTP_201_CREATED,
            content_type="application/json"
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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

    qs = Comment.objects.filter(is_deleted=False)  # Исключаем удалённые
    if entity_type_param:
        try:
            ct = ContentType.objects.get(model=entity_type_param.lower())
            qs = qs.filter(content_type=ct)
        except ContentType.DoesNotExist:
            return Response({"error": "Invalid entity_type"}, status=400)
    if entity_id_param:
        qs = qs.filter(object_id=entity_id_param)

    qs = qs.order_by('-created_at')  # Сортировка: новые сверху

    # Пагинация
    paginator = CommentPagination()
    paginated_qs = paginator.paginate_queryset(qs, request)

    # Сериализация и формирование дерева
    flat_comments = CommentSerializer(paginated_qs, many=True).data
    comment_dict = {}
    for comment in flat_comments:
        comment['children'] = []
        comment_dict[comment['id']] = comment

    root_comments = []
    for comment in flat_comments:
        parent_id = comment.get('parent_comment')  # Используем 'parent_comment' из сериализатора
        if parent_id:
            parent = comment_dict.get(parent_id)
            if parent:
                parent['children'].append(comment)
        else:
            root_comments.append(comment)

    return paginator.get_paginated_response(root_comments)


@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def get_latest_comment(request, news_id):
    try:
        # Получаем ContentType для модели News
        ct = ContentType.objects.get(model='news')
        
        # Запрашиваем самый новый комментарий для новости
        latest_comment = Comment.objects.filter(
            content_type=ct,
            object_id=news_id,
            is_deleted=False
        ).order_by('-created_at').first()

        if not latest_comment:
            return Response({"message": "Комментариев пока нет"}, status=200)

        # Сериализуем только один комментарий
        serializer = CommentSerializer(latest_comment)
        return Response(serializer.data, status=200)

    except ContentType.DoesNotExist:
        return Response({"error": "Неверный тип сущности"}, status=400)
    except Exception as e:
        return Response({"error": str(e)}, status=400)
    
from .models import CommentLike
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

    current_likes = comment.comment_likes.count()
    return Response({
        "comment_id": comment_id,
        "message": message,
        "liked": liked,
        "likes_count": current_likes
    }, status=200)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_comment(request, comment_id):
    try:
        comment = Comment.objects.get(pk=comment_id, is_deleted=False)
    except Comment.DoesNotExist:
        return Response({"detail": "Комментарий не найден или удалён"}, status=404)

    if comment.user != request.user and not request.user.is_superuser:
        return Response({"detail": "У вас нет прав на редактирование этого комментария"}, status=403)

    new_content = request.data.get('content')
    if not new_content or len(new_content.strip()) < 3:
        return Response({"detail": "Комментарий должен содержать минимум 3 символа"}, status=400)

    comment.content = new_content
    comment.save(update_fields=['content'])

    ser = CommentSerializer(comment)
    return Response(ser.data, status=200)

@api_view(['GET'])
def list_notifications(request):
    user_id = request.query_params.get('user_id')
    if not user_id:
        return Response({'error': 'No user_id'}, status=400)

    notifs = Notification.objects.filter(user_id=user_id).order_by('-created_at')
    ser = NotificationSerializer(notifs, many=True)
    return Response(ser.data, status=200)


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




