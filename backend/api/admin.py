from django.contrib import admin

from api import models


class TagAdmin(admin.ModelAdmin):
    search_fields = ("name",)


class IngredientAdmin(admin.ModelAdmin):
    list_filter = ("name",)


class RecipeAdmin(admin.ModelAdmin):
    list_display = ("name", "author", "count_favorites")
    list_filter = ("author", "name", "tags")

    def count_favorites(self, obj):
        return obj.favorites.count()


class FootgramUserAdmin(admin.ModelAdmin):
    search_fields = ("username", "email")


admin.site.register(models.Tag, TagAdmin)
admin.site.register(models.Ingredient, IngredientAdmin)
admin.site.register(models.Recipe, RecipeAdmin)
admin.site.register(models.Cart)
admin.site.register(models.Favorite)
admin.site.register(models.FootgramUser, FootgramUserAdmin)
admin.site.register(models.Follow)
