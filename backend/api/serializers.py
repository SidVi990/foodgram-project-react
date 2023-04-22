from django.contrib.auth import get_user_model
from django.db.models import F
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.models import Ingredient, IngredientsAmount, Recipe, Tag
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

# from users.models import Subscribe

User = get_user_model()


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения коротокой информации о рецепте.
    Необходим для части эндпоинтов."""
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('__all__',)


class CustomUserCreateSerializer(UserCreateSerializer):
    """Кастомный сериализатор для регистрации пользователя."""
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password'
        )

    def validate_username(self, value):
        """Запрещаем создание пользователя с именем 'me'."""
        if value.lower() == ('me'):
            raise ValidationError('Не корректное имя пользователя')
        return value


class CustomUserSerializer(UserSerializer):
    """Кастомный сериализатор пользователя."""
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta(UserSerializer.Meta):
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        """Получаем данные о подписках пользователя."""
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.follower.exists()


class SubscribeSerializer(CustomUserSerializer):
    """Сериализатор для подписок пользователя."""
    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)

    class Meta(CustomUserSerializer.Meta):
        fields = CustomUserSerializer.Meta.fields + (
            'recipes', 'recipes_count'
        )

    def get_recipes(self, obj):
        """Получаем информацию о рецептах автора."""
        request = self.context.get('request')
        context = {'request': request}
        recipe_limit = request.query_params.get('recipe_limit')
        queryset = obj.recipes.all()
        if recipe_limit:
            queryset = queryset[: int(recipe_limit)]
        return RecipeShortSerializer(queryset, context=context, many=True).data

    def get_recipes_count(self, obj):
        """Получаем данные об общем количестве рецептов автора."""
        return obj.recipes.count()


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тэгов"""
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов"""
    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализато для рецептов"""
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_ingredients(self, recipe):
        """Получаем данные о ингредиентах для рецепта."""
        ingredients = recipe.ingredients.values(
            'id', 'name', 'measurement_unit', amount=F('recipe__amount')
        )
        return ingredients

    def get_is_favorited(self, obj):
        """Проверяем находится ли рецепт в избранном у пользователя."""
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return user.favorites.filter(recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        """Проверяем находится ли рецепт в корзине у пользователя."""
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.shopping_cart.filter(recipe=obj).exists()

    def validate(self, attrs):
        """Проверяем корректность вводных данных."""
        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': 'Для приготовления блюда нужны ингредиенты'}
            )
        ingredient_set = set()
        for ingredient_item in ingredients:
            ingredient = get_object_or_404(Ingredient,
                                           id=ingredient_item['id'])
            if ingredient in ingredient_set:
                raise serializers.ValidationError(
                    'Ингредиенты не должны повторяться!'
                )
            ingredient_set.add(ingredient)
            amount = int(ingredient_item['amount'])
            if amount <= 0 or amount >= 32000:
                raise serializers.ValidationError({
                    'ingredients': ('Количество ингредиентов '
                                    'должно быть в диапазоне от 1 до 31999!')
                })
        attrs['ingredients'] = ingredients
        return attrs

    def create_ingredients(self, ingredients, recipe):
        """Добавляем ингредиенты в рецепт."""
        IngredientsAmount.objects.bulk_create(
            [IngredientsAmount(
                ingredient=Ingredient.objects.get(id=ingredient['id']),
                recipe=recipe,
                amount=ingredient['amount']
            ) for ingredient in ingredients]
        )

    def create(self, validated_data):
        """Создаём рецепт."""
        image = validated_data.pop('image')
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(image=image, **validated_data)
        tags_data = self.initial_data.get('tags')
        recipe.tags.set(tags_data)
        self.create_ingredients(ingredients_data, recipe)
        return recipe

    def update(self, instance, validated_data):
        """Обновляем рецепт."""
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        instance.tags.clear()
        tags_data = self.initial_data.get('tags')
        instance.tags.set(tags_data)
        IngredientsAmount.objects.filter(recipe=instance).all().delete()
        self.create_ingredients(validated_data.get('ingredients'), instance)
        instance.save()
        return instance
