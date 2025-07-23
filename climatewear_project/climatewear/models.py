from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models

class Color(models.Model):
    name = models.CharField(max_length=50, unique=True)
    hex_code = models.CharField(max_length=7, default='#FFFFFF')

    def __str__(self):
        return self.name

class Size(models.Model):
    name = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    is_popular = models.BooleanField(default=False)
    sizes = models.ManyToManyField(Size, related_name='products', blank=True)
    colors = models.ManyToManyField(Color, related_name='products', blank=True)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.name

    def get_discount_percentage(self):
        if self.discount_price and self.price > 0:
            discount = ((float(self.price) - float(self.discount_price)) / float(self.price)) * 100
            return int(round(discount))
        return 0

class Order(models.Model):
    STATUS_CHOICES = [
        ('ordered', 'Оформлен'),
        ('assembly', 'Отправлен на сборку'),
        ('assembled', 'Собран'),
        ('in_transit', 'В пути'),
        ('delivered', 'Доставлен'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ordered')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    comment = models.TextField(blank=True, null=True)


    def __str__(self):
        return f"Order #{self.id} - {self.status}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()  # Изменяем на IntegerField
    color = models.ForeignKey(Color, null=True, on_delete=models.SET_NULL)
    size = models.ForeignKey(Size, null=True, on_delete=models.SET_NULL)

    def clean(self):
        if self.quantity < 0:
            raise ValidationError('Количество не может быть отрицательным.')

    def save(self, *args, **kwargs):
        self.full_clean()  # Вызов валидации перед сохранением
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} (x{self.quantity})"

class Review(models.Model):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    rating = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f'Review by {self.author} on {self.product}'

class SiteReview(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор")
    content = models.TextField(verbose_name="Текст отзыва")
    rating = models.IntegerField(choices=RATING_CHOICES, verbose_name="Оценка")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Отзыв о сайте"
        verbose_name_plural = "Отзывы о сайте"
        ordering = ['-created_at']

    def __str__(self):
        return f"Отзыв от {self.author.username} ({self.rating}/5)"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    address = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.user.username

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/')

    def __str__(self):
        return f"Image for {self.product.name}"

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Корзина пользователя {self.user.username}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True)
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.product.name} (x{self.quantity})"

# Forms
class SiteReviewForm(forms.ModelForm):
    class Meta:
        model = SiteReview
        fields = ['content', 'rating']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4}),
            'rating': forms.Select(attrs={'class': 'form-control'})
        }
        labels = {
            'content': 'Ваш отзыв',
            'rating': 'Оценка'
        }

class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Подтвердите пароль")

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Этот email уже используется.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Это имя пользователя уже занято.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Пароли не совпадают.")
        return cleaned_data

class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)