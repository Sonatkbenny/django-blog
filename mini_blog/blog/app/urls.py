from django.urls import path
from . import views

app_name = 'app'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('blog/', views.IndexView.as_view(), name='blog-home'),
    path('blog/blogs/', views.BlogListView.as_view(), name='blog-list'),
    path('blog/<int:pk>/', views.BlogDetailView.as_view(), name='blog-detail'),
    path('blog/blogger/<int:pk>/', views.AuthorDetailView.as_view(), name='author-detail'),
    path('blog/bloggers/', views.AuthorListView.as_view(), name='author-list'),
    path('blog/<int:pk>/create/', views.CommentCreateView.as_view(), name='comment-create'),
    path('register/', views.register, name='register'),
    path('blog/create/', views.BlogCreateView.as_view(), name='blog-create'),
    path('dashboard/', views.AuthorDashboardView.as_view(), name='author-dashboard'),
    path('profile/update/', views.profile_update, name='profile-update'),
    path('profile/password/', views.CustomPasswordChangeView.as_view(), name='password-change'),
    path('blog/<int:pk>/delete/', views.BlogDeleteView.as_view(), name='blog-delete'),
    path('comment/<int:pk>/delete/', views.CommentDeleteView.as_view(), name='comment-delete'),
    path('blog/<int:pk>/audio/', views.text_to_speech, name='blog-audio'),
    path('blog/<int:pk>/like/', views.toggle_like, name='blog-like'),
] 