from django.db import models
from psycopg2 import IntegrityError
from django.utils import timezone
from apps.accounts.models import BillingAddress
from django.conf import settings
from apps.store.productmanager.models import Product, ProductInstance
# from apps.store.transactionmanager.models import Payment

# Create your models here.

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    address = models.ForeignKey(BillingAddress, on_delete=models.CASCADE, null=True, blank=True)
    payment = models.OneToOneField('Payment', on_delete = models.CASCADE, null=True, blank=True)
    is_ordered = models.BooleanField(default=False)
    is_deleted= models.BooleanField(default=False)

    @classmethod
    def get_order(cls, user):
        try:
            return cls.objects.get_or_create(user=user, is_ordered=False, is_deleted=False)
        except IntegrityError:
            return None

    @classmethod
    def get_completed_orders(cls, user):
        return cls.objects.filter(user=user, is_ordered=True, is_deleted=False)
    
    @classmethod
    def get_all_orders(cls, user):
        return cls.objects.filter(user=user)

    def get_items(self):
        return CartItem.objects.filter(order=self)

    def calculate_net(self):
        amt = 0
        for item in self.get_items():
            amt += item.calculate_net()
        return amt


class Refund(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    reason = models.TextField()
    accepted = models.BooleanField()
    email = models.EmailField(max_length=64)


class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    billing_address= models.ForeignKey(BillingAddress, on_delete=models.CASCADE, null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    payment_intent_id = models.CharField(max_length=256, null=True, blank= True)
    
    @classmethod
    def get_cart(cls, user):
        try:
            return cls.objects.get_or_create(user= user, is_active=True)
        except IntegrityError:
            return None

    def update_modified(self):
        self.modified_on = timezone.now()
        self.save()

    def clear_cart(self):
        self.is_active = False
        self.save()

    def add_product(self, product_instance:ProductInstance, quantity:int):
        order, created = Order.get_order(self.user)
        try:
            c = CartItem.objects.get(product_instance=product_instance, cart= self)
            c.order = order
            c.quantity += quantity
            self.update_modified()
            c.save()
        except CartItem.DoesNotExist:
            if product_instance.is_active:
                CartItem.objects.create(product_instance=product_instance, cart= self, quantity= quantity, order= order)
            else:
                raise product_instance.InactiveError("Product is no longer available")

    def decrease_product_quantity(self, product_instance):
        try:
            qty = 0
            c = CartItem.objects.get(product_instance=product_instance, cart=self)
            if c.quantity >=1:
                c.quantity -= 1
                qty = c.quantity
                c.save()
            else:
                c.delete()
            self.update_modified()
            return qty
        except:
            return 0

    def remove_product(self, product_instance):
        try:
            c = CartItem.objects.get(product_instance=product_instance, cart=self)
            c.delete()
            self.update_modified()
            return True
        except CartItem.DoesNotExist:
            return True

    def get_items(self):
        return CartItem.objects.filter(cart=self)

    def calculate_net(self):
        amt = 0
        for item in self.get_items():
            amt += item.calculate_net()
        return amt
    
    def quantity_in_cart(self,product_instance:ProductInstance):
        try:
            return CartItem.objects.get(cart=self, product_instance=product_instance).quantity
        except CartItem.DoesNotExist:
            return 0


class CartItem(models.Model):
    product_instance = models.OneToOneField(ProductInstance, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, on_delete= models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    order = models.ForeignKey(Order, on_delete= models.CASCADE, null=True, blank=True)

    def calculate_net(self):
        return self.quantity * self.product_instance.get_latest_price()

    @property
    def price(self):
        return self.product_instance.price

    
    @property
    def title(self):
        return self.product_instance.title

    @property
    def discount_price(self):
        return self.product_instance.discount_price

class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = (
        ('initiated','Initiated'),
        ('pending', 'Pending'),
        ('failed', 'Failed')
    )

    stripe_charge_id = models.CharField(max_length=64)
    amount = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices = PAYMENT_STATUS_CHOICES, default='initiated')
    is_success = models.BooleanField(default=False)

    def __str__(self):
        return '{}-{}'.format(self.user.first_name, self.stripe_charge_id)