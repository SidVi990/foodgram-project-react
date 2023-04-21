from django.db.models import BooleanField, ExpressionWrapper, Q
from django_filters.rest_framework import FilterSet, filters
from recipes.models import Ingredient, Recipe, Tag


class FilterRecipe(FilterSet):
    """Фильтация рецептов в соответствии с параметрами запроса."""
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )

    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('tags', 'author',)

    def filter_is_favorited(self, queryset, name, value):
        """Фильтруем по добавлению в избранное."""
        user = self.request.user
        if value and not user.is_anonymous:
            return queryset.filter(favorites__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Фильтруем по добавлению в корзину."""
        user = self.request.user
        if value and not user.is_anonymous:
            return queryset.filter(shopping_cart__user=user)
        return queryset


class FilterIngredient(FilterSet):
    """Фильтация ингредиентов в соответствии с параметрами запроса."""
    name = filters.CharFilter(method='name_filter')

    class Meta:
        model = Ingredient
        fields = ('name',)

    def name_filter(self, queryset, name, value):
        """Фильтруем название по вхождению в начало
        и по вхождению в произвольном месте названия."""
        return queryset.filter(
            Q(name__istartswith=value) | Q(name__icontains=value)
        ).annotate(
            startswith=ExpressionWrapper(
                Q(name__istartswith=value),
                output_field=BooleanField()
            )
        ).order_by('-startswith')
