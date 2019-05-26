from django.urls import path, include
from .views import (
                add_to_cart,
                decrease_cart_product_quantity,
                CartSummaryView,
                remove_from_cart,
                CheckoutView,
                PaymentView,
                payment_webhook,
                payment_success,
                payment_failed,
            )
app_name= 'store'

urlpatterns = [
    path('add-to-cart/<id>', add_to_cart, name='add-to-cart'),
    path('remove-from-cart/<id>',remove_from_cart, name='remove-from-cart'),
    path('decrease-cart-product-quantity/<id>', decrease_cart_product_quantity, name='decrease_cart_product_quantity'),
    path('cart-summary', CartSummaryView.as_view(), name='cart-summary'),
    path('checkout', CheckoutView.as_view(), name='checkout'),
    path('payment/<payment_option>', PaymentView.as_view(), name='payment'),
    path('payment-webhook',payment_webhook, name='payment-webhook'),
    path('payment-success', payment_success, name='payment_success'),
    path('payment-failed', payment_failed, name='payment-failed'),
]