from django.db import models
from django.contrib.auth.models import User
class category(models.Model):
    name=models.CharField(max_length=100,unique=True)
    description=models.TextField(blank=True)
    image=models.ImageField(upload_to='categories/',blank=True,null=True)

    def __str__(self):
        return self.name

class product(models.Model):
    category=models.ForeignKey(category,on_delete=models.CASCADE)
    name=models.CharField(max_length=200)
    description=models.TextField()
    price=models.DecimalField(max_digits=10,decimal_places=2)
    stock=models.PositiveIntegerField()
    low_stock_limit=models.IntegerField(default=5)
    image=models.ImageField(upload_to='products/',blank=True,null=True)
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Cart(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    product=models.ForeignKey(product,on_delete=models.CASCADE)
    quantity=models.PositiveIntegerField(default=1)
    created_at=models.DateTimeField(auto_now_add=True)
    def total_price(self):
        return self.product.price*self.quantity

    def __str__(self):
        return self.user.username+"-"+self.product.name

class Order(models.Model):
    STATUS_CHOICES=(
        ('Pending','Pending'),
        ('Processing','Processing'),
        ('Shipped','Shipped'),
        ('Delivered','Delivered'),
        ('Cancelled','Cancelled'),
        ('Refunded','Refunded'),
    )
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    address=models.TextField()
    phone=models.CharField(max_length=15)
    total_amount=models.DecimalField(max_digits=10,decimal_places=2)
    status=models.CharField(max_length=20,choices=STATUS_CHOICES,default='Pending')
    created_at=models.DateTimeField(auto_now_add=True)
    return_requested=models.BooleanField(default=False)
    return_reason=models.TextField(blank=True,null=True)
    refund_status=models.CharField(max_length=20,default="No Refund")
    payment_method=models.CharField(max_length=20,choices=[('COD','Cash on Delivery'),('UPI','UPI')],default='COD')
    upi_reference=models.CharField(max_length=100,blank=True,null=True)

    def __str__(self):
        return "Order - "+self.user.username

class Orderitem(models.Model):
    order=models.ForeignKey(Order,on_delete=models.CASCADE)
    product=models.ForeignKey(product,on_delete=models.CASCADE)
    quantity=models.PositiveIntegerField(default=1)
    price=models.DecimalField(max_digits=10,decimal_places=2)
    def __str__(self):
        return self.product.name

class Payment(models.Model):
    PAYMENT_METHODS=(
        ('COD','Cash on Delivery'),
        ('ONLINE','Online Payment'),
    )
    PAYMENT_STATUS=(
        ('Pending','Pending'),
        ('Paid','Paid'),
        ('Failed','Failed'),
    )
    order=models.OneToOneField(Order,on_delete=models.CASCADE)
    payment_method=models.CharField(max_length=20,choices=PAYMENT_METHODS)
    payment_status=models.CharField(max_length=20,choices=PAYMENT_STATUS,default='Pending')
    payment_date=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.order.user.username +" Payment"

class Profile(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    phone=models.CharField(max_length=15,blank=True)
    address=models.TextField(blank=True)

    def __str__(self):
        return self.user,username

class Review(models.Model):
    product=models.ForeignKey(product,on_delete=models.CASCADE,related_name='reviews')
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    rating=models.IntegerField()
    comment=models.TextField()
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.product.name

class Wishlist(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    product=models.ForeignKey(product,on_delete=models.CASCADE)
    created_at=models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.user.username

class Coupon(models.Model):
    code=models.CharField(max_length=20,unique=True)
    discount=models.IntegerField()
    minimum_amount=models.IntegerField(default=0)
    expiry_date=models.DateTimeField(null=True,blank=True)
    active=models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code

# Create your models here.
