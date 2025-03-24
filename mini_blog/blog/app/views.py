from django.shortcuts import render
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic.edit import CreateView
from .models import Blog, Author, Comment, Like
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .forms import UserRegistrationForm, BlogForm, UserProfileUpdateForm, AuthorProfileUpdateForm, CustomPasswordChangeForm
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.views import PasswordChangeView
from django.http import HttpResponseForbidden, HttpResponse, FileResponse, HttpResponseServerError, JsonResponse
from gtts import gTTS
import os
import tempfile
from pathlib import Path
from django.db import models

# Create your views here.

class IndexView(generic.TemplateView):
    template_name = 'app/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['latest_blogs'] = Blog.objects.all().order_by('-post_date')[:4]
        return context

class BlogListView(generic.ListView):
    model = Blog
    paginate_by = 9
    template_name = 'app/blog_list.html'
    context_object_name = 'blog_list'

    def get_queryset(self):
        queryset = Blog.objects.select_related('author', 'author__user').order_by('-post_date')
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                models.Q(title__icontains=search_query) |
                models.Q(content__icontains=search_query) |
                models.Q(author__user__username__icontains=search_query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context

class BlogDetailView(generic.DetailView):
    model = Blog
    template_name = 'app/blog_detail.html'

class AuthorListView(generic.ListView):
    model = Author
    template_name = 'app/author_list.html'
    context_object_name = 'authors'

class AuthorDetailView(generic.DetailView):
    model = Author
    template_name = 'app/author_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['blogs'] = Blog.objects.filter(author=self.object).order_by('-post_date')
        return context

@method_decorator(login_required, name='dispatch')
class CommentCreateView(CreateView):
    model = Comment
    fields = ['content']
    template_name = 'app/comment_form.html'

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.blog = get_object_or_404(Blog, pk=self.kwargs['pk'])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('app:blog-detail', kwargs={'pk': self.kwargs['pk']})

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create Author profile for the user
            Author.objects.create(user=user, bio='')
            messages.success(request, f'Account created successfully! Please login to continue.')
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

@method_decorator(login_required, name='dispatch')
class BlogCreateView(CreateView):
    model = Blog
    form_class = BlogForm
    template_name = 'app/blog_form.html'
    
    def form_valid(self, form):
        # Set the author to the current user's author profile
        author = Author.objects.get(user=self.request.user)
        form.instance.author = author
        messages.success(self.request, 'Blog post created successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('app:blog-detail', kwargs={'pk': self.object.pk})

# Add a view to show author's dashboard with their posts
@method_decorator(login_required, name='dispatch')
class AuthorDashboardView(generic.TemplateView):
    template_name = 'app/author_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        author = Author.objects.get(user=self.request.user)
        context['blogs'] = Blog.objects.filter(author=author).order_by('-post_date')
        return context

@login_required
def profile_update(request):
    if request.method == 'POST':
        user_form = UserProfileUpdateForm(request.POST, instance=request.user)
        author_form = AuthorProfileUpdateForm(request.POST, request.FILES, instance=request.user.author)
        
        if user_form.is_valid() and author_form.is_valid():
            user_form.save()
            author_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('app:author-dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserProfileUpdateForm(instance=request.user)
        author_form = AuthorProfileUpdateForm(instance=request.user.author)
    
    return render(request, 'app/profile_update.html', {
        'user_form': user_form,
        'author_form': author_form
    })

class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    form_class = CustomPasswordChangeForm
    template_name = 'app/password_change.html'
    success_url = reverse_lazy('app:author-dashboard')

    def form_valid(self, form):
        messages.success(self.request, 'Your password has been changed successfully!')
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
class CommentDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Comment
    template_name = 'app/comment_confirm_delete.html'

    def get_object(self, queryset=None):
        comment = super().get_object(queryset)
        if comment.user != self.request.user:
            return HttpResponseForbidden()
        return comment

    def get_success_url(self):
        return reverse('app:blog-detail', kwargs={'pk': self.object.blog.pk})

@method_decorator(login_required, name='dispatch')
class BlogDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Blog
    template_name = 'app/blog_confirm_delete.html'

    def get_object(self, queryset=None):
        blog = super().get_object(queryset)
        if blog.author.user != self.request.user:
            return HttpResponseForbidden()
        return blog

    def get_success_url(self):
        return reverse('app:author-dashboard')

def text_to_speech(request, pk):
    try:
        blog = get_object_or_404(Blog, pk=pk)
        
        # Create media/audio directory if it doesn't exist
        audio_dir = Path('media/audio')
        audio_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate a unique filename
        filename = f'blog_{pk}_{blog.title[:30]}_{tempfile.mktemp(suffix=".mp3", prefix="", dir="")}'
        filename = "".join(c for c in filename if c.isalnum() or c in ('_', '-', '.'))  # sanitize filename
        audio_path = audio_dir / filename
        
        # Convert text to speech and save
        tts = gTTS(text=blog.content, lang='en', slow=False)
        tts.save(str(audio_path))
        
        # Serve the file
        if audio_path.exists():
            response = FileResponse(open(audio_path, 'rb'))
            response['Content-Type'] = 'audio/mpeg'
            response['Content-Disposition'] = f'inline; filename="{blog.title}.mp3"'
            
            # Let the OS handle file cleanup when the response is complete
            def cleanup_file(file_path):
                try:
                    if os.path.exists(file_path):
                        os.unlink(file_path)
                except:
                    pass  # Ignore cleanup errors
            
            response.close = lambda: cleanup_file(audio_path)
            return response
            
        return HttpResponseServerError('Error generating audio file')
            
    except Exception as e:
        messages.error(request, f'Error generating audio: {str(e)}')
        return HttpResponseServerError('Error generating audio file')

@login_required
def toggle_like(request, pk):
    if request.method == 'POST':
        blog = get_object_or_404(Blog, pk=pk)
        like, created = Like.objects.get_or_create(user=request.user, blog=blog)
        
        if not created:
            # User already liked the post, so unlike it
            like.delete()
            liked = False
        else:
            liked = True
        
        return JsonResponse({
            'liked': liked,
            'likeCount': blog.get_like_count()
        })
