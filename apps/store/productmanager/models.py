from django.db import models
from django.db.models import Min
# Create your models here.
from django.db import models
from django.shortcuts import reverse
from psycopg2 import IntegrityError

# Create your models here.
class Tag(models.Model):
    title = models.CharField(max_length=40, unique=True)
    
    def __str__(self):
        return self.title


class Category(models.Model):
    title = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return self.title


class Brand(models.Model):
    title = models.CharField(max_length=40, unique=True)

    def __str__(self):
        return self.title


class Product(models.Model):
    title = models.CharField(max_length=64)
    brand = models.ForeignKey(Brand, on_delete = models.CASCADE)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete= models.CASCADE)
    tags = models.ManyToManyField(Tag)
    image = models.ImageField()
    is_active = models.BooleanField(default=True)

    def add_product(self, price, quantity, color=None, size=None):
        try:
            return ProductInstance.objects.create(product=self, price=price, color=color, size=size)
        except IntegrityError:
            return None

    def get_product_instances(self):
        return ProductInstance.objects.filter(product=self, is_active=True).exclude(quantity=0)

    def get_min_price(self):
        qs = ProductInstance.objects.filter(product=self, is_active=True).aggregate(price_min=Min('price'))
        if qs['price_min']:
            return qs['price_min']
        return None
    
    def get_min_discount_price(self):
        qs = ProductInstance.objects.filter(product=self,is_active=True)\
                                        .exclude(discount_price=None)\
                                        .aggregate(price_min=Min('price'))
        if qs and qs['price_min']:
            return qs['price_min']
        return None
        
    def remove(self):
        self.is_active = False
        self.save()

    def get_absolute_url(self):
        return reverse('product_manager:detail',args=[self.id])

    def __str__(self):
        return self.title

class ProductInstance(models.Model):
    price = models.FloatField()
    discount_price = models.FloatField(null=True, blank=True)
    color = models.CharField(max_length=10, null=True, blank=True)
    size = models.CharField(max_length=10, null=True, blank=True)
    quantity = models.IntegerField()
    product = models.ForeignKey(Product, on_delete = models.CASCADE)
    is_active = models.BooleanField(default=True)

    @classmethod
    def get_by_id(cls, id):
        try:
            return cls.objects.get(id=id)
        except cls.DoesNotExist:
            return None

    @property
    def title(self):
        return self.product.title

    def remove(self):
        self.is_active = False
        self.save()

    def is_instock(self):
        return self.quantity>0 and self.is_active

    def get_latest_price(self):
        return self.discount_price if self.discount_price else self.price

    def set_price(self, price):
        self.price = price
        self.save()
    
    def set_discount_price(self, discount_price):
        self.discount_price = discount_price
        self.save()
    
    def get_add_to_cart_url(self):
        return reverse('store:add-to-cart', kwargs={
            'id': self.id
        })
    
    def get_remove_from_cart_url(self):
        return reverse("store:decrease_cart_product_quantity", kwargs={
            'id': self.id
        })
    
    def __str__(self):
        return '{},{},{},{}'.format(self.product.title, self.color, self.size, self.price)

    class Meta:
        ordering = ('discount_price', 'price',)

    class InactiveError(Exception):
        pass
