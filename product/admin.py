from django.contrib import admin

from .models import Category, Product, Review, ProductItem


class ProductInLine(admin.TabularInline):
    model = ProductItem


class ProductAdmin(admin.ModelAdmin):
    list_display = ['slug', 'mog', 'name', 'price', 'category']
    list_filter = ['name', 'category']
    search_fields = ['slug', 'mog', 'name']
    inlines = [ProductInLine]


admin.site.register(Category)
admin.site.register(Product, ProductAdmin)
admin.site.register(Review)