from django.contrib import admin
from .models import Product, ProductInstance, Tag, Category, Brand
# Register your models here.

admin.site.register(Product)
admin.site.register(ProductInstance)
admin.site.register(Tag)
admin.site.register(Category)
admin.site.register(Brand)