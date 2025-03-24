from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

# Create your models here.

class Author(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, help_text="Enter your biography", blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', default='profile_pics/default.png')
    
    def get_absolute_url(self):
        return reverse('author-detail', args=[str(self.id)])
    
    def __str__(self):
        return self.user.username

class Blog(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    content = models.TextField(help_text="Write your blog content here")
    post_date = models.DateTimeField(default=timezone.now)
    likes = models.ManyToManyField(User, through='Like', related_name='liked_posts')
    
    class Meta:
        ordering = ['-post_date']
    
    def get_absolute_url(self):
        return reverse('blog-detail', args=[str(self.id)])
    
    def __str__(self):
        return self.title
    
    def get_like_count(self):
        return self.likes.count()

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'blog')  # Prevent duplicate likes
        
    def __str__(self):
        return f"{self.user.username} likes {self.blog.title}"

class Comment(models.Model):
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(max_length=1000, help_text="Enter your comment")
    post_date = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['post_date']
    
    def __str__(self):
        return f'{self.content[:75]}...' if len(self.content) > 75 else self.content
