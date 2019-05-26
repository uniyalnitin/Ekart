from django.shortcuts import render, redirect, reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import View, ListView
from django.http import HttpResponse
from django.conf import settings
from apps.accounts.models import BillingAddress, StripeCustomer
from apps.store.productmanager.models import ProductInstance

from .models import Cart, CartItem, Order,Payment
from .forms import CheckoutForm

import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY
end_point_secret = settings.WEBHOOK_SECRET
# Create your views here.

class CartSummaryView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        cart, created = Cart.get_cart(request.user)
        cart_items = cart.get_items()
        context = {
            'cart': cart
        }
        return render(self.request, 'order_summary.html', context)

@login_required
def add_to_cart(request, id):
    product_instance = ProductInstance.get_by_id(id)
    if product_instance:
        cart, created = Cart.get_cart(request.user)
        cart.add_product(product_instance,1)
        # import pdb;pdb.set_trace()
        return redirect(reverse('store:cart-summary'))

@login_required
def remove_from_cart(request, id):
    product_instance = ProductInstance.get_by_id(id)
    if product_instance:
        cart, created = Cart.get_cart(request.user)
        cart.remove_product(product_instance)
        return redirect(reverse('store:cart-summary'))

@login_required
def decrease_cart_product_quantity(request, id):
    product_instance = ProductInstance.get_by_id(id)
    if product_instance:
        cart, created = Cart.get_cart(request.user)
        cart.decrease_product_quantity(product_instance)
        return redirect(reverse('store:cart-summary'))

class CheckoutView(View, LoginRequiredMixin):

    def get(self, request):
        try:
            # order = Order.objects.get(user= self.request.user, is_ordered= True, is_deleted= False)
            cart = Cart.objects.get(user= self.request.user, is_active=True)
            try:
                billing_address = BillingAddress.objects.get(user= self.request.user, is_active=True)

                form = CheckoutForm(initial={
                    'street_address': billing_address.street_address,
                    'apartment_address': billing_address.apartment_address,
                    'country': billing_address.country,
                    'zip': billing_address.zip,
                    'save_info': True
                })
            except:
                form = CheckoutForm()
            amount = cart.calculate_net()
            
            context = {
                'form': form,
                'order': cart,
                'amount':amount
            }
            return render(self.request, 'checkout.html', context)
        except ObjectDoesNotExist:
            return render(self.request, 'checkout.html')
    
    def post(self, request):
        form = CheckoutForm(self.request.POST)

        try:
            cart = Cart.objects.get(user = self.request.user, is_active=True)
            if form.is_valid():
                street_address = form.cleaned_data.get('street_address')
                apartment_address = form.cleaned_data.get('apartment_address')
                country = form.cleaned_data.get('country')
                zip = form.cleaned_data.get('zip')

                same_shipping_address = form.cleaned_data.get('same_shipping_address')
                save_info = form.cleaned_data.get('save_info')
                payment_option = form.cleaned_data.get('payment_option')

                if save_info==True or save_info=='true':
                    try:
                        billing_address = BillingAddress.objects.get(user= self.request.user, country= country, zip=zip)
                        billing_address.street_address = street_address
                        billing_address.apartment_address = apartment_address
                    except BillingAddress.DoesNotExist:
                        billing_address = BillingAddress(
                            user = self.request.user,
                            street_address = street_address,
                            apartment_address= apartment_address,
                            country= country,
                            zip = zip
                        )
                    billing_address.save()
                    cart.billing_address = billing_address
                    cart.save()
            if payment_option == 'S':
                return redirect(reverse('store:payment', kwargs={'payment_option':'stripe'}))
            else:
                return redirect(reverse('store:checkout'))
        except ObjectDoesNotExist:
            return redirect(reverse('store:order_summary.html'))
            
class PaymentView(View):

    def get(self, request, payment_option):
        try:
            cart = Cart.objects.get(user= request.user, is_active=True)
            amount = cart.calculate_net()*100

            stp_cust = StripeCustomer.get_customer(request.user)

            if stp_cust:
                customer = stripe.Customer.retrieve(stp_cust.stripe_customer_id)
            else:
                customer = stripe.Customer.create(
                    name= request.user,
                )
                StripeCustomer.objects.create(
                    user = request.user, stripe_customer_id= customer.id, is_active=True
                )
            intent = stripe.PaymentIntent.create(
                amount= int(amount),
                currency= 'inr',
                customer= customer
            )
            cart.payment_intent_id = intent.id
            cart.save()

            if cart.billing_address:
                context = {
                    'order': cart,
                    'client_secret': intent.client_secret,
                    'meta_data': {'user_id': request.user.id, 'user_name': request.user}
                }
                return render(request, "payment.html", context)
            else:
                return redirect(reverse('store:checkout'))
        except Cart.DoesNotExist:
            return redirect(reverse('product_manager:list'))

@csrf_exempt
def payment_webhook(request):

    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, end_point_secret
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

    # Handle the event
    if event.type == 'charge.succeeded':
        stp_cust = StripeCustomer.get_by_stripe_customer_id(
            event.data.object.customer)
        if stp_cust:
            user = stp_cust.user
            order = Order.objects.get(user=user, ordered=False)
            payment_intent = event.data.object
            # handle_successful_pyament(user, order, payment_intent.id)
        else:
            raise ValueError('Invalid Data')

    elif event.type == 'payment_method.attached':
        payment_method = event.data.object

    elif event.type == 'payment_intent.succeeded':
        print('payment_intent succeeded')

    elif event.type == 'payment_intent.payment_failed':
        print('payment_intent failed')
        return HttpResponse(status=400)

    elif event.type == 'checkout.session.complete':
        # print(event)
        print('checkout_completed')

    elif event.type == 'payment_intent.created':
        print('*****************************')
        print(event)
        print('*****************************')

    else:
        print(event)
        print('unexpected event')
        return HttpResponse(status=400)
    return HttpResponse(status=200)

def payment_success(request):
    return render(request, 'payment_success.html')

def payment_failed(request):
    return render(request, 'payment_failed.html')