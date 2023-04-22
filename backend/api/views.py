import io

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from users.models import Subscribe

from recipes.models import (Favorite, Ingredient, IngredientsAmount, Recipe,
                            ShoppingCart, Tag)
from .filters import FilterIngredient, FilterRecipe
from .pagination import PageLimitPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (CustomUserSerializer, IngredientSerializer,
                          RecipeSerializer, RecipeShortSerializer,
                          SubscribeSerializer, TagSerializer)

User = get_user_model()

BEGIN_POSITION_X = 40
BEGIN_POSITION_Y = 750
POSITION_Y = 790
SPACING = 30
FONT_SIZE = 11
FONT_SIZE_HEADER = 14


class CustomUserViewSet(UserViewSet):
    """Кастомный вьюсет для работы с пользователем."""
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = PageLimitPagination

    def get_permissions(self):
        """Определяем уровень доступа."""
        if self.action == 'me':
            self.permission_classes = (IsAuthenticated,)
        return super().get_permissions()

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
    )
    def subscribe(self, request, id):
        """Создаем или удаляем подписку на автора."""
        user = request.user
        author = get_object_or_404(User, id=id)
        subscription = Subscribe.objects.filter(user=user, author=author)

        if request.method == 'POST':
            if subscription.exists():
                return Response(
                    {'error': 'Вы уже подписаны'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if user == author:
                return Response(
                    {'error': 'Невозможно подписаться на себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = SubscribeSerializer(
                author, context={'request': request}
            )
            Subscribe.objects.create(user=user, author=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if subscription.exists():
                subscription.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'error': 'Вы не подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        """Получаем данные о подписках пользователя."""
        user = request.user
        follows = User.objects.filter(following__user=user)
        page = self.paginate_queryset(follows)
        serializer = SubscribeSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = FilterIngredient
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для тэгов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для рецептов."""
    queryset = Recipe.objects.all()
    pagination_class = PageLimitPagination
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthorOrReadOnly,)
    add_serializer = RecipeShortSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = FilterRecipe

    def perform_create(self, serializer):
        """При создании рецепта указываем автором текущего пользоваетля."""
        serializer.save(author=self.request.user)

    def to_add_or_delete(self, model, pk):
        """Метод создания или удаления связи."""
        recipe = get_object_or_404(Recipe, pk=pk)
        user = self.request.user

        if self.request.method == 'POST':
            if model.objects.filter(user=user, recipe__id=pk).exists():
                return Response(
                    {'errors': 'Рецепт уже добавлен!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            recipe = get_object_or_404(Recipe, id=pk)
            model.objects.create(user=user, recipe=recipe)
            serializer = RecipeShortSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if self.request.method == 'DELETE':
            obj = model.objects.filter(user=user, recipe__id=pk)
            if obj.exists():
                obj.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'errors': 'Рецепт уже удален!'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(methods=['POST', 'DELETE'], detail=True, pagination_class=None)
    def favorite(self, request, pk):
        """Добавляем рецепт в избранное."""
        return self.to_add_or_delete(Favorite, pk)

    @action(methods=['POST', 'DELETE'], detail=True, pagination_class=None)
    def shopping_cart(self, request, pk):
        """Добавляем рецепт в корзину."""
        return self.to_add_or_delete(ShoppingCart, pk)

    @action(
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Скачиваем pdf файл со списком ингредиентов из корзины."""
        global BEGIN_POSITION_Y
        buffer = io.BytesIO()
        shopping_cart = IngredientsAmount.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))
        ingredients = {}
        for recipe in shopping_cart:
            name = recipe['ingredient__name']
            amount = recipe['amount']
            measurement_unit = recipe['ingredient__measurement_unit']
            if name in ingredients:
                ingredients[name]['amount'] = (
                    ingredients[name]['amount'] + amount
                )
            else:
                ingredients[name] = {
                    'measurement_unit': measurement_unit,
                    'amount': amount,
                }
        page = canvas.Canvas(buffer, pagesize=A4)
        pdfmetrics.registerFont(TTFont('FreeSans', 'data/FreeSans.ttf'))
        page.setFont('FreeSans', FONT_SIZE_HEADER)
        page.setTitle('Список покупок')
        page.drawString(
            BEGIN_POSITION_X,
            POSITION_Y,
            f'Список покупок для {request.user.get_full_name()}:'
        )
        page.setFont('FreeSans', FONT_SIZE)
        for key, values in ingredients.items():
            page.drawString(
                BEGIN_POSITION_X,
                BEGIN_POSITION_Y,
                f'{key.capitalize()} - '
                f'{values["amount"]} '
                f'{values["measurement_unit"]}.'
            )
            BEGIN_POSITION_Y -= SPACING
        page.showPage()
        page.save()
        buffer.seek(0)
        return FileResponse(
            buffer, as_attachment=True, filename='shopping-list.pdf'
        )
