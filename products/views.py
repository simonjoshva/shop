from django.shortcuts import render,redirect,get_object_or_404
from products.models import category as Category, product as Products,Cart,Order,Orderitem,Payment,Profile,Review,Wishlist,Coupon
from django.contrib.auth.decorators import login_required
from django.db.models import Q,Avg,Sum
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.http import HttpResponse
from reportlab.platypus import (
    SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from io import BytesIO
from django.utils import timezone
from django.contrib import messages



def category_list(request):
    categories=Category.objects.all()
    return render(request,'category_list.html',{'categories':categories})
 
def add_category(request):
    if request.method=="POST":
        name=request.POST['name']
        description=request.POST['description']
        image=request.FILES.get('image')
        Category.objects.create(name=name,description=description,image=image)
        return redirect('category_list')
    return render(request,'add_category.html')

def edit_category(request,id):
    category=Category.objects.get(id=id)
    if request.method=="POST":
        category.name=request.POST['name']
        category.description=request.POST['description']

        if request.FILES.get('image'):
            category.image=request.FILES['image']

        category.save()
        return redirect('category_list')
    return render(request,'edit_category.html',{'category':category})

def delete_category(request,id):
    category=get_object_or_404(Category,id=id)
    category.delete()
    return redirect('category_list')

def product_list(request):
    products=Products.objects.all()
    categories=Category.objects.all()
    search=request.GET.get('search')
    if search:
        products=products.filter(Q(name__icontains=search))
    category_id=request.GET.get('category')
    if category_id:
        products=products.filter(category_id=category_id)

    min_price=request.GET.get('min_price')
    max_price=request.GET.get('max_price')
    if min_price:
        products=products.filter(price__gte=min_price)
    if max_price:
        products=products.filter(price__lte=max_price)

    return render(request,'product_list.html',{'products':products,'categories':categories})

def add_product(request):
    categories=Category.objects.all()
    if request.method=="POST":
        category=Category.objects.get(id=request.POST['category'])
        Products.objects.create(
            category=category,
            name=request.POST['name'],
            description=request.POST['description'],
            price=request.POST['price'],
            stock=request.POST['stock'],
            image=request.FILES.get('image'))
        return redirect('product_list')
    return render(request,'add_product.html',{'categories':categories})

def edit_product(request,id):
    product=get_object_or_404(Products,id=id)
    categories=Category.objects.all()
    if request.method=="POST":
        product.category=Category.objects.get(id=request.POST['category'])
        product.name=request.POST['name']
        product.description=request.POST['description']
        product.price=request.POST['price']
        product.stock=request.POST['stock']
        if request.FILES.get('image'):
            product.image=request.FILES['image']
        product.save()
        return redirect('product_list')
    return render(request,'edit_product.html',{'product':product,'categories':categories})

def delete_product(request,id):
    product=get_object_or_404(Products,id=id)
    product.delete()
    return redirect('product_list')

def home(request):
    products=Products.objects.all()
    categories=Category.objects.all()
    return render(request,'homme.html',{'products':products,'categories':categories})

def product_detail(request,id):
    product=get_object_or_404(Products,id=id)
    average_rating=product.reviews.aggregate(avg_rating=Avg('rating'))
    return render(request,'product_detail.html',{'product':product,'average_rating':average_rating['avg_rating']})

@login_required
def add_to_cart(request,id):
    product=get_object_or_404(Products,id=id)
    if product.stock<=0:
        messages.error(request,"Product is out of stock")
        return redirect('product_detail',id=id)
    cart_item,created=Cart.objects.get_or_create(user=request.user,product=product)
    if not created:
        if cart_item.quantity>=product.stock:
            messages.error(request,"Not enough stock available")
            return redirect('cart')
        cart_item.quantity+=1
        cart_item.save()
    return redirect('cart')
@login_required
def cart(request):
    cart_items=Cart.objects.filter(user=request.user)
    total=0
    for item in cart_items:
        total+=item.total_price()
    return render(request,'cart.html',{'cart_items':cart_items,'total':total})
@login_required
def increase_quantity(request,id):
    cart_item=get_object_or_404(Cart,id=id,user=request.user)
    cart_item.quantity+=1
    cart_item.save()
    return redirect('cart')

@login_required
def decrease_quantity(request,id):
    cart_item=get_object_or_404(Cart,id=id,user=request.user)
    if cart_item.quantity>1:
        cart_item.quantity-=1
        cart_item.save()
    return redirect('cart')

@login_required
def remove_from_cart(request,id):
    cart_item=get_object_or_404(Cart,id=id,user=request.user)
    cart_item.delete()
    return redirect('cart')

@login_required
def checkout(request):
    cart_items=Cart.objects.filter(user=request.user)
    total=0
    for item in cart_items:
        total+=item.total_price()
    if request.method=="POST":
        address=request.POST['address']
        phone=request.POST['phone']
        payment_method=request.POST['payment_method']
        if payment_method=="COD":
            order=Order.objects.create(user=request.user,address=address,phone=phone,total_amount=total,payment_method="COD")
            Payment.objects.create(order=order,payment_method=payment_method,payment_status='Pending')
            for item in cart_items:
                Orderitem.objects.create(order=order,product=item.product,quantity=item.quantity,price=item.product.price)
                product=item.product
                product.stock-=item.quantity
                product.save()
            cart_items.delete()
            return redirect('home')
        elif payment_method=="UPI":
            request.session['checkout_address']=address
            request.session['checkout_phone']=phone
            return redirect('upi_payment')
    return render(request,'checkout.html',{'total':total})

@login_required
def order_history(request):
    orders=Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request,'order_history.html',{'orders':orders})


@login_required
def payment_success(request):
    payment_id=request.GET.get('razorpay_payment_id')
    order_id=request.GET.get('razorpay_order_id')
    signature=request.GET.get('razorpay_signature')
    client=razorpay.Client(
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        )
    )
    try:
        client.utility.verify_payment_signature({'razorpay_order_id':order_id,'razorpay_payment_id':payment_id,'razorpay_signature':signature})
        payment=Payment.objects.get(razorpay_order_id=order_id)
        payment.payment_status="Completed"
        payment.save()

        order=payment.order
        order.payment_status="Paid"
        order.save()
        send_payment_success_email(order)
        send_invoice_email(order)
        

        return render(request,'payment_success.html')
    except:
        return render(request,'payment_failed.html')

@login_required
def profile(request):

    user_profile,created=Profile.objects.get_or_create(user=request.user)
    return render(request,'profile.html',{'profile':user_profile})

@login_required
def update_profile(request):
    profile,created=Profile.objects.get_or_create(user=request.user)
    if request.method=='POST':
        request.user.username=request.POST['username']
        request.user.email=request.POST['email']
        request.user.save()
        profile.phone=request.POST['phone']
        profile.address=request.POST['address']
        profile.save()
        return redirect('profile')
    return redirect(request,'update_profile.html',{'profile':profile})

@login_required
def order_detail(request,id):
    order=Order.objects.get(id=id,user=request.user)
    return render(request,'order_detail.html',{'order':order})

def add_review(request,id):
    product=Products.objects.get(id=id)
    if request.method=="POST":
        rating=request.POST['rating']
        comment=request.POST['comment']
        Review.objects.create(
            product=product,user=request.user,rating=rating,comment=comment
        )
        return redirect('product_detail',id=id)
    return render(request,'add_review.html',{'product':product})


def add_wishlist(request,id):
    product=Products.objects.get(id=id)
    Wishlist.objects.get_or_create(user=request.user,product=product)
    return redirect('product_detail',id=id)

def wishlist(request):
    wishlist_items=Wishlist.objects.filter(user=request.user)
    return render(request,'wishlist.html',{'wishlist_items':wishlist_items})

def remove_wishlist(request,id):
    wishlist_item=Wishlist.objects.get(id=id)
    wishlist_item.delete()
    return redirect('wishlist')

def wishlist_to_cart(request,id):
    wishlist_item=Wishlist.objects.get(id=id)
    Cart.objects.get_or_create(user=request.user,product=wishlist_item.product)
    wishlist_item.delete()
    return redirect('cart')

def apply_coupon(request):
    if request.method=='POST':
        coupon_code=request.POST['coupon']
        try:
            coupon=Coupon.objects.get(code=coupon_code)
        except Coupon.DoesNotExist:
            return redirect('cart')
        if not coupon.active:
            return redirect('cart')

        if coupon.expiry_date:
            if coupon.expiry_date<timezone.now():
                return redirect('cart')

        cart_items=Cart.objects.filter(user=request.user)
        total=0
        for item in cart_items:
            total+=item.product.price*item.quantity
        if total<coupon.minimum_amount:
            return redirect('cart')
        discount_amount=(total*coupon.discount)/100
        final_amount=(total-discount_amount)
        request.session['coupon']=coupon.code
        request.session['discount']=float(discount_amount)
        request.session['final_amount']=float(final_amount)
        return redirect('cart')
        

def send_order_email(order):
    subject='Order Confirmed'
    message=f"""
    Hello {order.user.username},
    Your order has been placed
    successfully.

    order ID:{order.id}

    Total Amount:₹{order.total_amount}
    
    status:{order.status}

    Thank You for shopping with us.
    """

    send_mail(subject,message,'murthelp333@gmail.com',[order.user.email],fail_silently=False)


def send_payment_success_email(order):
    subject = "Payment Successful - My Shop"
    message = f"""
    Hello {order.user.username},
    
    Your payment has been received successfully.

    Order ID:{order.id}
    
    Amount Paid:₹{order.total_amount}
    
    Payment Status:SUCCESS
    
    Thank you for shopping with us.
    Your order will be processed soon.
    """
    send_mail(subject,message,'murthelp333@gmail.com',[order.user.email],fail_silently=False)



@login_required
def dashboard(request):
    orders=Order.objects.filter(user=request.user)
    total_orders=orders.count()
    total_spent=orders.aggregate(total=Sum('total_amount'))['total']
    recent_orders=orders.order_by('-created_at')[:5]
    return render(request,'dashboard.html',{'total_orders':total_orders,'total_spent':total_spent,'recent_orders':recent_orders})

def admin_dashboard(request):
    total_products=Products.objects.count()
    total_categories=Category.objects.count()
    total_orders=Order.objects.count()
    total_users=User.objects.count()
    total_sales=Order.objects.aggregate(Sum('total_amount'))['total_amount__sum']
    recent_orders=Order.objects.order_by('-created_at')[:5]
    context={
        'total_products':total_products,
        'total_categories':total_categories,
        'total_orders':total_orders,
        'total_users':total_users,
        'total_sales':total_sales,
        'recent_orders':recent_orders
        }
    return render(request,'admin_dashboard.html',context)

def admin_orders(request):
    orders=Order.objects.all().order_by('-created_at')
    context={'orders':orders}
    return render(request,'admin_orders.html',context)

def update_order_status(request,id):
    order=get_object_or_404(Order,id=id)
    if request.method=="POST":
        new_status=request.POST.get("status")
        order.status=new_status
        order.save()
        send_mail(subject=f"Order#{ order.id } Status Updated",
        message=f"""Hello {order.user.username},
        Your order status has been updated.
        Order ID:{order.id})
        New Status:{order.status}
        Total Amount:₹{order.total_amount}
        Thank You for Shopping with us.
        """,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[order.user.email])
    return redirect('admin_orders')
        

def generate_invoice(request,id):
    order=Order.objects.get(id=id)
    response=HttpResponse(content_type='application/pdf')
    response['Content-Disposition']=(f'attachment;filename="invoice_{order.id}.pdf"')
    pdf=SimpleDocTemplate(response,pagesize=A4)
    elements=[]
    styles=getSampleStyleSheet()
    title=Paragraph("🛒 ONLINE Shop<br/>INVOICE",styles['Title'])
    elements.append(title)
    elements.append(Spacer(1,20))
    customer=Paragraph(
        f"""
        <b>Customer Details</b><br/>
        Name:{order.user.username}<br/>
        Email:{order.user.email}<br/>
        Order ID:{order.id}<br/>
        Date:{order.created_at}
        """,
        styles['Normal']
    )
    elements.append(customer)
    elements.append(Spacer(1,20))
    data=[
        ["Product",
        "Quantity",
        "Price",
        "Total"]
    ]
    for item in order.orderitem_set.all():
        data.append([
            item.product.name,
            item.quantity,
            f"₹{item.price}",
            f"₹{item.price*item.quantity}"
        ])
    table=Table(data)
    table.setStyle(
        TableStyle(
            [
                ('BACKGROUND',(0,0),(-1,0),colors.grey),
                ('GRID',(0,0),(-1,-1),1,colors.black)
            ]
        )
    )
    elements.append(table)
    elements.append(Spacer(1,20))
    total=Paragraph(
        f"""
        <b>Total Amount:
        ₹{order.total_amount}</b>
        """,
        styles['Heading3']
    )
    elements.append(total)
    elements.append(Spacer(1,30))
    thank=Paragraph(
        "Thank you for shopping with us ❤️",
        styles['Normal']
    )
    elements.append(thank)
    pdf.build(elements)
    return response

def create_invoice_pdf(order):
    buffer=BytesIO()
    pdf=SimpleDocTemplate(buffer)
    styles=getSampleStyleSheet()
    content=[]
    content.append(
        Paragraph(
            "ONLINE SHOP INVOICE",
            styles['Title']
        )
    )
    content.append(
        Paragraph(
            f"Order ID:{order.id}",
            styles['Normal']
        )
    )
    content.append(Paragraph(
        f"Customer:{order.user.username}",
        styles['Normal']
    ))
    content.append(
        Paragraph(
            f"Total Amount:₹{order.total_amount}",
            styles['Normal']
        )
    )
    pdf.build(content)
    pdf_data=buffer.getvalue()
    buffer.close()
    return pdf_data

def send_invoice_email(order):
    pdf_file=create_invoice_pdf(order)
    email=EmailMessage(
        subject=f"Invoice for Order #{order.id}",
        body=f"""
        Hello {order.user.username},
        Thank you for your order.
        Your invoice is attached.
        Order ID:{order.id}
        Total Amount:₹{order.total_amount}
        Thank You!..
        """,
        from_email=settings.EMAIL_HOST_USER,
        to=[
            order.user.email
            ]
        )
    email.attach(
            f"invoice_{order.id}.pdf",
            pdf_file,
            "application/pdf")
    email.send()

def order_tracking(request,id):
    order=get_object_or_404(Order,id=id,user=request.user)
    steps=['Pending','Processing','Shipped','Delivered']
    current_index=steps.index(order.status)
    return render(request,'order_tracking.html',{'order':order,'steps':steps,'current_index':current_index})

def cancel_order(request,id):
    order=get_object_or_404(Order,id=id)
    if order.status in ["Pending","Processing"]:
        order.status="Cancelled"
        order.save()
    return redirect('order_detail',id=id)

def request_return(request,id):
    order=get_object_or_404(Order,id=id)
    if request.method == "POST":
        reason=request.POST.get("reason")
        order.return_requested=True
        order.return_reason=reason
        order.refund_status="Requested"
        order.save()
        return redirect('order_detail',id=order.id)
    return render(request,'return_request.html',{'order':order})

def admin_returns(request):
    orders=Order.objects.filter(return_requested=True)
    return render(request,'admin_returns.html',{'orders':orders})

def approve_return(request,id):
    order=get_object_or_404(Order,id=id)
    order.refund_status="Approved"
    order.save()
    return redirect('admin_returns')

def reject_return(request,id):
    order=get_object_or_404(Order,id=id)
    order.refund_status="Rejected"
    order.save()
    return redirect('admin_returns')

def complete_refund(request,id):
    order=get_object_or_404(Order,id=id)
    oeder.status="Refunded"
    order.refund_status="Completed"
    order.save()
    return redirect('admin_returns')

def coupon_list(request):
    coupons=Coupon.objects.all()
    return render(request,'coupon_list.html',{'coupons':coupons})

def add_coupon(request):
    if request.method == "POST":
        code=request.POST.get("code")
        discount=request.POST.get("discount")
        minimum=request.POST.get("minimum_amount")
        expiry=request.POST.get("expiry_date")
        active=request.POST.get("active")
        Coupon.objects.create(
            code=code,
            discount=discount,
            minimum_amount=minimum,
            expiry_date=expiry,
            active=True if active else False
        )
        return redirect('coupon_list')
    return render(request,'add_coupon.html')

def edit_coupon(request,id):
    coupon=get_object_or_404(Coupon,id=id)
    if request.method=="POST":
        coupon.code=request.POST.get("code")
        coupon.discount=request.POST.get("discount")
        coupon.minimum_amount=request.POST.get("minimum_amount")
        coupon.expiry_date=request.POST.get("expiry_date")
        coupon.active=True if request.POST.get("active") else False
        coupon.save()
        return redirect('coupon_list')
    return render(request,'edit_coupon.html',{'coupon':coupon})
def delete_coupon(request,id):
    coupon=get_object_or_404(Coupon,id=id)
    coupon.delete()
    return redirect('coupon_list')

def cod_payment(request):
    return render(request,'cash_on_delivery.html')

def upi_payment(request):
    cart_items=Cart.objects.filter(user=request.user)
    total=0
    for item in cart_items:
        total+=item.total_price()
    if request.method=="POST":
        upi_reference=request.POST['upi_reference']
        address=request.session.get('checkout_address')
        phone=request.session.get('checkout_phone')
        order=Order.objects.create(user=request.user,address=address,phone=phone,total_amount=total,payment_method="UPI",upi_reference=upi_reference)
        Payment.objects.create(order=order,payment_method="UPI",payment_status="Pending")
        for item in cart_items:
            Orderitem.objects.create(order=order,product=item.product,quantity=item.quantity,price=item.product.price)
            product=item.product
            product.stock-=item.quantity
            product.save()
        cart_items.delete()
        return redirect('payment_success')
    return render(request,'upi_payment.html',{'total':total})
#def low_stock_products(request):
