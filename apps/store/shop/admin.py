from django.contrib import admin
from .models import Cart, CartItem, Order, Refund, Payment
# Register your models here.
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Order)
admin.site.register(Refund)
admin.site.register(Payment)