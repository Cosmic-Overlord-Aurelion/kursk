import logging
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
    photos = NewsPhotoSerializer(many=True, read_only=True)
    is_liked = serializers.SerializerMethodField()
    likes = serializers.SerializerMethodField()  

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
            'photos',
            'is_liked'
        )

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.comment_likes.filter(user=request.user).exists()
        return False

    def get_likes(self, obj):
        return obj.likes.count()

class NewsListSerializer(serializers.ModelSerializer):
    photos = NewsPhotoSerializer(many=True, read_only=True)
    likes = serializers.SerializerMethodField()  # добавляем поле для подсчёта лайков

    class Meta:
        model = News
        fields = ['id', 'title', 'subheader', 'views_count', 'likes', 'photos']

    def get_likes(self, obj):
        return obj.likes.count()

class NewsSerializer(serializers.ModelSerializer):
    photos = NewsPhotoSerializer(many=True, read_only=True)
    is_liked = serializers.SerializerMethodField()
    likes = serializers.SerializerMethodField()

    class Meta:
        model = News
        fields = ['id', 'title', 'subheader', 'full_text', 'views_count', 'likes', 'photos', 'is_liked']

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(id=request.user.id).exists()
        return False

    def get_likes(self, obj):
        return obj.likes.count()

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = '__all__'
        read_only_fields = ('created_at', 'status', 'views_count')

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

logger = logging.getLogger(__name__)

class CommentSerializer(serializers.ModelSerializer):
    entity_id = serializers.IntegerField(write_only=True, source='object_id')
    entity_type = serializers.CharField(write_only=True)
    parent_comment_id = serializers.PrimaryKeyRelatedField(
        queryset=Comment.objects.filter(is_deleted=False),
        required=False,
        allow_null=True,
        source='parent_comment'
    )
    user = UserSerializer(read_only=True)
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()  # Проверка лайка текущим пользователем
    user_avatar = serializers.SerializerMethodField()  # URL аватара пользователя
    children = serializers.SerializerMethodField()  # Вложенные комментарии
    reply_to = serializers.SerializerMethodField()    # Никнейм родительского комментария

    class Meta:
        model = Comment
        fields = [
            'id', 'user', 'entity_id', 'entity_type', 'content',
            'parent_comment_id', 'created_at', 'likes_count', 'is_liked',
            'user_avatar', 'children', 'reply_to'
        ]

    def get_likes_count(self, obj):
        return obj.likes_count  # Используем свойство модели

    def get_is_liked(self, obj):
        logger.debug(f"get_is_liked called for comment {obj.id}, context: {self.context}")
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            is_liked = obj.comment_likes.filter(user=request.user).exists()
            logger.debug(f"Comment {obj.id} is_liked by user {request.user}: {is_liked}")
            return is_liked
        logger.debug(f"User not authenticated for comment {obj.id}")
        return False

    def get_user_avatar(self, obj):
        logger.debug(f"get_user_avatar called for comment {obj.id}, user {obj.user}")
        request = self.context.get('request')
        if request and obj.user.avatar:
            avatar_url = request.build_absolute_uri(obj.user.avatar.url)
            logger.debug(f"Avatar URL for user {obj.user}: {avatar_url}")
            return avatar_url
        return None

    def get_children(self, obj):
        logger.debug(f"get_children called for comment {obj.id}")
        if not obj.replies.exists():
            logger.debug(f"No replies for comment {obj.id}")
            return []
        children = CommentSerializer(
            obj.replies.filter(is_deleted=False),
            many=True,
            context=self.context
        ).data
        logger.debug(f"Children for comment {obj.id}: {children}")
        return children

    def get_reply_to(self, obj):
        if obj.parent_comment:
            if obj.parent_comment.user:
                username = obj.parent_comment.user.username
                logger.debug(f"Comment {obj.id} reply_to user: {username}")
                return username
            else:
                logger.debug(f"Comment {obj.id} parent_comment.user is None")
                return None
        else:
            logger.debug(f"Comment {obj.id} has no parent_comment")
            return None

    def validate(self, data):
        logger.debug(f"Validating data: {data}")
        content = data.get('content')
        if not content or len(content.strip()) < 3:
            logger.warning(f"Validation failed: content too short: {content}")
            raise serializers.ValidationError("Комментарий должен содержать минимум 3 символа.")

        entity_type = self.initial_data.get('entity_type')
        entity_id = self.initial_data.get('entity_id')
        parent_comment_id = self.initial_data.get('parent_comment_id')

        if not entity_type or not entity_id:
            logger.warning("Validation failed: entity_type или entity_id отсутствуют")
            raise serializers.ValidationError("Необходимо указать entity_type и entity_id.")

        try:
            content_type = ContentType.objects.get(model=entity_type.lower())
        except ContentType.DoesNotExist:
            logger.warning(f"Validation failed: некорректный entity_type: {entity_type}")
            raise serializers.ValidationError("Некорректный entity_type.")

        data['content_type'] = content_type

        if parent_comment_id:
            try:
                parent_comment = Comment.objects.get(id=parent_comment_id, is_deleted=False)
                if (parent_comment.content_type != content_type or
                    parent_comment.object_id != int(entity_id)):
                    logger.warning(f"Validation failed: родительский комментарий {parent_comment_id} не относится к этой сущности")
                    raise serializers.ValidationError("Родительский комментарий не относится к этой сущности.")
                data['parent_comment'] = parent_comment
            except Comment.DoesNotExist:
                logger.warning(f"Validation failed: родительский комментарий {parent_comment_id} не найден")
                raise serializers.ValidationError("Родительский комментарий не найден.")

        logger.debug(f"Validation passed, data: {data}")
        return data

    def create(self, validated_data):
        logger.debug(f"Creating comment with validated data: {validated_data}")
        validated_data.pop('entity_type', None)
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user
        comment = super().create(validated_data)
        logger.debug(f"Created comment: {comment.id}")
        return comment


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'

class UserActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserActivity
        fields = '__all__'
