from rest_framework import serializers
from .models import (
    User, Friendship, Message, News,
    Event, EventRegistration,
    Place, PlaceRating,
    Comment
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'role',
            'avatar', 'bio',
            'created_at', 'updated_at'
        ]


class FriendshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Friendship
        fields = '__all__'


class MessageSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Message."""
    class Meta:
        model = Message
        fields = '__all__'


class NewsSerializer(serializers.ModelSerializer):

    class Meta:
        model = News
        fields = '__all__'


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


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'
