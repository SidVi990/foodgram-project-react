from rest_framework.pagination import PageNumberPagination


class PageLimitPagination(PageNumberPagination):
    """Стандартный пагинатор с переопределённым названием поля,
    отвечающего за количество результатов в выдаче"""
    page_size_query_param = 'limit'
