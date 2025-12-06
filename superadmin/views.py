from django.shortcuts import render, redirect,get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from UserModule.models import Users
from SellerModule.models import Seller
from django.utils import timezone

# Create your views here.
def dashboard(request):
    return render(request, 'superadmin/dashboard.html')

#Need to add futher more like name search/ pagnation with limited rows.
def users(request):
    users = Users.objects.all().order_by('-UserID')
    return render(request,'superadmin/Users.html', {"users": users})


def addusers(request):

    role = request.session.get("role", "").lower()
    if role != "admin":
        messages.error(request, "You are not authorized to access this page.")
        return redirect("/")

    if request.method == "POST":
        fullname = request.POST.get("fullname")
        username = request.POST.get("username")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        address = request.POST.get("address")
        password = request.POST.get("password")

        if Users.objects.filter(UserName=username).exists():
            messages.error(request, "Username already exists")
            return redirect("addusers")

        # Hash the password before saving
        hashed_password = make_password(password)

        user = Users(
            FullName=fullname,
            UserName=username,
            Email=email,
            Phone=phone,
            Address=address,
            Password=hashed_password,  # store hashed password
            Role="basic",
            LoginAt=timezone.now(),
        )
        user.save()
        messages.success(request, "Customer created successfully.")
        return redirect("userslist-index")

    return render(request, "superadmin/addusers.html")

def edit_user(request, user_id):
    user = get_object_or_404(Users, UserID=user_id)

    if request.method == "POST":
        user.FullName = request.POST.get("fullname")
        user.UserName = request.POST.get("username")
        user.Email = request.POST.get("email")
        user.Phone = request.POST.get("phone")
        user.Address = request.POST.get("address")

        new_password = request.POST.get("password")
        hashed_password = make_password(new_password)
        if new_password:
            user.Password = hashed_password 

        user.save()
        return redirect("userslist-index")

    return render(request, "superadmin/edit_users.html", {"user": user})

def delete_item(request, user_id):
    if request.method == "POST":
        user = get_object_or_404(Users, UserID=user_id)
        user.delete()
        messages.success(request, "User deleted successfully.")
    return redirect('userslist-index')


#Vendors/Sellers
def vendorsrequest(request):
    # Get all seller requests
    sellers = Seller.objects.all().order_by('-SellerID')  # latest first
    return render(request, "superadmin/vendorrequest.html", {"sellers": sellers})

def seller_accept(request, seller_id):
    if request.method == "POST":
        seller = get_object_or_404(Seller, SellerID=seller_id)
        seller.Status = "accepted"
        seller.save()
        
        Users = seller.UserId
        Users.Role = "seller"
        Users.save()

        messages.success(request, f"Seller request for '{seller.StoreName}' accepted.")
    return redirect("vendorrequest")

def seller_reject(request, seller_id):
    if request.method == "POST":
        seller = get_object_or_404(Seller, SellerID=seller_id)
        seller.Status = "rejected"
        seller.save()
        messages.error(request, f"Seller request for '{seller.StoreName}' rejected.")
    return redirect("vendorrequest")

#logout
def logout_user(request):
    request.session.flush()  # clear session
    messages.success(request, "You have been logged out successfully.")
    return redirect('SignIn-index') 