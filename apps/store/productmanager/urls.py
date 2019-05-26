from django.urls import path
from .views import (
                    ProductListView,
                    ProductDetailView,
                )

app_name = 'product_manager'

urlpatterns = [
    path('', ProductListView.as_view(), name='list'),
    path('<pk>/', ProductDetailView.as_view(), name='detail')
]