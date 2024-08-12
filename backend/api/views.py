from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.http.response import HttpResponse

from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from django.db.models import Exists, OuterRef

from api import business_logic, models, pagination, permission, serializers
from api.filters import AuthorAndTagFilter
from api import const

User = get_user_model()


class FootGramUserViewSet(DjoserUserViewSet):
    pagination_class = pagination.LimitPage

    @action(["get", "put", "patch", "delete"], detail=False)
    def me(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                "Вы не авторизованы", status=status.HTTP_401_UNAUTHORIZED
            )
        return super().me(request, *args, **kwargs)

    @action(["post"], detail=True, permission_classes=[IsAuthenticated])
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, id=id)
        serializer = serializers.AuthorUserSerializer(
            data={"user": user.id, "author": author.id}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        user = request.user
        queryset = models.Follow.objects.filter(user=user)
        pages = self.paginate_queryset(queryset)
        serializer = serializers.FollowSerializer(
            pages,
            many=True,
            context={"limit": request.GET.get("recipes_limit")},
        )
        return self.get_paginated_response(serializer.data)

    @subscribe.mapping.delete
    def del_subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, id=id)
        if user == author:
            return Response(
                {"errors": "Вы не можете отписываться от самого себя"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        follow = models.Follow.objects.filter(user=user, author=author)
        if follow.exists():
            follow.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {"errors": "Вы уже отписались"}, status=status.HTTP_400_BAD_REQUEST
        )


class TagViewSet(ReadOnlyModelViewSet):
    queryset = models.Tag.objects.all()
    serializer_class = serializers.TagSerializer
    permission_classes = (permission.AdminChangeOrReadOnly,)


class IngredientViewSet(ReadOnlyModelViewSet):
    queryset = models.Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer
    permission_classes = (permission.AdminChangeOrReadOnly,)


class RecipeViewSet(ModelViewSet):
    serializer_class = serializers.RecipeSerializer
    pagination_class = pagination.LimitPage
    filter_class = AuthorAndTagFilter
    permission_classes = [permission.ForOwnerOrReadOnly]

    def get_queryset(self):
        queryset = models.Recipe.objects.select_related(
            "author"
        ).prefetch_related(
            "tags", "ingredients"
        )
        if self.request.user.is_anonymous:
            return queryset
        user = self.request.user
        queryset = queryset.annotate(
            is_in_shopping_cart=Exists(user.in_cart.filter(id=OuterRef('pk'))),
            is_favorited=Exists(user.favorites.filter(id=OuterRef('pk'))),
        )
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _delete_instance(self, request, model, pk):
        recipe = get_object_or_404(models.Recipe, id=pk)
        try:
            obj = model.objects.get(user=request.user, recipe=recipe)
        except ObjectDoesNotExist:
            raise ValidationError({"errors": "Рецепт не найден"})
        obj.delete()

    def _create_favorite_or_shop_cart(
        self, request, serializer_class, pk, model
    ):
        serializer = serializer_class(
            data={},
            context={"user": request.user, "recipe": pk, "model": model},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return serializer

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        serializer = self._create_favorite_or_shop_cart(
            request,
            serializer_class=serializers.FavoriteSerializer,
            pk=pk,
            model=models.Favorite,
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        self._delete_instance(request, models.Favorite, pk)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        serializer = self._create_favorite_or_shop_cart(
            request,
            serializer_class=serializers.CartRecipeSerializer,
            pk=pk,
            model=models.Cart,
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        self._delete_instance(request, models.Cart, pk)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False, methods=["get"], permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        user = self.request.user
        if not user.in_cart.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        filename = const.FILE_NAME.format(username=user.username)
        shopping_list = business_logic.get_list_for_shop(user)
        response = HttpResponse(
            shopping_list, content_type="text.txt; charset=utf-8"
        )
        response["Content-Disposition"] = f"attachment; filename={filename}"
        return response
