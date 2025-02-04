from django.db.models import Q
from django.utils import timezone

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.hashers import make_password, check_password

from .models import (
    User, News, Friendship, Message,
    Event, EventRegistration,
    Place, PlaceRating,
    Comment
)
from .serializers import (
    UserSerializer, NewsSerializer, FriendshipSerializer,
    MessageSerializer, EventSerializer, EventRegistrationSerializer,
    PlaceSerializer, PlaceRatingSerializer,
    CommentSerializer
)
@api_view(['POST'])
def register_user(request):
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')

    if not username or not email or not password:
        return Response({'error': 'Не все поля заполнены'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Такой username уже существует'}, status=status.HTTP_400_BAD_REQUEST)

    hashed = make_password(password)

    user = User.objects.create(
        username=username,
        email=email,
        password_hash=hashed,  
        created_at=timezone.now()
    )
    ser = UserSerializer(user)
    return Response(ser.data, status=status.HTTP_201_CREATED)

@api_view(['PUT', 'PATCH'])
def update_user_avatar(request, pk):
    try:
        user_obj = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({'error': 'Not found'}, status=404)

    serializer = UserSerializer(user_obj, data=request.data, partial=True)  # partial=True
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

    # Сравнить пароль:
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
