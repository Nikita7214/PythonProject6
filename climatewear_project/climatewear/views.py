from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.messages import get_messages
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect
from django.db.models import Q, Prefetch, Case, FloatField, When
from django.views.decorators.csrf import csrf_exempt
from openpyxl.reader.excel import load_workbook
from django.utils import timezone
from rest_framework import viewsets, permissions
from django.db import transaction
from django.contrib import messages
from django.contrib.auth.models import User
from rest_framework.generics import get_object_or_404

from .models import Product, Category, Review, UserProfile, Color, Cart, CartItem, Size, Order, OrderItem
from .serializers import ProductSerializer, ReviewSerializer, CategorySerializer, UserProfileSerializer
from .forms import RegistrationForm, LoginForm
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font
from django.db.models import Count, Sum
from django.contrib.admin.views.decorators import staff_member_required
from .models import User, Product
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count, F
from datetime import datetime, timedelta
from django.shortcuts import render

import os
from django.conf import settings
from datetime import datetime
from .models import SiteReview


@login_required
def submit_review(request):
    if request.method == 'POST':
        rating = request.POST.get('rating')
        content = request.POST.get('content')

        if not content or not rating:
            messages.error(request, 'Пожалуйста, заполните все поля')
            return redirect('about')

        SiteReview.objects.create(
            author=request.user,
            rating=rating,
            content=content
        )
        messages.success(request, 'Ваш отзыв успешно отправлен!')
        return redirect('about')

    return redirect('about')


def payment_success(request):
    return render(request, 'payment-success.html')

def edit_review(request, review_id):
    review = get_object_or_404(SiteReview, id=review_id)

    if request.method == 'POST':
        new_rating = request.POST.get('rating')
        new_content = request.POST.get('content', '').strip()

        if not new_rating or not new_content:
            messages.error(request, 'Все поля обязательны для заполнения')
            return render(request, 'edit_review.html', {'review': review})

        try:
            new_rating = int(new_rating)
            if 1 <= new_rating <= 5:
                review.rating = new_rating
                review.content = new_content
                review.save()
                messages.success(request, 'Отзыв успешно обновлен')
                return redirect('about')
            else:
                messages.error(request, 'Рейтинг должен быть от 1 до 5')
        except ValueError:
            messages.error(request, 'Некорректный формат рейтинга')

        return render(request, 'edit_review.html', {'review': review})

    return render(request, 'edit_review.html', {'review': review})

@staff_member_required
def delete_review(request, review_id):
    try:
        review = SiteReview.objects.get(id=review_id)
        review.delete()
        messages.success(request, 'Отзыв успешно удален')
    except SiteReview.DoesNotExist:
        messages.error(request, 'Отзыв не найден')
    return redirect('about')

def user_login(request):
    storage = get_messages(request)
    list(storage)  # Clear existing messages

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.warning(request, 'Неверные данные. Попробуйте снова.')
            return redirect('login')

    return render(request, 'login.html')


def registration(request):
    storage = get_messages(request)
    list(storage)  # Clear existing messages

    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if len(password1) < 4:
            messages.warning(request, 'Пароль должен быть не менее 4 символов.')
            return redirect('registration')

        if password1 == password2:
            if User.objects.filter(username=username).exists():
                messages.warning(request, "Имя пользователя уже занято.")
                return redirect('registration')
            elif User.objects.filter(email=email).exists():
                messages.warning(request, 'Email уже зарегистрирован.')
                return redirect('registration')
            else:
                user = User.objects.create_user(username=username, password=password1, email=email)
                user.save()
                messages.success(request, 'Регистрация успешна! Войдите в систему.')
                return redirect('login')
        else:
            messages.warning(request, 'Пароли не совпадают.')
            return redirect('registration')

    return render(request, 'registration.html')


def user_logout(request):
    storage = get_messages(request)
    list(storage)  # Clear existing messages
    logout(request)
    return redirect('home')


@login_required
def user_profile(request):
    user = request.user
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        user.username = username
        user.email = email
        if password:
            user.set_password(password)

        user.save()
        messages.success(request, "Ваш профиль успешно обновлен!")
        return redirect("user_profile")

    return render(request, "user_profile.html", {"user": user})

@staff_member_required
def admin_panel(request):
    products = Product.objects.all()
    orders = Order.objects.all().order_by('-created_at')
    users = User.objects.all()

    return render(request, 'admin_panel.html', {
        'products': products,
        'orders': orders,
        'users': users,
        'total_products': products.count(),
        'total_orders': orders.count(),
        'active_users': users.filter(is_active=True).count(),
    })

@staff_member_required
def update_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.price = request.POST.get('price')
        product.stock = request.POST.get('stock')
        product.discount_price = request.POST.get('discount_price')  # Если есть скидка
        product.save()
        messages.success(request, 'Товар успешно обновлён')
        return redirect('admin_panel')

    return render(request, 'edit_product.html', {'product': product})

@staff_member_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    messages.success(request, 'Товар успешно удалён')
    return redirect('admin_panel')

def home(request):
    categories = Category.objects.all()
    popular_products = Product.objects.filter(is_popular=True)
    return render(request, 'home.html', {
        'categories': categories,
        'popular_products': popular_products,
        'is_authenticated': request.user.is_authenticated,
    })


@login_required
def order_tracking(request):
    if request.user.is_staff:
        # Для админа показываем все заказы всех пользователей
        orders = Order.objects.all().order_by('-created_at')
    else:
        # Для обычных пользователей показываем только их заказы
        orders = Order.objects.filter(user=request.user).order_by('-created_at')

    return render(request, 'order_tracking.html', {
        'orders': orders,
        'user': request.user  # Добавляем пользователя в контекст
    })


@login_required
def create_order(request):
    if request.method == 'POST':
        user = request.user
        cart = request.session.get('cart', {})
        comment = request.POST.get('comment', '')

        # Проверка на наличие товаров в корзине
        if not cart:
            messages.error(request, 'Ваша корзина пуста.')
            return redirect('cart')

        total_price = 0
        order = Order.objects.create(user=user, status='ordered', comment=comment)

        for item_key, item_data in cart.items():
            try:
                product = Product.objects.get(id=item_data['product_id'])
                size = Size.objects.get(id=item_data['size'])
                color = Color.objects.get(id=item_data['color'])

                # Проверка доступности товара на складе
                if product.stock < item_data['quantity']:
                    messages.error(request, f'Недостаточно товара "{product.name}" на складе. Доступно: {product.stock} шт.')
                    order.delete()  # Удаляем заказ
                    return redirect('cart')

                total_price += product.price * item_data['quantity']

                # Создаем элемент заказа
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item_data['quantity'],
                    color=color,
                    size=size
                )

                # Уменьшаем количество товара на складе
                product.stock -= item_data['quantity']
                product.save()

            except (Product.DoesNotExist, Color.DoesNotExist, Size.DoesNotExist) as e:
                messages.warning(request, f'Ошибка обработки товара: {str(e)}.')
                continue

        # Сохраняем общую стоимость заказа
        order.total_price = total_price
        order.save()

        # Очищаем корзину после оформления заказа
        request.session['cart'] = {}
        messages.success(request, 'Ваш заказ успешно оформлен!')
        return redirect('order_tracking')

    return redirect('cart')



def search(request):
    query = request.GET.get('q')
    results = Product.objects.filter(Q(name__icontains=query)) if query else []
    return render(request, 'search_results.html', {'query': query, 'results': results})


@login_required
def checkout(request):
    # Retrieve cart from session
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, 'Ваша корзина пуста!')
        return redirect('cart')

    # Calculate total price
    total_price = 0
    items = []
    for item_key, item_data in cart.items():
        try:
            product = Product.objects.get(id=item_data['product_id'])
            size = Size.objects.filter(id=item_data['size']).first()
            color = Color.objects.filter(id=item_data['color']).first()
            item_price = product.discount_price if product.discount_price else product.price
            total_price += item_price * item_data['quantity']

            items.append({
                'product': product,
                'quantity': item_data['quantity'],
                'size': size.name if size else "Не выбран",
                'color': color.name if color else "Не выбран",
                'price': product.price,
            })
        except Product.DoesNotExist:
            messages.warning(request, f"Ошибка загрузки товара с ID {item_data['product_id']}")

    return render(request, 'checkout.html', {'cart_items': items, 'total_price': total_price})


def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    new_quantity = int(request.POST.get('quantity'))

    if new_quantity > cart_item.product.stock:
        return JsonResponse({
            'status': 'error',
            'message': f'Максимальное количество: {cart_item.product.stock}'
        }, status=400)

    cart_item.quantity = new_quantity
    cart_item.save()
    return JsonResponse({'status': 'success'})


def cart(request):
    cart = request.session.get('cart', {})
    items = []

    # Обработка POST-запросов (изменение количества)
    if request.method == 'POST':
        item_key = request.POST.get('item_key')
        new_quantity = int(request.POST.get('quantity', 1))

        if item_key in cart:
            if new_quantity > 0:
                cart[item_key]['quantity'] = new_quantity
                messages.success(request, 'Количество товара успешно обновлено.')
            else:
                del cart[item_key]
                messages.success(request, 'Товар удален из корзины.')
        else:
            messages.error(request, 'Товар не найден в корзине.')

        request.session['cart'] = cart
        return redirect('cart')

    # Отображение корзины
    for item_key, item_data in cart.items():
        try:
            # Разбиваем ключ на составляющие (если используется формат "product_id_size_color")
            parts = item_key.split('_')
            product_id = parts[0]

            product = Product.objects.get(id=product_id)

            size_name = None
            if len(parts) > 1 and parts[1]:  # Если есть размер в ключе
                size = Size.objects.filter(id=parts[1]).first()
                size_name = size.name if size else "Не выбран"
            elif 'size' in item_data:  # Альтернативно проверяем в данных
                size = Size.objects.filter(id=item_data['size']).first()
                size_name = size.name if size else "Не выбран"

            color_name = None
            if len(parts) > 2 and parts[2]:  # Если есть цвет в ключе
                color = Color.objects.filter(id=parts[2]).first()
                color_name = color.name if color else "Не выбран"
            elif 'color' in item_data:  # Альтернативно проверяем в данных
                color = Color.objects.filter(id=item_data['color']).first()
                color_name = color.name if color else "Не выбран"

            items.append({
                'item_key': item_key,  # Важно для идентификации товара в формах
                'product': product,
                'quantity': item_data['quantity'],
                'price': product.price,
                'color': color_name,
                'size': size_name
            })
        except (Product.DoesNotExist, IndexError, ValueError) as e:
            messages.warning(request, f'Ошибка загрузки товара с ID {product_id}: {str(e)}')
            continue

    return render(request, 'cart.html', {'items': items})


@login_required
def add_to_cart(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        color_id = request.POST.get('color')
        size_id = request.POST.get('size')
        quantity = int(request.POST.get('quantity', 1))
        cart = request.session.get('cart', {})
        product = get_object_or_404(Product, id=product_id)

        if product.stock <= 0:
            return JsonResponse({
                'status': 'error',
                'message': f'Товар "{product.name}" закончился'
            }, status=400)

        if quantity > product.stock:
            return JsonResponse({
                'status': 'error',
                'message': f'Максимальное доступное количество: {product.stock} шт.'
            }, status=400)

        from uuid import uuid4
        item_key = f"{product_id}_{size_id}_{color_id}_{uuid4()}"

        cart[item_key] = {
            'product_id': product_id,
            'quantity': quantity,
            'color': color_id,
            'size': size_id
        }

        request.session['cart'] = cart
        messages.success(request, 'Товар успешно добавлен в корзину!')
        return redirect('cart')

    return redirect('catalog')

def about(request):

    reviews = SiteReview.objects.all().order_by('-created_at')
    return render(request, 'about.html', {'reviews': reviews})


def contacts(request):
    return render(request, 'contacts.html')


@login_required
def remove_from_cart(request):
    if request.method == 'POST':
        item_key = request.POST.get('item_key')
        cart = request.session.get('cart', {})

        if item_key in cart:
            del cart[item_key]
            messages.success(request, 'Товар удален из корзины.')
        else:
            messages.error(request, 'Товар не найден в корзине.')

        request.session['cart'] = cart
        return redirect('cart')

    return redirect('cart')


def catalog_view(request):
    category = request.GET.get('category', 'all')
    color_filter = request.GET.get('color', 'all')
    sort = request.GET.get('sort')

    products = Product.objects.all().prefetch_related(Prefetch('colors', queryset=Color.objects.all()))

    if category == 'women':
        products = products.filter(category__name='Женское')
    elif category == 'men':
        products = products.filter(category__name='Мужское')
    elif category == 'discount':
        products = products.filter(discount_price__isnull=False)

    if sort == 'price_asc':
        products = products.annotate(
            final_price=Case(
                When(discount_price__isnull=False, then='discount_price'),
                default='price',
                output_field=FloatField()
            )
        ).order_by('final_price')
    elif sort == 'price_desc':
        products = products.annotate(
            final_price=Case(
                When(discount_price__isnull=False, then='discount_price'),
                default='price',
                output_field=FloatField()
            )
        ).order_by('-final_price')

    if color_filter and color_filter != 'all':
        products = products.filter(colors__name=color_filter)

    return render(request, 'catalog.html', {'products': products, 'current_category': category})


@staff_member_required
def export_statistics(request):
    data = []
    file_path = os.path.join(settings.BASE_DIR, 'climatewear_project', 'statistic.xlsx')

    if request.method == 'POST':
        month_range = request.POST.get('month_range', '30')  # Берем значение, если его нет — ставим 30 дней
        month_range = int(month_range)

        start_date = datetime.now() - timedelta(days=month_range)

        wb = Workbook()
        ws = wb.active
        ws.title = "Statistics"

        ws.append(["Статистика продаж - ClimateWear"])
        ws.append(["Период:", f"Последние {month_range} {'день' if month_range == 1 else 'дней'}"])
        ws.append([])

        ws.append(["Пользователь", "Количество заказов", "Общая сумма (руб)"])
        user_stats = User.objects.annotate(
            order_count=Count('order'),
            total_spent=Sum('order__total_price')
        ).filter(order_count__gt=0, order__created_at__gte=start_date).order_by('-order_count')

        for user in user_stats:
            ws.append([user.username, user.order_count, user.total_spent or 0])
            data.append(user)

        wb.save(file_path)

        download_ready = True
    else:
        download_ready = False
        month_range = 30  # Ставим значение по умолчанию (1 месяц), если запрос GET

    return render(request, 'statistics.html', {'data': data, 'download_ready': download_ready, 'file_path': file_path, 'month_range': month_range})



def download_statistics(request):
    file_path = os.path.join(settings.BASE_DIR, 'climatewear_project', 'statistic.xlsx')

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="statistic_{datetime.now().strftime("%Y-%m-%d")}.xlsx"'
    with open(file_path, 'rb') as f:
        response.write(f.read())

    return response


# REST API Viewsets
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


