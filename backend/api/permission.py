from django.contrib.auth import get_user_model

from rest_framework import serializers
from rest_framework.permissions import SAFE_METHODS, BasePermission

from api.models import Follow

User = get_user_model()


class AdminChangeOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or request.method in SAFE_METHODS


class ForOwnerOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return (
            request.method in SAFE_METHODS
        ) or request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or obj.author == request.user


def check_subscription(author, user):
    if user == author:
        raise serializers.ValidationError(
            {"error": "Вы не можете подписываться на самого себя"}
        )
    if Follow.objects.filter(user=user, author=author).exists():
        raise serializers.ValidationError(
            {"error": "Вы уже подписаны на этого пользователя"}
        )
