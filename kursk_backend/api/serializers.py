from rest_framework import serializers
from .models import User, News

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'avatar_url', 'bio', 'created_at']

class NewsSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)  

    class Meta:
        model = News
        fields = ['id', 'title', 'content', 'author', 'views_count', 'created_at']
