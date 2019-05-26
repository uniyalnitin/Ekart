from django.contrib import admin
from .models import BillingAddress, StripeCustomer
# Register your models here.
admin.site.register(BillingAddress)
admin.site.register(StripeCustomer)
