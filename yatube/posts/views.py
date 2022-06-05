from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post
from .utils import get_paginator_page_obj

User = get_user_model()
POSTS_PER_PAGE = 10


def index(request):
    post_list = Post.objects.select_related('group', 'author').all()
    page_number = request.GET.get('page')
    page_obj = get_paginator_page_obj(post_list, POSTS_PER_PAGE, page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('group', 'author').all()
    page_number = request.GET.get('page')
    page_obj = get_paginator_page_obj(posts, POSTS_PER_PAGE, page_number)

    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    following = False
    author = User.objects.get(username=username)

    if Follow.objects.filter(author=author).filter(user=request.user).exists():
        following = True

    user_posts = author.posts.select_related('author', 'group').all()
    page_number = request.GET.get('page')
    page_obj = get_paginator_page_obj(user_posts, POSTS_PER_PAGE, page_number)

    context = {
        'following': following,
        'author': author,
        'page_obj': page_obj
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related('group', 'author'), pk=post_id)
    comments = post.comments.select_related('author', 'post').all()
    is_author = False

    if post.author == request.user:
        is_author = True

    form = CommentForm(request.POST or None)

    if form.is_valid():
        form.save()
    context = {'post': post,
               'is_author': is_author,
               'form': form,
               'comments': comments}
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    is_edit = False
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        new_record = form.save(commit=False)
        new_record.author = request.user
        form.save()
        return redirect('posts:profile', request.user)
    return render(request,
                  'posts/create_post.html',
                  {'form': form, 'is_edit': is_edit})


def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    is_edit = True

    if request.user != post.author:
        return redirect('posts:post_detail', post_id)

    form = PostForm(
        instance=post,
        files=request.FILES or None,
        data=request.POST or None
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    return render(request,
                  'posts/create_post.html',
                  {'form': form, 'is_edit': is_edit})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related('group', 'author'), pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.select_related(
        'group', 'author').filter(author__following__user=request.user).all()

    page_number = request.GET.get('page')
    page_obj = get_paginator_page_obj(post_list, POSTS_PER_PAGE, page_number)

    context = {
        'page_obj': page_obj,
    }

    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user == author:
        return redirect('posts:profile', request.user.username)

    Follow.objects.create(user=request.user, author=author)
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    author = User.objects.get(username=username)
    if Follow.objects.filter(user=request.user).filter(author=author).exists():
        Follow.objects.filter(user=request.user).filter(author=author).delete()
    return redirect('posts:follow_index')
