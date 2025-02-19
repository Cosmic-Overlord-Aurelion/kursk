from django.db.models import Q
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password

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

from django.core.mail import send_mail
import random

@api_view(['POST'])
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

    hashed = make_password(password)
    verification_code = str(random.randint(100000, 999999))
    user = User.objects.create(
        username=username,
        email=email,
        password_hash=hashed,
        is_email_confirmed=False,
        email_verification_code=verification_code,
        created_at=timezone.now(),
        updated_at=timezone.now() 
    )

    try:
        subject = "Подтверждение почты"
        message = f"Здравствуйте, {username}!\n\nВаш код подтверждения: {verification_code}\n\nВведите этот код в приложении, чтобы завершить регистрацию."
        send_mail(subject, message, "noreply@yourdomain.com", [email])
        return Response({
            'message': 'Код подтверждения отправлен на e-mail.',
            'user_id': user.id
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': 'Ошибка при отправке письма. Попробуйте позже.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
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
        user.save()
        return Response({"message": "E-mail подтверждён! Теперь можно войти."}, status=200)
    else:
        return Response({"error": "Неверный код"}, status=400)


@api_view(['PUT', 'PATCH'])
def update_user_avatar(request, pk):
    try:
        user_obj = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({'error': 'Not found'}, status=404)

    serializer = UserSerializer(user_obj, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=200)
    return Response(serializer.errors, status=400)


@api_view(['POST'])
def login_user(request):
    username = request.data.get('username')
    password = request.data.get('password')

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response({'error': 'Нет такого пользователя'}, status=404)
    
    if not user.is_email_confirmed: return Response({"error":"Email not confirmed"}, status=403)

    if check_password(password, user.password_hash):
        return Response({'message': 'Успешный вход'}, status=200)
    else:
        return Response({'error': 'Неверный пароль'}, status=400)


@api_view(['GET'])
def list_users(request):
    qs = User.objects.all()
    ser = UserSerializer(qs, many=True)
    return Response(ser.data, status=200)


@api_view(['GET', 'PUT', 'DELETE'])
def user_detail(request, pk):
    try:
        user_obj = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({'error': 'Пользователь не найден'}, status=404)

    if request.method == 'GET':
        ser = UserSerializer(user_obj)
        return Response(ser.data, status=200)

    elif request.method == 'PUT':
        ser = UserSerializer(user_obj, data=request.data, partial=True)
        if ser.is_valid():
            ser.save()
            return Response(ser.data, status=200)
        return Response(ser.errors, status=400)

    elif request.method == 'DELETE':
        user_obj.delete()
        return Response({'message': 'Пользователь удалён'}, status=204)

@api_view(['GET'])
def news_list(request):
    qs = News.objects.all().order_by('-created_at')
    ser = NewsSerializer(qs, many=True)
    return Response(ser.data, status=200)


@api_view(['POST'])
def create_news(request):
    author_id = request.data.get('author_id')
    title = request.data.get('title')
    content = request.data.get('content')

    try:
        author = User.objects.get(id=author_id)
        if author.role != 'admin':
            return Response({'error': 'Только admin может публиковать новости'}, status=403)
    except User.DoesNotExist:
        return Response({'error': 'Пользователь не найден'}, status=404)

    data = {
        'title': title,
        'content': content,
        'author': author_id,
        'created_at': timezone.now()
    }
    s = NewsSerializer(data=data)
    if s.is_valid():
        news_obj = s.save(author=author)
        return Response(NewsSerializer(news_obj).data, status=201)
    return Response(s.errors, status=400)


@api_view(['GET', 'PUT', 'DELETE'])
def news_detail(request, pk):
    try:
        news_obj = News.objects.get(pk=pk)
    except News.DoesNotExist:
        return Response({'error': 'Новость не найдена'}, status=404)

    if request.method == 'GET':
        s = NewsSerializer(news_obj)
        return Response(s.data, status=200)

    elif request.method == 'PUT':
        s = NewsSerializer(news_obj, data=request.data, partial=True)
        if s.is_valid():
            s.save()
            return Response(s.data, status=200)
        return Response(s.errors, status=400)

    elif request.method == 'DELETE':
        news_obj.delete()
        return Response({'message': 'Новость удалена'}, status=204)

@api_view(['GET'])
def list_news_photos(request, pk):
    try:
        news_obj = News.objects.get(pk=pk)
    except News.DoesNotExist:
        return Response({'error': 'News not found'}, status=404)

    from .models import NewsPhoto
    from .serializers import NewsPhotoSerializer
    photos = NewsPhoto.objects.filter(news=news_obj)
    ser = NewsPhotoSerializer(photos, many=True)
    return Response(ser.data, status=200)


@api_view(['POST'])
def add_news_photo(request, pk):
    try:
        news_obj = News.objects.get(pk=pk)
    except News.DoesNotExist:
        return Response({'error': 'News not found'}, status=404)

    if 'photo' not in request.FILES:
        return Response({'error': 'No photo file provided'}, status=400)

    from .models import NewsPhoto
    from .serializers import NewsPhotoSerializer

    photo_file = request.FILES['photo']
    new_photo = NewsPhoto.objects.create(news=news_obj, photo=photo_file)
    ser = NewsPhotoSerializer(new_photo)
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
def send_message(request):
    from_user_id = request.data.get('from_user_id')
    to_user_id = request.data.get('to_user_id')
    content = request.data.get('content')
    if not all([from_user_id, to_user_id, content]):
        return Response({'error': 'Не все поля'}, status=400)

    msg = Message.objects.create(
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        content=content,
        sent_at=timezone.now()
    )
    return Response(MessageSerializer(msg).data, status=201)


@api_view(['GET'])
def get_messages_between(request, user1, user2):
    qs = Message.objects.filter(
        Q(from_user_id=user1, to_user_id=user2) |
        Q(from_user_id=user2, to_user_id=user1)
    ).order_by('sent_at')
    ser = MessageSerializer(qs, many=True)
    return Response(ser.data, status=200)


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
    
    if request.user.role != 'admin':
         return Response({'error':'Only admin can approve places'}, status=403)

    place_obj.is_approved = True
    place_obj.save()
    return Response({'message': 'Place approved'}, status=200)

@api_view(['POST'])
def create_comment(request):
    data = request.data.copy()
    data['created_at'] = str(timezone.now())

    s = CommentSerializer(data=data)
    if s.is_valid():
        com = s.save()
        return Response(CommentSerializer(com).data, status=201)
    return Response(s.errors, status=400)


@api_view(['GET'])
def list_comments(request):
    entity_type = request.GET.get('entity_type')
    entity_id = request.GET.get('entity_id')

    qs = Comment.objects.all()
    if entity_type:
        qs = qs.filter(entity_type=entity_type)
    if entity_id:
        qs = qs.filter(entity_id=entity_id)

    qs = qs.order_by('-created_at')
    ser = CommentSerializer(qs, many=True)
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
    from .models import UserActivity
    from .serializers import UserActivitySerializer

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

    from .models import UserActivity
    from .serializers import UserActivitySerializer

    s = UserActivitySerializer(data=data)
    if s.is_valid():
        act = s.save()
        return Response(UserActivitySerializer(act).data, status=201)
    return Response(s.errors, status=400)
