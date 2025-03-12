from rest_framework import serializers
from .models import (
    User, Friendship, Message, News,
    NewsPhoto,          
    Event, EventRegistration,
    Place, PlaceRating,
    Comment,
    Notification,         
    UserActivity         
)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email',
            'role', 'avatar', 'bio',
            'created_at', 'updated_at'
        ]

class FriendshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Friendship
        fields = '__all__'

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'


class NewsPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsPhoto
        fields = ('id', 'photo', 'uploaded_at')

class NewsDetailSerializer(serializers.ModelSerializer):
    photos = NewsPhotoSerializer(many=True, read_only=True)  # если у модели настроено related_name="photos"

    class Meta:
        model = News
        fields = (
            'id',
            'title',
            'subheader',
            'full_text',
            'author',
            'created_at',
            'views_count',
            'likes',
            'photos'
        )

class NewsListSerializer(serializers.ModelSerializer):
    photos = NewsPhotoSerializer(many=True, read_only=True)

    class Meta:
        model = News
        fields = ['id', 'title', 'subheader', 'views_count', 'likes', 'photos']


class NewsSerializer(serializers.ModelSerializer):
    photos = NewsPhotoSerializer(many=True, read_only=True)

    class Meta:
        model = News
        fields = ['id', 'title', 'subheader', 'full_text', 'views_count', 'likes', 'photos']

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = '__all__'

class EventRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventRegistration
        fields = '__all__'

class PlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = '__all__'

class PlaceRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlaceRating
        fields = '__all__'

from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import Comment
from .serializers import UserSerializer

class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    likes_count = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = '__all__'

    def get_likes_count(self, obj):
        return obj.comment_likes.count()

    def create(self, validated_data):
        """
        Когда мы вызываем serializer.save() во вью,
        этот метод привяжет комментарий к request.user (если есть)
        и потом вызовет super().create().
        """
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user
        return super().create(validated_data)

    def validate(self, data):
        """
        Здесь мы берем entity_type и entity_id (пришедшие в self.initial_data),
        мапим их на content_type и object_id, нужные модели Comment (GenericForeignKey).
        """
        entity_type = self.initial_data.get('entity_type')
        entity_id = self.initial_data.get('entity_id')

        if not entity_type or not entity_id:
            raise serializers.ValidationError("Необходимо указать entity_type и entity_id.")

        # Ищем ContentType по названию модели
        try:
            content_type = ContentType.objects.get(model=entity_type.lower())
        except ContentType.DoesNotExist:
            raise serializers.ValidationError("Некорректный entity_type.")

        # Присваиваем нужные поля
        data['content_type'] = content_type
        data['object_id'] = entity_id

        return data



class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'

class UserActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserActivity
        fields = '__all__'
