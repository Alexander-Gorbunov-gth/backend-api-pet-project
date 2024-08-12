from django.urls import include, path

from rest_framework.routers import DefaultRouter

from api import views

router = DefaultRouter()
router.register("users", views.FootGramUserViewSet)
router.register("tags", views.TagViewSet, "tags")
router.register("ingredients", views.IngredientViewSet, "ingredients")
router.register("recipes", views.RecipeViewSet, "recipes")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include("djoser.urls.authtoken")),
]
