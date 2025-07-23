from django.contrib import admin
from django.contrib.auth import get_user_model

User = get_user_model()

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'date_joined')

admin.site.unregister(User)

admin.site.register(User, UserAdmin)

from .models import UserProfile, Color, Size, Category, Product, Review, ProductImage, Cart, CartItem

admin.site.register(UserProfile)
admin.site.register(Color)
admin.site.register(Size)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Review)
admin.site.register(ProductImage)
admin.site.register(Cart)
admin.site.register(CartItem)
from django.contrib import admin
from .models import Order, OrderItem

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username',)

admin.site.register(OrderItem)
