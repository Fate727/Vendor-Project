from django.shortcuts import render,redirect, get_object_or_404
from decimal import Decimal
from .models import Users, Cart, Transaction
from SellerModule.models import Seller 
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from SellerModule.models import Product, Category, Tag
from django.http import JsonResponse
import json
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.db import models
import re
from django.db.models import Q
from django.contrib.auth.hashers import make_password
from decorators import role_based_redirect, login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

@role_based_redirect
def index(request):
    categories = Category.objects.filter(status='active')
    products = Product.objects.filter(Category__status='active')[:8]
    return render(request, 'UserModule/Home.html', {
        'categories': categories,
        'products': products
    })


@role_based_redirect
def Shop(request):
    categories = Category.objects.all()
    products = Product.objects.all()
    
    # Get all tags from Tag model
    all_tags = Tag.objects.all()

    selected_categories = []
    selected_tags = []
    search_query = ""
    sort_by = request.GET.get('sort_by', 'featured')
    show_per_page = int(request.GET.get('show', 12))
    page = request.GET.get('page', 1)

    # Handle filters
    if request.method == "POST":
        selected_categories = request.POST.getlist("categories")
        selected_tags = request.POST.getlist("tags")
        search_query = request.POST.get("search", "").strip()
    
    elif request.method == "GET":
        selected_categories = request.GET.getlist('categories')
        selected_tags = request.GET.getlist('tags')
        search_query = request.GET.get('search', '').strip()
        
        # Handle single tag from URL parameter
        if 'tag' in request.GET and not selected_tags:
            tag = request.GET.get('tag')
            selected_tags = [tag]

    # Apply filters
    if selected_categories:
        selected_categories_int = [
            int(cat_id) for cat_id in selected_categories if cat_id.isdigit()
        ]
        products = products.filter(Category__in=selected_categories_int)

    if selected_tags:
        tag_filters = Q()
        for tag in selected_tags:
            tag_filters |= Q(SubCategories__contains=[tag])
        products = products.filter(tag_filters)

    if search_query:
        products = products.filter(ProductName__icontains=search_query)
    
    # Apply Sorting
    # Note: For JSON field sorting, we need to annotate first
    # For now, we'll use list sorting for price sorting
    # For date sorting, we can use database sorting
    
    if sort_by == 'newest':
        products = products.order_by('-CreatedAt')
    elif sort_by == 'oldest':
        products = products.order_by('CreatedAt')
    else:
        # For price sorting, we need to convert to list
        products_list = list(products)
        
        def get_min_price(units):
            if units and isinstance(units, list) and len(units) > 0:
                try:
                    if isinstance(units, str):
                        units = json.loads(units)
                    return min([float(unit.get('price', 0)) for unit in units])
                except:
                    return 0
            return 0
        
        if sort_by == 'price_low':
            products_list.sort(key=lambda p: get_min_price(p.Units))
        elif sort_by == 'price_high':
            products_list.sort(key=lambda p: get_min_price(p.Units), reverse=True)
        
        products = products_list  # Use sorted list
    
    # Filter tags based on selected categories
    filtered_tags = all_tags
    
    if selected_categories:
        selected_categories_int = [
            int(cat_id) for cat_id in selected_categories if cat_id.isdigit()
        ]
        filtered_tags = all_tags.filter(CategoryID__in=selected_categories_int)
    
    elif request.method == "GET" and 'tag' in request.GET and not selected_categories:
        tag = request.GET.get('tag')
        tag_obj = Tag.objects.filter(Name=tag).first()
        if tag_obj:
            filtered_tags = all_tags.filter(CategoryID=tag_obj.CategoryID)

    # Pagination
    # Check if products is a list or queryset
    if isinstance(products, list):
        paginator = Paginator(products, show_per_page)
    else:
        paginator = Paginator(products, show_per_page)
    
    try:
        products_page = paginator.page(page)
    except PageNotAnInteger:
        products_page = paginator.page(1)
    except EmptyPage:
        products_page = paginator.page(paginator.num_pages)

    context = {
        "categories": categories,
        "products": products_page,
        "all_tags": filtered_tags,
        "selected_categories": selected_categories,
        "selected_tags": selected_tags,
        "search_query": search_query,
        "sort_by": sort_by,
        "show_per_page": show_per_page,
        "current_page": products_page.number,
        "total_pages": paginator.num_pages,
        "total_products": paginator.count,
    }
    return render(request, "UserModule/Shop.html", context)


@role_based_redirect
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

@role_based_redirect
def Store(request):
    sellers = Seller.objects.filter(Status = "accepted")[:9]
    seller_data = []

    for seller in sellers:
        products = Product.objects.filter(SellerID=seller)[:3]


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

@role_based_redirect    
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
                return redirect("superadmin-dashboard")
            elif role_lower == "seller":
                return redirect("seller-dashboard")
            else:
                return redirect("user-index")

        # Invalid credentials
        messages.error(request, "Invalid username or password.")
    
    return render(request, "UserModule/SignIn.html")


def SignUp(request):
    if request.method == 'POST':
        # Get form data
        fullname = request.POST.get('fullname', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        
        # Default role is 'basic' - removed from form
        role = 'basic'

        # Validation flags
        is_valid = True
        
        # Validate Full Name
        if not fullname or len(fullname) > 100:
            messages.error(request, "Please enter a valid full name (max 100 characters)")
            is_valid = False
        
        # Validate Username
        if not username or len(username) > 50:
            messages.error(request, "Please enter a valid username (max 50 characters)")
            is_valid = False
        elif Users.objects.filter(UserName=username).exists():
            messages.error(request, "Username already exists")
            is_valid = False
        
        # Validate Email
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not email or not re.match(email_regex, email):
            messages.error(request, "Please enter a valid email address")
            is_valid = False
        elif Users.objects.filter(Email=email).exists():
            messages.error(request, "Email already registered")
            is_valid = False
        
        # Validate Phone (basic validation)
        if not phone or len(phone) > 15:
            messages.error(request, "Please enter a valid phone number (max 15 digits)")
            is_valid = False
        
        # Validate Address
        if not address or len(address) > 255:
            messages.error(request, "Please enter a valid address (max 255 characters)")
            is_valid = False
        
        # Validate Password
        if not password or len(password) < 6:
            messages.error(request, "Password must be at least 6 characters long")
            is_valid = False
        elif password != confirm_password:
            messages.error(request, "Passwords do not match")
            is_valid = False
        
        # If all validations pass, create user
        if is_valid:
            try:
                # Hash the password before saving
                hashed_password = make_password(password)
                
                user = Users.objects.create(
                    FullName=fullname,
                    UserName=username,
                    Email=email,
                    Phone=phone,
                    Address=address,
                    Password=hashed_password,
                    Role=role,  # Always set to 'basic'
                    LoginAt=timezone.now()   # Initially no login time
                )
                
                messages.success(request, "Account created successfully! Please sign in.")
                return redirect('SignIn-index')  # Redirect to sign in page
                
            except Exception as e:
                messages.error(request, f"Error creating account: {str(e)}")
        
        # If validation fails, preserve form data in session
        request.session['form_data'] = {
            'fullname': fullname,
            'username': username,
            'email': email,
            'phone': phone,
            'address': address,
            # No need to preserve role since it's always 'basic'
        }
    
    # Get saved form data if exists
    form_data = request.session.pop('form_data', {}) if request.method == 'GET' else {}
    
    return render(request, 'UserModule/SignUp.html', {
        'form_data': form_data,
        # Removed role_choices from context
    })

@login_required
def Forgot(request):
    return render(request, 'UserModule/Forgot.html')

def About(request):
    return render(request, 'UserModule/About.html')

def Contact(request):
    return render(request, 'UserModule/Contact.html')

# All cart features sections
@login_required
@role_based_redirect
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

@login_required
@role_based_redirect
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

@role_based_redirect
@login_required
@role_based_redirect
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

@login_required
@role_based_redirect
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
@login_required
@role_based_redirect
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

@login_required
@role_based_redirect
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

@login_required
@role_based_redirect
def AccountSetting(request):
    session_uid = request.session.get('uid')
    if not session_uid:
        return redirect("login")  # redirect if not logged in

    try:
        user = Users.objects.get(UserID=session_uid)
    except Users.DoesNotExist:
        return redirect("login")

    if request.method == 'POST':
        # Check which form was submitted
        if 'update_details' in request.POST:
            # Handle profile update
            fullname = request.POST.get('fullname', '').strip()
            email = request.POST.get('email', '').strip()
            phone = request.POST.get('phone', '').strip()
            
            # Validation
            is_valid = True
            
            # Validate Full Name
            if not fullname or len(fullname) > 100:
                messages.error(request, "Please enter a valid full name (max 100 characters)")
                is_valid = False
            
            # Validate Email
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not email or not re.match(email_regex, email):
                messages.error(request, "Please enter a valid email address")
                is_valid = False
            elif Users.objects.filter(Email=email).exclude(UserID=session_uid).exists():
                messages.error(request, "Email already registered with another account")
                is_valid = False
            
            # Validate Phone
            if not phone or len(phone) > 15:
                messages.error(request, "Please enter a valid phone number (max 15 digits)")
                is_valid = False
            
            if is_valid:
                try:
                    user.FullName = fullname
                    user.Email = email
                    user.Phone = phone
                    user.save()
                    messages.success(request, "Profile updated successfully!")
                except Exception as e:
                    messages.error(request, f"Error updating profile: {str(e)}")
        
        elif 'change_password' in request.POST:
            # Handle password change
            current_password = request.POST.get('current_password', '').strip()
            new_password = request.POST.get('new_password', '').strip()
            confirm_password = request.POST.get('confirm_password', '').strip()
            
            # Validation
            is_valid = True
            
            # Check current password
            if not check_password(current_password, user.Password):
                messages.error(request, "Current password is incorrect")
                is_valid = False
            
            # Validate new password
            if not new_password or len(new_password) < 6:
                messages.error(request, "New password must be at least 6 characters long")
                is_valid = False
            elif new_password == current_password:
                messages.error(request, "New password must be different from current password")
                is_valid = False
            elif new_password != confirm_password:
                messages.error(request, "New passwords do not match")
                is_valid = False
            
            if is_valid:
                try:
                    user.Password = make_password(new_password)
                    user.save()
                    messages.success(request, "Password changed successfully!")
                except Exception as e:
                    messages.error(request, f"Error changing password: {str(e)}")

    # 3️⃣ Pass user details to template
    context = {
        "user": user
    }

    return render(request, 'UserModule/AccountSetting.html', context)


@login_required
@role_based_redirect
def Address(request):
    return render(request, 'UserModule/Address.html')

@login_required
@role_based_redirect
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

@login_required
def logout_accout(request):
    request.session.flush()  # clear session
    messages.success(request, "You have been logged out successfully.")
    return redirect('user-index') 