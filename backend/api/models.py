from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from colorfield.fields import ColorField

from api import const


class FootgramUser(AbstractUser):
    username = models.CharField(
        "Юзернейм",
        max_length=const.MAX_LEN_USER_CHARFIELD,
        unique=True,
        validators=(
            RegexValidator(
                regex=r"^[\w.@+-]+$",
                message="Недопустимый символ в имени пользователя",
            ),
        ),
    )
    email = models.EmailField(
        "Адрес электронной почты",
        max_length=const.MAX_LEN_EMAIL,
        unique=True,
    )
    first_name = models.CharField(
        "Имя",
        max_length=const.MAX_LEN_USER_CHARFIELD,
    )
    last_name = models.CharField(
        "Фамилия",
        max_length=const.MAX_LEN_USER_CHARFIELD,
    )
    password = models.CharField(
        "Пароль",
        max_length=const.MAX_LEN_USER_CHARFIELD,
    )
    is_active = models.BooleanField(
        "Активирован",
        default=True,
    )
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ("username",)

    def __str__(self):
        return self.username


class Follow(models.Model):
    user = models.ForeignKey(
        FootgramUser,
        on_delete=models.CASCADE,
        related_name="follower",
        verbose_name="Подписчик",
    )
    author = models.ForeignKey(
        FootgramUser,
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name="Автор",
    )

    class Meta:
        ordering = ["-id"]
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "author"],
                name="unique follow",
            )
        ]

    def __str__(self):
        return self.user.username


class Tag(models.Model):
    name = models.CharField(
        verbose_name="Название тэга",
        max_length=const.MAX_LEN_TAG_NAME,
        unique=True,
    )
    color = ColorField(
        verbose_name="Цветовой код тэга",
        max_length=const.MAX_LEN_TAG_COLOUR,
        unique=True,
    )
    slug = models.CharField(
        verbose_name="Слаг тэга",
        max_length=const.MAX_LEN_TAG_SLUG,
        validators=(
            RegexValidator(
                regex=r"^[-a-zA-Z0-9_]+$",
                message="Недопустимый символ в slug тэга",
            ),
        ),
        unique=True,
    )

    class Meta:
        verbose_name = "Тэг"
        verbose_name_plural = "Тэги"
        ordering = ("name",)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        verbose_name="Ингридиент",
        max_length=const.MAX_LEN_INGREDIENT_CHARFIELD,
    )
    measurement_unit = models.CharField(
        verbose_name="Единицы измерения",
        max_length=const.MAX_LEN_INGREDIENT_CHARFIELD,
    )

    class Meta:
        verbose_name = "Ингридиент"
        verbose_name_plural = "Ингридиенты"
        ordering = ("name",)

    def __str__(self):
        return f"{self.name}, {self.measurement_unit}"


class Recipe(models.Model):
    name = models.CharField(
        verbose_name="Название блюда",
        max_length=const.MAX_LEN_RECIPES_CHARFIELD,
    )
    author = models.ForeignKey(
        FootgramUser,
        verbose_name="Автор рецепта",
        related_name="recipes",
        on_delete=models.SET_NULL,
        null=True,
    )
    tags = models.ManyToManyField(
        Tag, verbose_name="Тег", related_name="recipes"
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name="Ингредиенты блюда",
        related_name="recipes",
        through="AmountIngredientInRecipe",
    )
    pub_date = models.DateTimeField(
        verbose_name="Дата публикации",
        auto_now_add=True,
        editable=False,
    )
    image = models.ImageField(
        verbose_name="Изображение блюда",
        upload_to="picture_for_recipe/",
    )
    text = models.TextField(verbose_name="Описание блюда")
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name="Время приготовления",
        validators=(
            MinValueValidator(
                const.MIN_TIME_FOR_RECIPE,
                "Время приготовления слишком маленькое",
            ),
        ),
    )

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ("-pub_date",)

    def __str__(self):
        return f"{self.name}. Автор: {self.author.username}"


class AmountIngredientInRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="В каких рецептах",
        related_name="ingredient",
    )
    ingredients = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name="Связанные ингредиенты",
        related_name="recipe",
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name="Количество",
        validators=(
            MinValueValidator(
                const.MIN_AMOUNT,
                "Ошибка количества ингредиентов",
            ),
        ),
    )

    class Meta:
        verbose_name = "Ингридиент"
        verbose_name_plural = "Количество ингридиентов"
        ordering = ("recipe",)

    def __str__(self):
        return f"{self.amount} {self.ingredients}"


class CartFavoriteModel(models.Model):
    user = models.ForeignKey(
        FootgramUser,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
    )

    class Meta:
        abstract = True
        ordering = ["-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"], name="%(class)s_unique_user"
            )
        ]

    def __str__(self):
        return self.user.username


class Cart(CartFavoriteModel):

    class Meta(CartFavoriteModel.Meta):
        verbose_name = "Корзина"
        verbose_name_plural = "В корзине"
        default_related_name = "in_cart"


class Favorite(CartFavoriteModel):

    class Meta(CartFavoriteModel.Meta):
        verbose_name = "Избранное"
        verbose_name_plural = "Избранные"
        default_related_name = "favorites"
