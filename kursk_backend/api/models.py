from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation

class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None):
        if not email:
            raise ValueError("У пользователя должен быть email")
        user = self.model(email=self.normalize_email(email), username=username)
        if password:
            user.set_password(password)  
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password):
        user = self.create_user(email, username, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    role = models.CharField(max_length=20, default="user")
    is_email_confirmed = models.BooleanField(default=False)
    email_verification_code = models.CharField(max_length=6, null=True, blank=True)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    password_reset_code = models.CharField(max_length=6, null=True, blank=True)
    password_reset_expires = models.DateTimeField(null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def get_by_natural_key(self, email):
        return self.__class__.objects.get(email=email)

    class Meta:
        db_table = "users"

    def __str__(self):
        return f"{self.username} ({self.email})"

class Friendship(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='friendships_initiated')
    friend = models.ForeignKey('User', on_delete=models.CASCADE, related_name='friendships_received')
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'friendships'

    def __str__(self):
        return f"Friendship {self.user.username} - {self.friend.username} ({self.status})"

from django.utils import timezone

class Message(models.Model):
    id = models.AutoField(primary_key=True)
    from_user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='messages_sent')
    to_user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='messages_received')
    content = models.TextField()
    sent_at = models.DateTimeField(default=timezone.now)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'messages'
        indexes = [
            models.Index(fields=['from_user', 'to_user', 'sent_at']),
        ]

    def __str__(self):
        return f"Msg from {self.from_user.username} to {self.to_user.username}"


User = get_user_model()

class News(models.Model):
    title = models.CharField(max_length=255)
    subheader = models.CharField(max_length=500, blank=True, null=True)
    full_text = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  
    views_count = models.PositiveIntegerField(default=0)
    likes = models.ManyToManyField(
        User,
        related_name='liked_news',
        blank=True
    )
    comments = GenericRelation('Comment')

    def __str__(self):
        return self.title

    @property
    def likes_count(self):
        return self.likes.count()

class NewsPhoto(models.Model):
    id = models.AutoField(primary_key=True)
    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name="photos")
    photo = models.ImageField(upload_to='news/', null=False, blank=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'news_photos'

    def __str__(self):
        return f"Photo #{self.id} for News {self.news.id}"

class Event(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    subheader = models.CharField(max_length=500, blank=True, null=True)
    description = models.TextField(null=True, blank=True)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField(null=True, blank=True)
    organizer = models.ForeignKey('User', on_delete=models.CASCADE)
    views_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)  
    image = models.ImageField(upload_to='events/', null=True, blank=True)
    status = models.CharField(max_length=20, default="pending")
    address = models.CharField(max_length=255, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    max_participants = models.PositiveIntegerField(
        default=0,
        verbose_name="Максимальное количество участников",
        help_text="0 означает, что ограничений нет"
    )
    participants_count = models.PositiveIntegerField(default=0)  

    # Постоянная связь с комментариями
    comments = GenericRelation('Comment')

    def __str__(self):
        return f"Event: {self.title}"



class EventPhoto(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='photos')
    photo = models.ImageField(upload_to='events/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"EventPhoto #{self.id} for {self.event.title}"


class EventRegistration(models.Model):
    id = models.AutoField(primary_key=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default='going')
    registered_at = models.DateTimeField()

    class Meta:
        db_table = 'event_registrations'
        unique_together = ('event', 'user')  

    def __str__(self):
        return f"Registration: {self.event.title} - {self.user.username}"

class Place(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    views_count = models.IntegerField(default=0)
    created_at = models.DateTimeField()
    added_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True)
    is_approved = models.BooleanField(default=False)

    class Meta:
        db_table = 'places'

    def __str__(self):
        return f"Place: {self.name}"

class PlaceRating(models.Model):
    id = models.AutoField(primary_key=True)
    place = models.ForeignKey('Place', on_delete=models.CASCADE)
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    rating = models.IntegerField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'place_ratings'

    def __str__(self):
        return f"Rating {self.rating} for {self.place.name} by {self.user.username}"


class Comment(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, blank=True)
    object_id = models.PositiveIntegerField()
    entity = GenericForeignKey('content_type', 'object_id')
    content = models.TextField(max_length=5000)  # Ограничение до 5000 символов
    parent_comment = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='replies'
    )
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        'User',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='deleted_comments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # Добавляем

    class Meta:
        db_table = 'comments'
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['parent_comment']),
            models.Index(fields=['is_deleted']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Comment by {self.user.username} on {self.content_type} #{self.object_id}"

    @property
    def likes_count(self):
        return self.comment_likes.count()

class Notification(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    type = models.CharField(max_length=50)
    message = models.TextField(null=True, blank=True)
    entity_type = models.CharField(max_length=20, null=True, blank=True)
    entity_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'notifications'

    def __str__(self):
        return f"Notif {self.type} to user {self.user_id}"

class UserActivity(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    action = models.CharField(max_length=50)  
    entity_type = models.CharField(max_length=20, null=True, blank=True)  
    entity_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_activity'

    def __str__(self):
        return f"Activity {self.action} by user {self.user_id}"
    
class NewsLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name="news_likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'news')

    def __str__(self):
        return f"Like by {self.user.username} on {self.news.title}"
    
class CommentLike(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    comment = models.ForeignKey('Comment', on_delete=models.CASCADE, related_name='comment_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'comment_likes'  
        unique_together = ('user', 'comment')
        indexes = [
            models.Index(fields=['user', 'comment']),  
        ]

    def __str__(self):
        return f"Like by {self.user.username} on comment #{self.comment.id}"

class EventView(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="viewed_users")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('event', 'user')  # Только один просмотр от одного юзера

    def __str__(self):
        return f"{self.user.username} viewed {self.event.title}"

User = get_user_model()

class FCMToken(models.Model):
    token = models.CharField(max_length=255, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.token} ({self.user.username if self.user else 'No user'})"


class PushNotificationSetting(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='push_settings')
    events = models.BooleanField(default=True)  # Уведомления о событиях
    moderation = models.BooleanField(default=True)  # Уведомления о модерации
    likes_comments = models.BooleanField(default=True)  # Уведомления о лайках и комментариях
    messages = models.BooleanField(default=True)  # Уведомления о сообщениях <--- Добавляем

    def __str__(self):
        return f"Settings for {self.user.username}"
