
from django.db import models

class User(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    password_hash = models.TextField()  
    role = models.CharField(max_length=20, default='user')  
    avatar_url = models.TextField(null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f"{self.username} ({self.id})"


class Friendship(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='friendships_initiated')
    friend = models.ForeignKey('User', on_delete=models.CASCADE, related_name='friendships_received')
    status = models.CharField(max_length=20, default='pending')  # pending/accepted
    created_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'friendships'

    def __str__(self):
        return f"Friendship {self.user.username} - {self.friend.username} ({self.status})"

class Message(models.Model):
    id = models.AutoField(primary_key=True)
    from_user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='messages_sent')
    to_user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='messages_received')
    content = models.TextField()
    sent_at = models.DateTimeField()
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'messages'

    def __str__(self):
        return f"Msg from {self.from_user.username} to {self.to_user.username}"


class News(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.ForeignKey('User', on_delete=models.CASCADE)
    views_count = models.IntegerField(default=0)
    created_at = models.DateTimeField()

    class Meta:
        db_table = 'news'

    def __str__(self):
        return f"News: {self.title}"


class Event(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField(null=True, blank=True)
    organizer = models.ForeignKey('User', on_delete=models.CASCADE)
    views_count = models.IntegerField(default=0)
    created_at = models.DateTimeField()

    class Meta:
        db_table = 'events'

    def __str__(self):
        return f"Event: {self.title}"


class EventRegistration(models.Model):
    id = models.AutoField(primary_key=True)
    event = models.ForeignKey('Event', on_delete=models.CASCADE)
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default='going')  # going/interested/canceled
    registered_at = models.DateTimeField()

    class Meta:
        db_table = 'event_registrations'

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

    class Meta:
        db_table = 'places'

    def __str__(self):
        return f"Place: {self.name}"


class PlaceRating(models.Model):
    id = models.AutoField(primary_key=True)
    place = models.ForeignKey('Place', on_delete=models.CASCADE)
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    rating = models.IntegerField()  # 1..5
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'place_ratings'

    def __str__(self):
        return f"Rating {self.rating} for {self.place.name} by {self.user.username}"



class Comment(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    entity_type = models.CharField(max_length=20)  
    entity_id = models.IntegerField()             
    content = models.TextField()
    parent_comment_id = models.IntegerField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField()

    class Meta:
        db_table = 'comments'

    def __str__(self):
        return f"Comment by {self.user.username} on {self.entity_type} #{self.entity_id}"
