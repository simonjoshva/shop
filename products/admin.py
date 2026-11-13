from django.contrib import admin
from products.models import category,product,Order,Orderitem,Payment,Review,Wishlist,Coupon
admin.site.register(category)
admin.site.register(product)

admin.site.register(Orderitem)
class PaymentAdmin(admin.ModelAdmin):
    list_display=('id','order','payment_method','payment_status')
    list_filter=('payment_method','payment_status')
admin.site.register(Payment,PaymentAdmin)
class orderadmin(admin.ModelAdmin):
    list_display=('id','user','phone','address','total_amount','status','created_at')
    list_editable=('status',)
admin.site.register(Order,orderadmin)
admin.site.register(Review)
admin.site.register(Wishlist)
admin.site.register(Coupon)
# Register your models here.
