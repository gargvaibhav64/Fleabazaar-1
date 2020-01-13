from django.contrib import admin
from .models import Shop, Event, Order, OrderItem, PaymentInfo
# Register your models here.

admin.site.register(Event)
admin.site.register(Shop)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(PaymentInfo)
