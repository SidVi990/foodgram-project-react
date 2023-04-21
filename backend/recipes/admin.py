from django.contrib.admin import ModelAdmin, TabularInline, register
from recipes.models import (
    Favorite,
    Ingredient,
    IngredientsAmount,
    Recipe,
    ShoppingCart,
    Tag,
)


@register(Ingredient)
class IngredientAdmin(ModelAdmin):

    list_display = (
        "pk",
        "name",
        "measurement_unit",
    )
    list_editable = ("name", "measurement_unit")
    search_fields = ("name",)


@register(Tag)
class TagAdmin(ModelAdmin):
    list_display = (
        "pk",
        "name",
        "color",
        "slug",
    )
    list_editable = ("name", "color", "slug")
    search_fields = ("name",)


class IngredientAmountInline(TabularInline):
    model = IngredientsAmount


@register(Recipe)
class RecipeAdmin(ModelAdmin):
    list_display = ("pk", "name", "author", "image", "favorites")
    exclude = ("ingredients",)
    inlines = (IngredientAmountInline,)
    list_filter = ("author", "name", "tags")
    search_fields = ("author__username", "name", "tags__name")

    def favorites(self, obj):
        return obj.favorites.count()

    favorites.short_description = 'Добавлен в избранное'


@register(IngredientsAmount)
class IngredientsAmountAdmin(ModelAdmin):
    list_display = ("id", "recipe", "ingredient", "amount")
    search_fields = ("recipe__name", "ingredient__name")


@register(Favorite)
class FavoriteAdmin(ModelAdmin):
    list_display = ("recipe", "user")


@register(ShoppingCart)
class ShoppingCartAdmin(ModelAdmin):
    list_display = ("recipe", "user")
