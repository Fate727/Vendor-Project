from django.shortcuts import render,redirect, get_object_or_404
from decimal import Decimal
from .models import Users, Cart, Transaction
from SellerModule.models import Seller 
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from SellerModule.models import Product, Category
from django.http import JsonResponse
import json
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction

def index(request):
    categories = Category.objects.filter(status='active')
    products = Product.objects.filter(Category__status='active')[:8]
    return render(request, 'UserModule/Home.html', {
        'categories': categories,
        'products': products
    })


def Shop(request):
    categories = Category.objects.all()
    products = Product.objects.all()

    selected_categories = []
    search_query = ""

    if request.method == "POST":
        selected_categories = request.POST.getlist("categories")
        search_query = request.POST.get("search", "").strip()

        # --------------------------
        # Category Filter
        # --------------------------
        if selected_categories:
            selected_categories_int = [
                int(cat_id) for cat_id in selected_categories if cat_id.isdigit()
            ]
            products = products.filter(Category__in=selected_categories_int)

        # --------------------------
        # Search Filter (Product Name)
        # --------------------------
        if search_query:
            products = products.filter(ProductName__icontains=search_query)

    context = {
        "categories": categories,
        "products": products,
        "selected_categories": selected_categories,
        "search_query": search_query,
    }
    return render(request, "UserModule/Shop.html", context)


def product_quick_view(request, product_id):
    try:
        product = get_object_or_404(Product, ProductID=product_id)

        # Prepare image URLs (prepend MEDIA_URL)
        image_urls = []
        if product.Images:
            image_urls = [f"{settings.MEDIA_URL}{img}" for img in product.Images]

        data = {
            "name": product.ProductName,
            "category": product.Category.name if product.Category else "No category",
            "subcategories": product.SubCategories if product.SubCategories else [],
            "units": product.Units if product.Units else [],
            "company": product.CompanyName or "N/A",
            "stock": product.Stock,
            "specifications": product.Specifications if product.Specifications else [],
            "description": product.Description or "",
            "store_name": product.SellerID.StoreName if product.SellerID else "Unknown Store",
            "images": image_urls,
        }
        return JsonResponse(data)

    except Exception as e:
        print("Quick View Error:", e)
        return JsonResponse({"error": str(e)}, status=500)


def Store(request):
    sellers = Seller.objects.all()[:9]  # limit to 9 sellers
    seller_data = []

    for seller in sellers:
        # Get up to 3 products for this seller
        products = Product.objects.filter(SellerID=seller)[:3]

        # Collect subcategories from these products
        subcategories = []
        for prod in products:
            for sub in prod.SubCategories:
                if sub not in subcategories:  # avoid duplicates
                    subcategories.append(sub)
                if len(subcategories) >= 3:  # limit to 3
                    break
            if len(subcategories) >= 3:
                break

        seller_data.append({
            'seller': seller,
            'subcategories': subcategories,
        })

    total_sellers = Seller.objects.count()  # total number of vendors

    return render(request, 'UserModule/Store.html', {
        'seller_data': seller_data,
        'total_sellers': total_sellers
    })
    
    
def SignIn(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        try:
            user = Users.objects.get(UserName=username)
        except Users.DoesNotExist:
            user = None

        if user and check_password(password, user.Password):
            # Save session
            request.session['uid'] = user.UserID
            request.session['uname'] = user.UserName
            request.session['role'] = user.Role

            # Set session to expire after 24 hours
            request.session.set_expiry(24 * 60 * 60)  # 24 hours in seconds

            # Update LastLogin in the database
            user.LoginAt = timezone.now()
            user.save()

            # Redirect based on role
            role_lower = user.Role.lower()
            if role_lower == "admin":
                return redirect("superadmin_dashboard")
            elif role_lower == "seller":
                return redirect("seller-dashboard")
            else:
                return redirect("user-index")

        # Invalid credentials
        messages.error(request, "Invalid username or password.")
    
    return render(request, "UserModule/SignIn.html")


def SignUp(request):
    return render(request, 'UserModule/SignUp.html')

def Forgot(request):
    return render(request, 'UserModule/Forgot.html')

def About(request):
    return render(request, 'UserModule/About.html')

def Contact(request):
    return render(request, 'UserModule/Contact.html')

# All cart features sections
def Carts(request):
    if 'uid' not in request.session:
        return redirect('SignIn-index')

    user_id = request.session['uid']

    try:
        user = Users.objects.get(UserID=user_id)
    except Users.DoesNotExist:
        return redirect('SignIn-index')

    cart_items = Cart.objects.filter(
        UserID=user,
        Status="active"
    ).select_related("ProductID")

    subtotal = Decimal('0')
    for item in cart_items:
        selected_unit = item.SelectedUnit
        price = Decimal(selected_unit['price'])
        quantity = int(selected_unit['amount'])
        subtotal += price * quantity
    
    shipping = Decimal('5')  
    tax = (subtotal * Decimal('0.02')).quantize(Decimal('0.01')) 
    total = subtotal + shipping + tax

    return render(request, "UserModule/Carts.html", {
        "cart_items": cart_items,
        "subtotal": subtotal,
        "shipping": shipping,
        "tax": tax,
        "total": total
    })

@csrf_exempt
def add_to_cart(request, product_id):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

    try:
        # Get user from session
        user_id = request.session.get("uid")
        if not user_id:
            return JsonResponse({"status": "error", "redirect": "/SignIn"}, status=401)

        user = Users.objects.get(UserID=user_id)

        # Parse POST data
        data = json.loads(request.body.decode("utf-8"))
        quantity = int(data.get("quantity", 1))
        selected_unit = data.get("unit", {})

        if not selected_unit:
            return JsonResponse({"status": "error", "message": "No unit selected"}, status=400)

        # Fetch product
        product = get_object_or_404(Product, ProductID=product_id)
        unit_type = f"{selected_unit.get('unit')}-{selected_unit.get('amount')}"

        # Check if the same cart item exists but inactive
        cart_item = Cart.objects.filter(
            UserID=user,
            ProductID=product,
            UnitType=unit_type,
            Status="inactive"
        ).first()

        if cart_item:
            cart_item.Status = "active"
            cart_item.Quantity = quantity
            cart_item.SelectedUnit = selected_unit
            cart_item.save()
            message = f"{product.ProductName} re-activated in cart!"
        else:
            cart_item, created = Cart.objects.get_or_create(
                UserID=user,
                ProductID=product,
                UnitType=unit_type,
                Status="active",
                defaults={
                    "SelectedUnit": selected_unit,
                    "Quantity": quantity,
                }
            )
            if not created:
                cart_item.Quantity += quantity
                cart_item.save()
            message = f"{product.ProductName} added to cart!"

        return JsonResponse({"status": "success", "message": message})

    except Users.DoesNotExist:
        return JsonResponse({"status": "error", "redirect": "/SignIn"}, status=401)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

@csrf_exempt
def update_quantity(request):
    if request.method == "POST":
        cart_id = request.POST.get("cart_id")
        quantity = request.POST.get("quantity")

        if not cart_id or not quantity:
            return JsonResponse({"status": "error", "message": "Missing data"})

        try:
            quantity = int(quantity)
        except:
            return JsonResponse({"status": "error", "message": "Invalid quantity"})

        try:
            cart_item = Cart.objects.get(CartID=cart_id)  # FIXED HERE
        except Cart.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Cart item not found"})

        cart_item.Quantity = quantity
        cart_item.save()

        return JsonResponse({"status": "success", "message": "Quantity updated"})

    return JsonResponse({"status": "error", "message": "Invalid request method"})

@csrf_exempt
def remove_cart_item(request):
    if request.method == "POST":
        cart_id = request.POST.get("cart_id")

        if not cart_id:
            return JsonResponse({"status": "error", "message": "cart_id missing"})

        try:
            cart_item = Cart.objects.get(CartID=cart_id)
            cart_item.Status = "inactive"
            cart_item.save()
        except Cart.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Item not found"})

        return JsonResponse({"status": "success", "message": "Item removed"})

    return JsonResponse({"status": "error", "message": "Invalid request"})


# Checkout view with messages
@transaction.atomic
def checkout(request):
    if request.method == "POST":

        # 1️⃣ Check session UID
        session_uid = request.session.get('uid')
        if not session_uid:
            messages.error(request, "Please login first to proceed with checkout.")
            return redirect("login")

        # 2️⃣ Fetch user
        try:
            user = Users.objects.get(UserID=session_uid)

            # 2a️⃣ Role check
            if user.Role == "basic":
                pass  # allow ordering
            elif user.Role == "seller":
                messages.warning(request, "Sellers cannot place orders.")
                return redirect("seller-dashboard")
            elif user.Role == "admin":
                messages.warning(request, "Admins cannot place orders.")
                return redirect("superadmin_dashboard")
        except Users.DoesNotExist:
            messages.error(request, "User not found. Please login again.")
            return redirect("login")

        # 3️⃣ Payment method
        payment_method = request.POST.get("payment", "Cash")

        # 4️⃣ Fetch active cart items
        cart_items = Cart.objects.filter(UserID=user, Status="active").select_related('ProductID')
        if not cart_items.exists():
            messages.error(request, "Your cart is empty.")
            return redirect("Cart")

        out_of_stock_items = []
        successful_transactions = 0

        # 5️⃣ Process cart items & create separate transaction for each product
        for item in cart_items:
            product = item.ProductID

            if product.Stock < item.Quantity:
                out_of_stock_items.append(product.ProductName)
                continue

            # Deduct stock
            product.Stock -= item.Quantity
            product.save()

            price = item.SelectedUnit.get("price", 0)
            price = float(price)
            subtotal = price * item.Quantity

            # Get seller information
            seller_id = product.SellerID  # Adjust based on your model relationship

            # Create separate transaction for each product
            Transaction.objects.create(
                UserID=user,
                SellerID=seller_id,  # Store seller for this specific product
                Products=[{  # Store only this product's data
                    "product_id": product.ProductID,
                    "product_name": product.ProductName,
                    "unit": item.UnitType,
                    "quantity": item.Quantity,
                    "unit_price": price,
                    "subtotal": subtotal
                }],
                TotalAmount=subtotal,  # Only this product's total
                PaymentMethod=payment_method,
                Status="pending"
            )
            successful_transactions += 1

        # 6️⃣ Check if any transactions were successful
        if successful_transactions == 0:
            messages.error(
                request,
                f"The following items are out of stock: {', '.join(out_of_stock_items)}"
            )
            return redirect("Cart")

        # 7️⃣ Deactivate cart items (only after successful processing)
        cart_items.update(Status="inactive")

        # 8️⃣ Success message
        if out_of_stock_items:
            messages.success(
                request, 
                f"Order placed for {successful_transactions} item(s)! "
                f"Some items were out of stock: {', '.join(out_of_stock_items)}"
            )
        else:
            messages.success(request, f"Your order for {successful_transactions} item(s) has been placed successfully!")

        return redirect("Cart")

    # GET or other methods
    messages.error(request, "Invalid request method.")
    return redirect("Cart")


def Order(request):
    # 1️⃣ Check session user
    session_uid = request.session.get('uid')
    if not session_uid:
        return redirect("login")

    try:
        user = Users.objects.get(UserID=session_uid)
    except Users.DoesNotExist:
        return redirect("login")

    # 2️⃣ Fetch orders for this user
    orders = Transaction.objects.filter(UserID=user).order_by('-CreatedAt')

    # 3️⃣ Attach product images to each product in JSON
    for order in orders:
        for product in order.Products:
            try:
                prod_obj = Product.objects.get(ProductID=product["product_id"])
                # Assuming Images is a list or JSONField storing image paths
                if hasattr(prod_obj, "Images") and prod_obj.Images:
                    product["image"] = prod_obj.Images[0]  # first image
                else:
                    product["image"] = ""  # fallback if no image
            except Product.DoesNotExist:
                product["image"] = ""  # fallback if product missing

    # 4️⃣ Pass orders to template
    context = {
        "orders": orders
    }

    return render(request, 'UserModule/Order.html', context)


def AccountSetting(request):
    session_uid = request.session.get('uid')
    if not session_uid:
        return redirect("login")  # redirect if not logged in

    try:
        user = Users.objects.get(UserID=session_uid)
    except Users.DoesNotExist:
        return redirect("login")

    # 3️⃣ Pass user details to template
    context = {
        "user": user
    }

    return render(request, 'UserModule/AccountSetting.html', context)

def Address(request):
    return render(request, 'UserModule/Address.html')

def request_seller(request):
    # get logged in user from session
    user_id = request.session.get("uid")

    if not user_id:
        messages.error(request, "You must be logged in to request seller access.")
        return redirect("SignIn-index")

    user = Users.objects.get(UserID=user_id)

    # check if user already submitted
    seller_request = Seller.objects.filter(UserId=user).first()

    if request.method == "POST" and not seller_request:
        name = request.POST.get("StoreName")  # corrected here
        store = request.POST.get("StoreAddress")
        license_num = request.POST.get("ProductionLicenseNumber")
        pan = request.POST.get("PAN")

        Seller.objects.create(
            UserId=user,
            StoreName=name,
            StoreAddress=store,
            ProductionLicenseNumber=license_num,
            PAN=pan,
            Status="pending"
        )
        messages.success(request, "Your seller request has been submitted.")
        return redirect("requestseller")

    return render(request, "UserModule/requestseller.html", {"seller_request": seller_request})

def logout_accout(request):
    request.session.flush()  # clear session
    messages.success(request, "You have been logged out successfully.")
    return redirect('user-index') 