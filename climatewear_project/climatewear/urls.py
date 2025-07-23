from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.admin.views.decorators import staff_member_required


router = DefaultRouter()
router.register(r'products', views.ProductViewSet)
router.register(r'reviews', views.ReviewViewSet)
router.register(r'categories', views.CategoryViewSet)
router.register(r'profiles', views.UserProfileViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('search/', views.search, name='search'),
    path('about/', views.about, name='about'),
    path('contacts/', views.contacts, name='contacts'),
    path('registration/', views.registration, name='registration'),

    path('catalog/', views.catalog_view, name='catalog'),
    path('api/', include(router.urls)),
    path('login/', views.user_login, name='login'),  # Оставьте только один вариант
    path('logout/', views.user_logout, name='logout'),  # Добавьте logout
    path('add_to_cart/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart, name='cart'),
    path('checkout/', views.checkout, name='checkout'),

    path('remove_from_cart/', views.remove_from_cart, name='remove_from_cart'),
    path('create_order/', views.create_order, name='create_order'),
    path('order_tracking/', views.order_tracking, name='order_tracking'),
    path('registration/', views.registration, name='registration'),
    path('logout/', views.user_logout, name='logout'),
    path('admin-panel/', staff_member_required(views.admin_panel), name='admin-panel'),
    path('statistics/', views.export_statistics, name='export_statistics'),
    path('export-statistics/', views.export_statistics, name='export_statistics'),
    path('submit-review/', views.submit_review, name='submit_review'),
    path('delete-review/<int:review_id>/', views.delete_review, name='delete_review'),
    path('edit_review/<int:review_id>/', views.edit_review, name='edit_review'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('download_statistics/', views.download_statistics, name='download_statistics')
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)