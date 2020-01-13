from django.shortcuts import render, get_object_or_404, get_list_or_404, reverse, redirect, HttpResponse
from .models import Event, Shop, OrderItem, Order, Address, PaymentInfo
from django.utils import timezone
from django.views.generic import ListView, DetailView, View
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import CheckoutForm
from django.views.decorators.csrf import csrf_exempt
from .Paytm import Checksum
import json
import requests
# Create your views here.

MERCHANT_ID = 'yGhiFc56070841982837'
MERCHANT_KEY = 'Be7uTRD@7R9QOGN3'


def event_list(request):
    context = {
        'events': Event.objects.all()
    }
    return render(request, "event_list.html", context)


class HomeView(ListView):
    model = Event
    template_name = "event_list.html"


def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    shops = Shop.objects.filter(event=event)
    return render(request, 'event_detail.html', {'event': event, 'shops': shops, })


class CheckoutView(View):
    def get(self, *args, **kwargs):
        form = CheckoutForm()
        context = {
            'form': form,
        }
        return render(self.request, "checkout-page.html", context)

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            print(form.is_valid())
            if form.is_valid():
                address = Address()
                address.first_name = form.cleaned_data.get('first_name')
                address.last_name = form.cleaned_data.get('last_name')
                address.email = form.cleaned_data.get('email')
                address.street_address = form.cleaned_data.get(
                    'street_address')
                address.apartment_address = form.cleaned_data.get(
                    'apartment_address')
                address.country = form.cleaned_data.get('country')
                address.state = form.cleaned_data.get('state')
                address.zip = form.cleaned_data.get('zip')
                address.user = self.request.user
                address.save()
                order.address = address
                order.save()

                param_dict = {

                    'MID': MERCHANT_ID,
                    'ORDER_ID': str(order.pk),
                    'TXN_AMOUNT': str(order.get_total()),
                    'CUST_ID': address.email,
                    'INDUSTRY_TYPE_ID': 'Retail',
                    'WEBSITE': 'WEBSTAGING',
                    'CHANNEL_ID': 'WEB',
                    'CALLBACK_URL': 'http://127.0.0.1:8000/handlerequest/',

                }
                param_dict['CHECKSUMHASH'] = Checksum.generate_checksum(
                    param_dict, MERCHANT_KEY)

                return render(self.request, 'paytm.html', {'param_dict': param_dict})
            else:
                messages.warning(self.request, "Form is not valid")
                return redirect('core:checkout')

        except ObjectDoesNotExist:
            messages.error(
                self.request, "You do not have any items in the cart")
            return redirect('core:order-summary')


class EventDetailView(DetailView):
    model = Shop
    template_name = "event_detail.html"


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'object': order
            }
        except ObjectDoesNotExist:
            messages.error(
                self.request, "You do not have any items in the cart")
            return redirect('/')
        return render(self.request, 'order_summary.html', context)


@login_required
def add_to_cart(request, pk, shop_no):
    event = get_object_or_404(Event, pk=pk)
    shop = Shop.objects.get(event=event, shop_no=shop_no)
    order_item, created = OrderItem.objects.get_or_create(
        item=shop, user=request.user, ordered=False)

    order_qs = Order.objects.filter(user=request.user, ordered=False)

    if order_qs.exists():
        order = order_qs[0]
        order.items.add(order_item)
        messages.info(request, "This shop was added to your cart.")

    else:
        ordered_date = timezone.now()
        order = Order.objects.create(
            user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "This shop was added to your cart.")

    return redirect('core:order-summary')


@login_required
def remove_from_cart(request, pk, shop_no):
    event = get_object_or_404(Event, pk=pk)
    shop = Shop.objects.get(event=event, shop_no=shop_no)

    order_qs = Order.objects.filter(user=request.user, ordered=False)

    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(user=request.user, ordered=False, item=shop).exists():
            order_item = OrderItem.objects.filter(
                item=shop, user=request.user, ordered=False)
            order_item = order_item[0]
            order.items.remove(order_item)
            messages.info(request, "This shop was removed from your cart.")
            return redirect('core:order-summary')

        else:
            messages.info(request, "This shop was not in your cart.")
            return redirect('core:event_detail', pk=pk)

    else:
        messages.info(request, "No order is created yet.")
        return redirect('core:event_detail', pk=pk)


@csrf_exempt
def handlerequest(request):
    # paytm will send you post request here
    form = request.POST
    response_dict = {}
    for i in form.keys():
        response_dict[i] = form[i]
        if i == 'CHECKSUMHASH':
            checksum = form[i]

    verify = Checksum.verify_checksum(response_dict, MERCHANT_KEY, checksum)
    if verify:
        if response_dict['RESPCODE'] == '01':
            # verify with transaction-status-api
            paytmParams = dict()
            paytmParams["MID"] = MERCHANT_ID
            print(response_dict)
            paytmParams["ORDERID"] = response_dict["ORDERID"]
            checksum = Checksum.generate_checksum(paytmParams, MERCHANT_KEY)
            paytmParams["CHECKSUMHASH"] = checksum
            post_data = json.dumps(paytmParams)
            url = "https://securegw-stage.paytm.in/order/status"
            response_from_api = requests.post(url, data=post_data, headers={
                                              "Content-type": "application/json"}).json()

            if response_from_api['RESPCODE'] == '01':
                try:
                    orders = Order.objects.filter(
                        pk=response_dict["ORDERID"])[0]
                    orders.ordered = True
                    orders.ordered_date = timezone.now()
                    payment = PaymentInfo()
                    payment.gateway_name = response_dict['GATEWAYNAME']
                    payment.transaction_id = response_dict['TXNID']
                    payment.bank_transaction_id = response_dict['BANKTXNID']
                    payment.transaction_amount = response_dict['TXNAMOUNT']
                    payment.save()

                    orders.payment = payment
                    orders.save()
                except ObjectDoesNotExist:
                    messages.error(request, "Order not found")

                print('Payment received')

            print('order successful')
        else:
            print(response_dict)
            print('order was not successful because' +
                  response_dict['RESPMSG'])
    return render(request, 'paymentstatus.html', {'response': response_dict})


class PastOrderView(View):
    def get(request, *args, **kwargs):
        try:
            orders = Order.objects.filter(user=request.user, ordered=True)
            context = {
                'orders': orders
            }
        except ObjectDoesNotExist:
            messages.error(
                self.request, "You do not have any past orders")
        return render(self.request, 'myorders.html', context)
