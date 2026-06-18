from django.db import transaction as db_transaction
from rest_framework.generics import GenericAPIView, ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import serializers

from api.models import CommunityPost, CommunityPostLike


class CommunityPostSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)
    liked_by_me = serializers.SerializerMethodField()

    class Meta:
        model = CommunityPost
        fields = ['id', 'title', 'body', 'author_username', 'created_at', 'likes', 'liked_by_me']
        read_only_fields = ['id', 'author_username', 'created_at', 'likes', 'liked_by_me']

    def get_liked_by_me(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return CommunityPostLike.objects.filter(post=obj, user=request.user).exists()
        return False


class CommunityPostListView(GenericAPIView):
    """GET: list approved posts. POST: create a post (pending admin approval)."""
    permission_classes = [IsAuthenticated]
    serializer_class = CommunityPostSerializer

    def get(self, request, *args, **kwargs):
        posts = CommunityPost.objects.filter(is_approved=True)
        serializer = CommunityPostSerializer(posts, many=True, context={'request': request})
        return Response({'status': 'success', 'data': serializer.data})

    def post(self, request, *args, **kwargs):
        title = request.data.get('title', '').strip()
        body = request.data.get('body', '').strip()
        if not title or not body:
            return Response({'status': 'error', 'message': 'title and body are required'}, status=400)
        post = CommunityPost.objects.create(author=request.user, title=title, body=body)
        return Response({
            'status': 'success',
            'message': 'Post submitted and awaiting admin approval.',
            'data': CommunityPostSerializer(post, context={'request': request}).data,
        }, status=201)


class CommunityPostLikeView(GenericAPIView):
    """POST: toggle like on a post."""
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id, *args, **kwargs):
        try:
            post = CommunityPost.objects.get(id=post_id, is_approved=True)
        except CommunityPost.DoesNotExist:
            return Response({'status': 'error', 'message': 'Post not found'}, status=404)

        with db_transaction.atomic():
            like, created = CommunityPostLike.objects.get_or_create(post=post, user=request.user)
            if created:
                CommunityPost.objects.filter(id=post_id).update(likes=post.likes + 1)
                action = 'liked'
            else:
                like.delete()
                CommunityPost.objects.filter(id=post_id).update(likes=max(post.likes - 1, 0))
                action = 'unliked'

        post.refresh_from_db()
        return Response({'status': 'success', 'action': action, 'likes': post.likes})
