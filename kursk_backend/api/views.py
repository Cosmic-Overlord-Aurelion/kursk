
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import User, News
from .serializers import UserSerializer, NewsSerializer


@api_view(['POST'])
def register_user(request):
    """Регистрация пользователя (упрощённая)."""
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')

    if not username or not email or not password:
        return Response({'error': 'Не все поля заполнены'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Такой username уже существует'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create(
        username=username,
        email=email,
        password_hash=password,  
    )

    serializer = UserSerializer(user)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def news_list(request):
    """Вернуть список всех новостей (GET /api/news)."""
    qs = News.objects.all().order_by('-created_at')
    serializer = NewsSerializer(qs, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
def create_news(request):
    """Создать новость (POST /api/news/create). Допустим, только admin может."""
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
    }
    serializer = NewsSerializer(data=data)
    if serializer.is_valid():
        news_obj = serializer.save(author=author)
        return Response(NewsSerializer(news_obj).data, status=201)
    return Response(serializer.errors, status=400)
