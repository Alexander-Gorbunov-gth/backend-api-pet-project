from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F

from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from api import models, validators

User = get_user_model()


class FoodgramUserCreateSerializer(UserCreateSerializer):

    class Meta:
        model = models.FootgramUser
        fields = (
            "email",
            "id",
            "password",
            "username",
            "first_name",
            "last_name",
        )


class FoodgramUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = models.FootgramUser
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
        )

    def get_is_subscribed(self, obj):
        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return models.Follow.objects.filter(user=user, author=obj.id).exists()


class CartOrFavoriteerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="recipe.id")
    image = Base64ImageField(read_only=True, source="recipe.image")
    name = serializers.ReadOnlyField(source="recipe.name")
    cooking_time = serializers.ReadOnlyField(source="recipe.cooking_time")

    def validate(self, data):
        user = self.context.get("user")
        recipe_id = self.context.get("recipe")
        models_for_valid = self.context.get("model")
        try:
            recipe = models.Recipe.objects.get(id=recipe_id)
        except ObjectDoesNotExist:
            raise serializers.ValidationError({"recipe": "Рецепт не найден"})
        if models_for_valid.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                {"errors": "Рецепт уже добавлен в список"}
            )
        data["user"] = user
        data["recipe"] = recipe
        return data


class CartRecipeSerializer(CartOrFavoriteerializer):

    class Meta:
        model = models.Cart
        fields = ("id", "name", "image", "cooking_time")
        read_only_fields = ("id", "name", "image", "cooking_time")


class FavoriteSerializer(CartOrFavoriteerializer):

    class Meta:
        model = models.Favorite
        fields = ("id", "name", "image", "cooking_time")


class CropRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Recipe
        fields = ("id", "name", "image", "cooking_time")


class FollowSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="author.id")
    email = serializers.ReadOnlyField(source="author.email")
    username = serializers.ReadOnlyField(source="author.username")
    first_name = serializers.ReadOnlyField(source="author.first_name")
    last_name = serializers.ReadOnlyField(source="author.last_name")
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = models.Follow
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )

    def get_is_subscribed(self, obj):
        return models.Follow.objects.filter(
            user=obj.user, author=obj.author
        ).exists()

    def get_recipes(self, obj):
        limit = self.context.get("limit")
        queryset = models.Recipe.objects.filter(author=obj.author)
        if limit:
            queryset = queryset[: int(limit)]
        return CropRecipeSerializer(queryset, many=True).data

    def get_recipes_count(self, obj):
        return models.Recipe.objects.filter(author=obj.author).count()

    def create(self, validated_data):
        user = self.context["user"]
        author = self.context["author"]
        follow = models.Follow.objects.create(user=user, author=author)
        return follow


class AuthorUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Follow
        fields = ("user", "author")

    def validate(self, data):
        user = data["user"]
        author = data["author"]
        if user == author:
            raise serializers.ValidationError(
                {"error": "Вы не можете подписываться на самого себя"}
            )
        if models.Follow.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError(
                {"error": "Вы уже подписаны на этого пользователя"}
            )
        return data

    def to_representation(self, instance):
        serializer = FollowSerializer(instance)
        return serializer.data


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Tag
        fields = "__all__"
        read_only_fields = ("__all__",)


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Ingredient
        fields = "__all__"
        # read_only_fields = ("__all__",)


class AmountIngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit"
    )

    class Meta:
        model = models.AmountIngredientInRecipe
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField(validators=[validators.NotNullVAlidator()])
    tags = TagSerializer(read_only=True, many=True)
    author = FoodgramUserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = models.Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def get_ingredients(self, recipe):
        ingredients = recipe.ingredients.values(
            "id", "name", "measurement_unit", amount=F("recipe__amount")
        )
        return ingredients

    def get_is_favorited(self, obj):
        user = self.context.get("request").user
        if user.is_authenticated:
            return obj.is_favorited
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get("request").user
        if user.is_authenticated:
            return obj.is_in_shopping_cart
        return False

    def validate(self, data):
        ingredients = self.initial_data.get("ingredients")
        tags = self.initial_data.get("tags")
        validator = validators.RecipeValidator()
        validator.tag_validation(models.Tag, tags)
        validator.ingredient_validation(models.Ingredient, ingredients)
        data["ingredients"] = ingredients
        data["tags"] = tags
        return data

    def set_ingredients(self, recipe, ingredients_data):
        ingredient_list = []
        for ingredient in ingredients_data:
            ingredient_list.append(
                models.AmountIngredientInRecipe(
                    recipe=recipe,
                    ingredients=get_object_or_404(
                        models.Ingredient, pk=ingredient.get("id")
                    ),
                    amount=ingredient.get("amount"),
                )
            )
        models.AmountIngredientInRecipe.objects.bulk_create(ingredient_list)

    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        tags = validated_data.pop("tags")
        recipe = models.Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.set_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags")
        ingredients_data = validated_data.pop("ingredients")
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        instance.tags.clear()
        instance.tags.set(tags)
        models.AmountIngredientInRecipe.objects.filter(
            recipe=instance
        ).all().delete()
        self.set_ingredients(instance, ingredients_data)
        return instance
