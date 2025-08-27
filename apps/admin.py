from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.sites.models import Site
from parler.admin import TranslatableAdmin

from apps.models import Category, Product, SiteSettings, Order, Withdraw


# Register your models here.
@admin.register(Category)
class CategoryAdmin(TranslatableAdmin):
    exclude = ('slug',)

@admin.register(Product)
class ProductAdmin(TranslatableAdmin):
    exclude = ('slug',)

@admin.register(SiteSettings)
class SiteSettingsAdmin(ModelAdmin):
    pass

@admin.register(Order)
class OrderAdmin(ModelAdmin):
    pass

@admin.register(Withdraw)
class WithdrawAdmin(ModelAdmin):
    list_display = 'card_number','user','amount','status','pay_check'