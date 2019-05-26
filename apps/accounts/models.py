from django.db import models
from django.conf import settings
from psycopg2 import IntegrityError
from django_countries.fields import CountryField

# Create your models here.
class StripeCustomer(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=256)
    is_active = models.BooleanField(default=True)

    @classmethod
    def get_customer(cls, user):
        try:
            return StripeCustomer.objects.get(user= user, is_active=True)
        except IntegrityError:
            return None
        except:
            None

class BillingAddress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    street_address = models.CharField(max_length=100)
    apartment_address = models.CharField(max_length=100)
    country = CountryField(multiple=False)
    zip = models.CharField(max_length=100)

    class Meta:
        unique_together = ('user', 'country', 'zip')

    def __str__(self):
        return self.user.username
