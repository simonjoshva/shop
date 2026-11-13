from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
def home(request):
    
    return render(request,'home.html')
def register(request):
    if request.method=="POST":
        username=request.POST['username']
        email=request.POST['email']
        password=request.POST['password']

        if User.objects.filter(username=username).exists():
            messages.error(request,"username already exists")
            return redirect('register')

        User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        messages.success(request,"Registrtion Successful")
        return redirect('login')

    return render(request,'register.html')
def user_login(request):
    if request.method=="POST":
        username=request.POST['username']
        password=request.POST['password']

        user=authenticate(  
            request,
            username=username,
            password=password
        )
        if user is not None:
            login(request,user)
            return redirect('home')
        else:
            messages.error(request,'Invalid Username or password')
    return render(request,'login.html')

def user_logout(request):
    logout(request)
    return redirect('login')

# Create your views here.
