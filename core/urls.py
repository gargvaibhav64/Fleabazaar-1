from django.urls import path
from . import views
from .views import (
    event_list,
    HomeView,
    event_detail,
    add_to_cart,
    remove_from_cart,
    OrderSummaryView,
    CheckoutView,
    handlerequest,
    PastOrderView
)

app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name='event-list'),
    path('order-summary/', OrderSummaryView.as_view(), name='order-summary'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('pastorders/', PastOrderView.as_view(), name='pastorders'),
    path('handlerequest/', views.handlerequest, name='handlerequest'),
    path('event/<int:pk>', views.event_detail, name='event_detail'),
    path('add-to-cart/<int:pk>/<int:shop_no>/',
         add_to_cart, name='add-to-cart'),
    path('remove-from-cart/<int:pk>/<int:shop_no>/',
         remove_from_cart, name='remove-from-cart'),
]
