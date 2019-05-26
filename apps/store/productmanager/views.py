from django.conf import settings
from django.db.models import Min
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, View
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.utils import timezone
from .models import Product, ProductInstance 
# Create your views here.

class ProductListView(ListView):
    model = Product

    template_name= 'products/home.html'

class ProductDetailView(View):
    
    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        product_instances = product.get_product_instances()
        min_priced_instance = product_instances[0] if product_instances else None
        return render(self.request, 'products/product.html',
                                    {'products':product_instances, 
                                    'mpp': min_priced_instance})
        