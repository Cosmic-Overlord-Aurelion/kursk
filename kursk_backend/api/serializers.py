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
    entity_id = serializers.IntegerField(write_only=True, source='object_id')
    entity_type = serializers.CharField(write_only=True)
    parent_comment_id = serializers.IntegerField(
        write_only=True,
        required=False,
        allow_null=True,
        source='parent_comment'
    )
    user = UserSerializer(read_only=True)
    likes_count = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()  # Добавляем вложенные комментарии

    class Meta:
        model = Comment
        fields = [
            'id', 'user', 'entity_id', 'entity_type', 'content',
            'parent_comment_id', 'created_at', 'likes_count', 'children'
        ]

    def get_likes_count(self, obj):
        return obj.likes_count  # Используем свойство модели

    def get_children(self, obj):
        """Рекурсивно сериализуем вложенные комментарии."""
        if not obj.replies.exists():
            return []
        return CommentSerializer(
            obj.replies.filter(is_deleted=False),
            many=True,
            context=self.context
        ).data

    def validate(self, data):
        content = data.get('content')
        if not content or len(content.strip()) < 3:
            raise serializers.ValidationError("Комментарий должен содержать минимум 3 символа.")

        entity_type = self.initial_data.get('entity_type')
        entity_id = self.initial_data.get('entity_id')
        parent_comment_id = self.initial_data.get('parent_comment_id')

        if not entity_type or not entity_id:
            raise serializers.ValidationError("Необходимо указать entity_type и entity_id.")

        try:
            content_type = ContentType.objects.get(model=entity_type.lower())
        except ContentType.DoesNotExist:
            raise serializers.ValidationError("Некорректный entity_type.")

        data['content_type'] = content_type

        if parent_comment_id:
            try:
                parent_comment = Comment.objects.get(id=parent_comment_id, is_deleted=False)
                if (parent_comment.content_type != content_type or
                    parent_comment.object_id != int(entity_id)):
                    raise serializers.ValidationError(
                        "Родительский комментарий не относится к этой сущности."
                    )
                data['parent_comment'] = parent_comment
            except Comment.DoesNotExist:
                raise serializers.ValidationError("Родительский комментарий не найден.")

        return data

    def create(self, validated_data):
        validated_data.pop('entity_type', None)
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user
        return super().create(validated_data)


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'

class UserActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserActivity
        fields = '__all__'
