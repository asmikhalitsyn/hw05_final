from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.cache import cache_page

from .forms import PostForm, CommentForm
from .models import Post, Group, User, Follow
from .settings import POSTS_PER_PAGE

CACHE_TIME = 20


def page_paginator(posts, count_pages, request):
    return Paginator(posts, count_pages).get_page(request.GET.get('page'))


@cache_page(CACHE_TIME, key_prefix='index_page')
def index(request):
    return render(request, 'posts/index.html', {
        'page_obj': page_paginator(Post.objects.all(), POSTS_PER_PAGE, request)
    })


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    return render(request, 'posts/group_list.html', {
        'group': group,
        'page_obj': page_paginator(group.posts.all(), POSTS_PER_PAGE, request)
    })


def profile(request, username):
    author = get_object_or_404(User, username=username)
    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user,
            author=author).exists()
    return render(request, 'posts/profile.html', {
        'following': following,
        'author': author,
        'page_obj': page_paginator(
            author.posts.select_related('group'), POSTS_PER_PAGE, request
        )})


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all()
    form = CommentForm()
    return render(request, 'posts/post_detail.html', {
        'post': get_object_or_404(Post, pk=post_id),
        'form': form,
        'comments': comments
    })


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', username=str(request.user))


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post.id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if not form.is_valid():
        return render(
            request,
            'posts/create_post.html',
            {'form': form, 'is_edit': True}
        )
    form.save()
    return redirect('posts:post_detail', post_id=post.id)


@login_required
def follow_index(request):
    return render(request, 'posts/follow.html', {'page_obj': page_paginator(
        Post.objects.filter(author__following__user=request.user),
        POSTS_PER_PAGE,
        request
    )})


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(user=user, author=author)
    if user != author and follow.count() == 0:
        Follow.objects.create(user=user, author=author)
    return redirect('posts:profile', username=author)


@login_required
def profile_unfollow(request, username):
    get_object_or_404(Follow,
                      user=request.user,
                      author__username=username).delete()
    return redirect('posts:profile', username=username)
