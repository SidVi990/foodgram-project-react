import json

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    """Загрузка списка игредиентов из json файла."""
    help = 'Loads data from ingredients.json'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Start'))
        with open('data/ingredients.json', encoding='utf-8',
                  ) as data_file_ingredients:
            ingredient_data = json.loads(data_file_ingredients.read())
            for ingredients in ingredient_data:
                Ingredient.objects.get_or_create(**ingredients)

        self.stdout.write(self.style.SUCCESS('Done'))
