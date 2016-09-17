# coding: utf-8
from django.core.paginator import Paginator
from django.forms.models import model_to_dict
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.utils import timesince

from .models import Category, CategoryTag, Post, Reply, Attachment
from .serializers import PostSerializer
from accounts.templatetags.users_tags import gravatar

from actstream.models import Action
from rest_framework import viewsets
import random
import datetime
import json
import bleach

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all().order_by('-created_at')
    serializer_class = PostSerializer

def post_list(request, category_id):
    category = Category.objects.get(pk=category_id)
    tags = CategoryTag.objects.filter(category=category)
    page_size = 50

    posts = Post.objects.approved().filter(category=category).order_by('-created_at')
    if request.GET.get('tag_id'):
        posts = posts.filter(tag_id=int(request.GET.get('tag_id')))

    paginator = Paginator(posts, page_size)
    page = request.GET.get('page', 1)
    try:
        page = int(page)
    except:
        page = 1
    posts = paginator.page(page)

    ctx = {
        'paginator': paginator,
        'tags': tags,
        'category': category,
        'posts': posts,
    }
    return TemplateResponse(request, 'posts/category.html', ctx)

def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    post.pageviews = post.pageviews + 1
    post.save()

    replies = Reply.objects.filter(post=post)

    # 暂时以修改verb的方式实现清除回帖提醒
    if request.user:
        notices = Action.objects.filter(actor_object_id=request.user.id, target_object_id=post.id).exclude(verb='read')
        notices.update(verb='read')

    if request.is_ajax():
        response = []
        for reply in replies:
            data = model_to_dict(reply)
            data['user'] = _serialize_user(data['author'])
            data['content'] = bleach.clean(data['content'], ['a',], strip=True)
            data['created_at'] = timesince.timesince(reply.created_at)
            response.append(data)
        return HttpResponse(json.dumps(response), content_type='application/json')

    ctx = {
        'category': post.category,
        'post': post,
        'tags': CategoryTag.objects.filter(category=post.category),
        'post_replies': replies,
    }

    return TemplateResponse(request, 'posts/detail.html', ctx)

@login_required
def create(request):
    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        if not category_id:
            category_id = 1
        category = Category.objects.get(pk=category_id)
        tag_id = request.POST.get('tag')
        title = request.POST.get('title')
        content = request.POST.get('content', '')

        post, is_create = Post.objects.get_or_create(title=title, content=content, category=category, tag_id=tag_id, author=request.user)
        post.save()

        return HttpResponseRedirect('/posts/%s/' % post.id)
    
    return HttpResponseRedirect('/')

@login_required
def edit(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Post, pk=post_id)
        if request.user == post.author:
            post.title = request.POST.get('title')
            post.content = request.POST.get('content')
            post.save()
        return HttpResponse(post.id)
    return HttpResponseRedirect('/')

@csrf_exempt
@login_required
def reply(request, post_id):
    if request.method == 'POST':
        reply = Reply()
        reply.post = Post.objects.get(pk=post_id)
        reply.author = request.user
        reply.content = request.POST.get('content')
        reply.save()

        response = model_to_dict(reply)
        response['user'] = _serialize_user(response['author'])
        return HttpResponse(json.dumps(response), content_type='application/json')
    else:
        try:
            reply_id = int(request.GET.get('reply_id'))
        except TypeError:
            return HttpResponse(json.dumps({'errorMessage': '获取回复内容失败，reply_id错误'}), content_type='application/json')

        reply = Reply.objects.get(pk=reply_id)
        response = model_to_dict(reply)
        response['user'] = _serialize_user(reply.author.id)

        return HttpResponse(json.dumps(response), content_type='application/json')

def _serialize_user(user_id):
    user = User.objects.get(pk=user_id)
    return {
        'username': user.username,
        'id': user.id,
        'gravatar': gravatar(user.email),
    }

def delete(request):
    object_id = request.GET.get('object_id')
    if request.GET.get('type').lower() == 'post':
        model = Post
    else:
        model = Reply

    row = model.objects.get(pk=object_id)
    response = {}
    if request.user.id == row.author.id:
        row.delete()
        response['status'] = 'ok'
    else:
        response['errorMessage'] = '没有删除权限'

    return HttpResponse(json.dumps(response), content_type='application/json')

def upload(request):
    today = datetime.datetime.today()
    upfile = request.FILES.get('upfile', '')

    file_type = str(upfile.name).split('.')[-1].lower()
    file_name = str(today.strftime("%Y%m%d%H-%f")) + '.' + file_type
    upfile.name = file_name
    attachment = Attachment.objects.create(user=request.user, src=upfile)
    return HttpResponse(attachment.src.url)

def search(request):
    if request.GET.get('q'):
        q = request.GET.get('q')
        posts = []
        for post in Post.objects.filter(title__contains=q):
            url = post.get_absolute_url()
            post = model_to_dict(post)
            post['url'] = url
            posts.append(post)
        
        response = {"status" : "ok", "data": posts}
        return HttpResponse(json.dumps(response), content_type='application/json')
