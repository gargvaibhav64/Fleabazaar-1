from django.db import models
from django.conf import settings
from django.urls import reverse
from django.template.defaultfilters import slugify
from django_countries.fields import CountryField
# Create your models here.


class Event(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(
        unique=True, help_text="Slug will be generated automatically from the title of the post", default='')
    place = models.CharField(max_length=300)
    description = models.CharField(max_length=500)
    layout_type = models.IntegerField(default=1)
    no_of_shops = models.IntegerField(default=10)
    time = models.DateTimeField()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('core:event_detail', args=[self.pk])

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Event, self).save(*args, **kwargs)

        for i in range(1, self.no_of_shops):
            X = Shop()
            X.event = self
            X.shop_no = i
            X.save()


class Shop(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE,)
    shop_no = models.IntegerField(unique=True, blank=False)
    price = models.DecimalField(max_digits=6, decimal_places=2, default=500.00)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return str(self.shop_no)

    def add_to_cart_url(self):
        return reverse('core:add-to-cart', kwargs={'pk': self.event.pk, 'shop_no': self.shop_no})

    def remove_from_cart_url(self):
        return reverse('core:remove-from-cart', kwargs={'pk': self.event.pk, 'shop_no': self.shop_no})


class OrderItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    item = models.ForeignKey(Shop, on_delete=models.CASCADE)
    ordered = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.item.shop_no} of {self.item.event.name}"

    def price(self):
        return self.item.price


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)

    items = models.ManyToManyField(OrderItem)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField()

    ordered = models.BooleanField(default=False)

    address = models.ForeignKey(
        'Address', on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return str(self.pk)

    def get_total(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.price()

        return total


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    street_address = models.CharField(max_length=200)
    apartment_address = models.CharField(max_length=200)
    country = CountryField()
    state = models.CharField(max_length=50)
    zip = models.CharField(max_length=6)

    def __str__(self):
        return self.user.username
