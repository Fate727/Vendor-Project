import os, uuid
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.storage import FileSystemStorage
from .models import Category, Product, Seller
from django.core.paginator import Paginator
from django.contrib import messages
from django.template.loader import render_to_string
from django.http import JsonResponse
import json
from UserModule.models import Transaction, Users
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models import Sum, Count
from decorators import login_required, seller_required
from django.db.models.functions import ExtractYear
from django.contrib.auth.hashers import make_password, check_password
from django.views.decorators.csrf import csrf_exempt
import re


@seller_required
@login_required
def dashboard(request):
    user_id = request.session.get('uid')
    
    if not user_id:
        messages.error(request, "You must be logged in to view dashboard.")
        return redirect('user-index')

    try:
        seller = Seller.objects.get(UserId__UserID=user_id, Status='accepted')
    except Seller.DoesNotExist:
        messages.error(request, "You are not an approved seller.")
        return redirect('user-index')

    today = timezone.now()
    
    # ========== GET FILTER PARAMETERS ==========
    selected_year = request.GET.get('year', today.year)
    selected_month = request.GET.get('month', today.month)
    
    try:
        selected_year = int(selected_year)
        selected_month = int(selected_month)
    except (ValueError, TypeError):
        selected_year = today.year
        selected_month = today.month
    
    # Validate month range
    if selected_month < 1 or selected_month > 12:
        selected_month = today.month
    
    # ========== MONTHS AND YEARS LIST FOR TEMPLATE ==========
    months_list = [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ]
    
    # Get all transactions for this seller
    transactions = Transaction.objects.filter(SellerID=seller)
    
    # Get available years from seller's transactions PLUS current year
    years_from_transactions = []
    if transactions.exists():
        from django.db.models.functions import ExtractYear
        year_dates = transactions.annotate(
            year=ExtractYear('CreatedAt')
        ).values('year').distinct().order_by('-year')
        years_from_transactions = [year['year'] for year in year_dates]
    
    # Always include current year in the list
    if today.year not in years_from_transactions:
        years_from_transactions.append(today.year)
    
    # Sort years in descending order
    years_from_transactions.sort(reverse=True)
    
    # Also include a few recent years (last 3 years) for better UX
    current_year = today.year
    recent_years = list(range(current_year - 2, current_year + 1))
    
    # Combine both lists and remove duplicates
    all_years = list(set(years_from_transactions + recent_years))
    all_years.sort(reverse=True)
    
    # Limit to reasonable range (last 10 years max)
    years_range_list = all_years[:10]
    
    # ========== CREATE DATE RANGE FOR SELECTED MONTH/YEAR ==========
    month_start = datetime(selected_year, selected_month, 1)
    if selected_month == 12:
        month_end = datetime(selected_year + 1, 1, 1)
    else:
        month_end = datetime(selected_year, selected_month + 1, 1)
    
    # Convert to timezone aware
    if timezone.is_naive(month_start):
        month_start = timezone.make_aware(month_start)
    if timezone.is_naive(month_end):
        month_end = timezone.make_aware(month_end)
    
    # ========== MONTHLY METRICS (LAST 30 DAYS) - Always shows last 30 days ==========
    thirty_days_ago = today - timedelta(days=30)
    
    monthly_transactions = transactions.filter(
        CreatedAt__gte=thirty_days_ago,
        Status='completed'
    )
    
    monthly_earnings = monthly_transactions.aggregate(
        total=Sum('TotalAmount')
    )['total'] or 0
    
    monthly_orders = monthly_transactions.count()
    monthly_customers = monthly_transactions.values('UserID').distinct().count()
    
    # ========== SELECTED MONTH METRICS ==========
    selected_month_transactions = transactions.filter(
        CreatedAt__gte=month_start,
        CreatedAt__lt=month_end,
        Status='completed'
    )
    
    selected_month_earnings = selected_month_transactions.aggregate(
        total=Sum('TotalAmount')
    )['total'] or 0
    
    selected_month_orders = selected_month_transactions.count()
    selected_month_customers = selected_month_transactions.values('UserID').distinct().count()
    
    # ========== CHART DATA FOR SELECTED MONTH ==========
    import calendar
    days_in_month = calendar.monthrange(selected_year, selected_month)[1]
    
    # Initialize arrays for the month
    date_labels = [f"Day {day}" for day in range(1, days_in_month + 1)]
    daily_totals = [0] * days_in_month
    daily_breakdown = {str(i): [] for i in range(days_in_month)}
    
    # Group transactions by day
    for transaction in selected_month_transactions:
        day_index = transaction.CreatedAt.day - 1  # 0-based index
        if 0 <= day_index < len(daily_totals):
            # Add to daily total
            daily_totals[day_index] += float(transaction.TotalAmount or 0)
            
            # Add product breakdown if available
            try:
                if transaction.Products:
                    products_data = transaction.Products
                    
                    if isinstance(products_data, str):
                        import json as json_module
                        products_data = json_module.loads(products_data)
                    
                    if isinstance(products_data, list) and len(products_data) > 0:
                        for product_item in products_data:
                            if isinstance(product_item, dict):
                                product_name = product_item.get('product_name', 'Product')
                                quantity = product_item.get('quantity', 1)
                                unit_price = product_item.get('unit_price', 0)
                                
                                # Add product info for each quantity
                                for _ in range(int(quantity)):
                                    daily_breakdown[str(day_index)].append({
                                        'name': product_name[:20] + "..." if len(product_name) > 20 else product_name,
                                        'price': float(unit_price)
                                    })
            except Exception as e:
                print(f"Error processing product breakdown: {e}")
    
    # Filter to only show days with sales
    filtered_labels = []
    filtered_totals = []
    filtered_breakdown = {}
    
    for i, total in enumerate(daily_totals):
        if total > 0:
            filtered_labels.append(f"Day {i+1}")
            filtered_totals.append(total)
            filtered_breakdown[str(len(filtered_totals) - 1)] = daily_breakdown[str(i)]
    
    # If no sales in selected month, show example data for first 7 days
    if not filtered_totals:
        # Show example for first 7 days of the month
        filtered_labels = [f"Day {day}" for day in range(1, 8) if day <= days_in_month]
        filtered_totals = [0] * len(filtered_labels)
        filtered_breakdown = {str(i): [] for i in range(len(filtered_labels))}
    
    # Prepare chart data
    chart_data = {
        'daily_totals': filtered_totals,
        'daily_breakdown': filtered_breakdown,
        'date_labels': filtered_labels,
        'has_sales_data': any(total > 0 for total in filtered_totals),
        'total_last_7_days': sum(filtered_totals[:7]) if filtered_totals else 0
    }
    
    chart_data_json = json.dumps(chart_data)
    
    # ========== RECENT ORDERS (Always show latest 10) ==========
    recent_transactions = transactions.order_by('-CreatedAt')[:10]
    recent_orders = []
    
    for transaction in recent_transactions:
        product_name = "Product"
        
        try:
            if transaction.Products:
                products_data = transaction.Products
                
                if isinstance(products_data, str):
                    import json as json_module
                    products_data = json_module.loads(products_data)
                
                if isinstance(products_data, list) and len(products_data) > 0:
                    first_product = products_data[0]
                    
                    if isinstance(first_product, dict):
                        product_name = first_product.get('product_name', 'Product')
                    elif isinstance(first_product, str):
                        product_name = first_product
                    else:
                        product_name = str(first_product)
                    
                    if len(product_name) > 30:
                        product_name = product_name[:30] + "..."
        except Exception as e:
            print(f"Error parsing product data: {e}")
            product_name = "Product"
        
        recent_orders.append({
            'order_number': f"#TR{str(transaction.TransactionID).zfill(6)}",
            'product_name': product_name,
            'order_date': transaction.CreatedAt.strftime('%d %b %Y'),
            'price': f"Rs. {transaction.TotalAmount:,.2f}",
            'status': transaction.Status,
            'status_class': {
                'pending': 'bg-light-warning text-dark-warning',
                'completed': 'bg-light-success text-dark-success',
                'cancelled': 'bg-light-danger text-dark-danger'
            }.get(transaction.Status, 'bg-light-secondary text-dark-secondary')
        })
    
    # ========== ORDER STATUS STATISTICS (All time) ==========
    completed_count = transactions.filter(Status='completed').count()
    pending_count = transactions.filter(Status='pending').count()
    cancelled_count = transactions.filter(Status='cancelled').count()
    
    # Calculate percentages
    total_transactions = completed_count + pending_count + cancelled_count
    
    if total_transactions > 0:
        completed_percentage = (completed_count / total_transactions) * 100
        pending_percentage = (pending_count / total_transactions) * 100
        cancelled_percentage = (cancelled_count / total_transactions) * 100
    else:
        completed_percentage = 0
        pending_percentage = 0
        cancelled_percentage = 0
    
    # Get selected month name
    selected_month_name = next((name for num, name in months_list if num == selected_month), "Unknown")
    
    # ========== PREPARE CONTEXT ==========
    
    context = {
        'seller': seller,
        'monthly_earnings': monthly_earnings,
        'monthly_orders': monthly_orders,
        'monthly_customers': monthly_customers,
        'recent_orders': recent_orders,
        'completed_count': completed_count,
        'pending_count': pending_count,
        'cancelled_count': cancelled_count,
        'completed_percentage': completed_percentage,
        'pending_percentage': pending_percentage,
        'cancelled_percentage': cancelled_percentage,
        'current_year': today.year,
        'current_month': today.month,
        'selected_year': selected_year,
        'selected_month': selected_month,
        'selected_month_name': selected_month_name,
        'selected_month_earnings': selected_month_earnings,
        'selected_month_orders': selected_month_orders,
        'selected_month_customers': selected_month_customers,
        'months': months_list,
        'years_range': years_range_list,  # This now includes current year
        'sales_chart_data_json': chart_data_json,
        'total_transactions': total_transactions,
    }
    
    return render(request, 'SellerModule/dashboard.html', context)

@login_required
@seller_required
def seller_profile(request):
    # Get user ID from session (using 'uid' as per your logs)
    user_id = request.session.get('uid')
    
    if not user_id:
        messages.error(request, "Please login to access seller profile")
        return redirect('login')
    
    try:
        user = Users.objects.get(UserID=user_id)
    except Users.DoesNotExist:
        messages.error(request, "User not found")
        return redirect('login')
    
    try:
        seller = Seller.objects.get(UserId=user)
    except Seller.DoesNotExist:
        messages.error(request, "Seller profile not found. Please complete seller registration.")
        return redirect('requestseller')
    
    if request.method == 'POST':
        form_type = request.POST.get('form_type', '')
        
        if form_type == 'personal_info':
            return handle_personal_info(request, user)
        elif form_type == 'store_info':
            return handle_store_info(request, seller, user)
        elif form_type == 'change_password':
            return handle_password_change(request, user)
    
    # Get product statistics based on Stock
    total_products = Product.objects.filter(SellerID=seller).count()
    
    # Active products: Stock > 0 (you can adjust threshold as needed)
    active_products = Product.objects.filter(SellerID=seller, Stock__gt=0).count()
    
    # Products that need restocking (Stock <= 0)
    low_stock_products = Product.objects.filter(SellerID=seller, Stock__lte=0).count()
    
    # For now, use placeholder values for orders
    pending_orders = 0
    completed_orders = 0
    
    context = {
        'user': user,
        'seller': seller,
        'total_products': total_products,
        'active_products': active_products,
        'low_stock_products': low_stock_products,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
    }
    
    return render(request, 'SellerModule/seller_profile.html', context)


# Helper functions for form handling
def handle_personal_info(request, user):
    """Handle personal information update"""
    try:
        # Get form data
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        
        # Validation
        if not all([full_name, email, phone, address]):
            messages.error(request, "All personal information fields are required")
            return redirect('profile-seller')
        
        # Email validation
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            messages.error(request, "Please enter a valid email address")
            return redirect('profile-seller')
        
        # Phone validation
        if not re.match(r'^\+?[0-9\s\-\(\)]{7,15}$', phone):
            messages.error(request, "Please enter a valid phone number")
            return redirect('profile-seller')
        
        # Check email uniqueness
        if Users.objects.filter(Email=email).exclude(UserID=user.UserID).exists():
            messages.error(request, "Email is already registered with another account")
            return redirect('profile-seller')
        
        # Update user
        user.FullName = full_name
        user.Email = email
        user.Phone = phone
        user.Address = address
        user.save()
        
        messages.success(request, "Personal information updated successfully!")
        
    except Exception as e:
        messages.error(request, f"Error updating personal information: {str(e)}")
    
    return redirect('profile-seller')

def handle_store_info(request, seller, user):
    """Handle store information update"""
    try:
        # Get form data
        store_name = request.POST.get('store_name', '').strip()
        store_address = request.POST.get('store_address', '').strip()
        license_number = request.POST.get('license_number', '').strip()
        pan = request.POST.get('pan', '').strip().upper()
        
        # Validation
        if not all([store_name, store_address, license_number, pan]):
            messages.error(request, "All store information fields are required")
            return redirect('profile-seller')
        
        # PAN validation
        if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', pan):
            messages.error(request, "Please enter a valid PAN number (format: ABCDE1234F)")
            return redirect('profile-seller')
        
        # Check PAN uniqueness
        if Seller.objects.filter(PAN=pan).exclude(SellerID=seller.SellerID).exists():
            messages.error(request, "PAN number is already registered with another seller")
            return redirect('profile-seller')
        
        # Store original status for comparison
        original_status = seller.Status
        had_changes = False
        
        # Check for actual changes
        if seller.StoreName != store_name:
            seller.StoreName = store_name
            had_changes = True
        
        if seller.StoreAddress != store_address:
            seller.StoreAddress = store_address
            had_changes = True
            
        if seller.ProductionLicenseNumber != license_number:
            seller.ProductionLicenseNumber = license_number
            had_changes = True
            
        if seller.PAN != pan:
            seller.PAN = pan
            had_changes = True
        
        # Only update if there are changes
        if had_changes:
            # If store was accepted and info changed, set to pending
            if original_status == 'accepted':
                seller.Status = 'pending'
                messages.warning(request, "Store information updated successfully! Your store status is now 'Pending' for re-verification.")
            else:
                messages.success(request, "Store information updated successfully!")
            
            seller.save()
        else:
            messages.info(request, "No changes were made to store information.")
        
    except Exception as e:
        messages.error(request, f"Error updating store information: {str(e)}")
    
    return redirect('profile-seller')

def handle_password_change(request, user):
    """Handle password change"""
    try:
        current_password = request.POST.get('current_password', '').strip()
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        
        # Validation
        if not all([current_password, new_password, confirm_password]):
            messages.error(request, "All password fields are required")
            return redirect('profile-seller')
        
        # Check current password
        if not check_password(current_password, user.Password):
            messages.error(request, "Current password is incorrect")
            return redirect('profile-seller')
        
        # Check password length
        if len(new_password) < 6:
            messages.error(request, "New password must be at least 6 characters long")
            return redirect('profile-seller')
        
        # Check password match
        if new_password != confirm_password:
            messages.error(request, "New password and confirmation do not match")
            return redirect('profile-seller')
        
        # Check if new password is different
        if check_password(new_password, user.Password):
            messages.error(request, "New password must be different from current password")
            return redirect('profile-seller')
        
        # Update password
        user.Password = make_password(new_password)
        user.save()
        
        # Clear session for security
        if 'uid' in request.session:
            del request.session['uid']
        request.session.flush()
        
        messages.success(request, "Password changed successfully! Please log in again with your new password.")
        return redirect('login')
        
    except Exception as e:
        messages.error(request, f"Error changing password: {str(e)}")
        return redirect('profile-seller')


# Helper function to normalize product images
def normalize_images(product):
    if product.Images:
        if isinstance(product.Images, str):
            try:
                product.Images = json.loads(product.Images)
            except:
                product.Images = []
        elif isinstance(product.Images, list):
            pass
        # Normalize slashes
        product.Images = [img.replace("\\", "/") for img in product.Images]
    else:
        product.Images = []

# Product Section view
@seller_required
@login_required
def productSection(request):
    user_id = request.session.get('uid')
    if not user_id:
        messages.error(request, "You must be logged in to view products.")
        return redirect('user-index')

    try:
        seller = Seller.objects.get(UserId__UserID=user_id, Status='accepted')
    except Seller.DoesNotExist:
        messages.error(request, "You are not an approved seller.")
        return redirect('dashboard')

    products = Product.objects.filter(SellerID=seller).select_related('Category').order_by('-ProductID')

    # Optional filters
    status = request.GET.get('status')
    if status in ['active', 'disabled']:
        products = products.filter(Stock__gt=0 if status == 'active' else 0)

    query = request.GET.get('q')
    if query:
        products = products.filter(ProductName__icontains=query)

    # Normalize images
    for product in products:
        normalize_images(product)

    paginator = Paginator(products, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj,
        'initial_total': products.count()
    }
    return render(request, 'SellerModule/ProductSection.html', context)

# AJAX Products view

def ajax_products(request):
    user_id = request.session.get('uid')
    if not user_id:
        return JsonResponse({'html': '', 'pagination': ''})

    try:
        seller = Seller.objects.get(UserId__UserID=user_id, Status='accepted')
    except Seller.DoesNotExist:
        return JsonResponse({'html': '', 'pagination': ''})

    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    page = int(request.GET.get('page', 1))

    products = Product.objects.filter(SellerID=seller).select_related('Category').order_by('-ProductID')

    if q:
        products = products.filter(ProductName__icontains=q)
    if status:
        products = products.filter(Stock__gt=0 if status == 'active' else 0)

    # Normalize images
    for product in products:
        normalize_images(product)

    paginator = Paginator(products, 5)
    paged_products = paginator.get_page(page)

    rows_html = render_to_string(
        'SellerModule/partials/_product_rows.html',
        {'products': paged_products},
        request=request
    )
    pagination_html = render_to_string(
        'SellerModule/partials/_product_pagination.html',
        {'products': paged_products},
        request=request
    )

    return JsonResponse({'html': rows_html, 'pagination': pagination_html})


@seller_required
@login_required
def categorySection(request):
    # Fetch all categories
    categories = Category.objects.all().order_by('-category_id')

    # Optional: filter by status
    status = request.GET.get('status')
    if status in ['active', 'disabled']:
        categories = categories.filter(status=status)

    # Optional: search by name
    query = request.GET.get('q')
    if query:
        categories = categories.filter(name__icontains=query)

    # Pagination (5 categories per page)
    paginator = Paginator(categories, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'categories': page_obj,
        'initial_total': categories.count()
    }
    return render(request, 'SellerModule/CategorySection.html', context)


def ajax_categories(request):
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    page = int(request.GET.get('page', 1))

    categories = Category.objects.all().order_by('-category_id')

    # Search filter
    if q:
        categories = categories.filter(name__icontains=q)

    # Status filter
    if status:
        if status == 'active':
            categories = categories.filter(status='active')
        elif status == 'disabled':
            categories = categories.filter(status='disabled')

    # Pagination
    paginator = Paginator(categories, 10)
    paged_categories = paginator.get_page(page)

    # Render partials
    rows_html = render_to_string('SellerModule/partials/_category_rows.html', {'categories': paged_categories})
    pagination_html = render_to_string('SellerModule/partials/_category_pagination.html', {'categories': paged_categories})

    return JsonResponse({'html': rows_html, 'pagination': pagination_html})

@seller_required
@login_required
def AddProduct(request):
    categories = Category.objects.filter(status="active")

    user_id = request.session.get('uid')
    if not user_id:
        messages.error(request, "You must be logged in to add products.")
        return redirect('login')

    try:
        seller = Seller.objects.get(UserId__UserID=user_id, Status='accepted')
    except Seller.DoesNotExist:
        messages.error(request, "You are not an approved seller.")
        return redirect('dashboard')

    if request.method == "POST":
        product_name = request.POST.get("product_name")
        company_name = request.POST.get("company_name")
        category_id = request.POST.get("category")
        stock = int(request.POST.get("stock", 0))

        sub_categories = request.POST.getlist("sub_category[]")
        unit_names = request.POST.getlist("unit_name[]")
        unit_quantities = request.POST.getlist("unit_quantity[]")
        unit_prices = request.POST.getlist("unit_price[]")
        spec_names = request.POST.getlist("spec_name[]")
        spec_values = request.POST.getlist("spec_value[]")
        images = request.FILES.getlist("images")
        description = request.POST.get("description", "")

        subcategories = sub_categories if sub_categories else []
        units = []
        for i in range(len(unit_names)):
            # guard against uneven lists
            if i < len(unit_quantities) and i < len(unit_prices):
                units.append({
                    "unit": unit_names[i],
                    "quantities": unit_quantities[i],
                    "price": unit_prices[i],
                })

        specifications = []
        for i in range(len(spec_names)):
            if i < len(spec_values):
                specifications.append({
                    "name": spec_names[i],
                    "value": spec_values[i],
                })

        # ✅ Save images
        image_list = []
        if images:
            folder_path = os.path.join(settings.MEDIA_ROOT, 'products')
            os.makedirs(folder_path, exist_ok=True)
            for image in images:
                ext = os.path.splitext(image.name)[1]
                unique_filename = f"{uuid.uuid4()}{ext}"
                fs = FileSystemStorage(location=folder_path)
                filename = fs.save(unique_filename, image)
                image_list.append(f"products/{filename}")

        category = get_object_or_404(Category, pk=category_id)

        Product.objects.create(
            SellerID=seller,
            CompanyName=company_name,
            ProductName=product_name,
            Stock=stock,
            Category=category,
            SubCategories=subcategories,
            Units=units,
            Specifications=specifications,
            Images=image_list,
            Description=description,
        )

        messages.success(request, "Product added successfully!")
        return redirect("products-index")

    return render(request, "SellerModule/AddProducts.html", {"categories": categories})


def DeleteProductImage(request, product_id, image_index):
    product = get_object_or_404(Product, pk=product_id)
    
    try:
        removed_image = product.Images.pop(image_index)
        product.save()
        messages.success(request, f"Image '{removed_image}' deleted successfully.")
    except IndexError:
        messages.error(request, "Invalid image index.")

    return redirect('edit-product', product_id=product_id)

@seller_required
@login_required
def edit_product(request, product_id):
    user_id = request.session.get('uid')
    if not user_id:
        messages.error(request, "You must be logged in.")
        return redirect('login')

    # Ensure the product belongs to the logged-in seller
    product = get_object_or_404(Product, ProductID=product_id, SellerID__UserId__UserID=user_id)
    categories = Category.objects.filter(status="active")

    # Convert possible JSON fields safely
    def to_list(field):
        if isinstance(field, str):
            try:
                return json.loads(field)
            except:
                return []
        return field or []

    # Prepare lists for editing form
    product.Images = [img.replace("\\", "/") for img in to_list(product.Images)]
    product.Units = to_list(product.Units)
    product.SubCategories = to_list(product.SubCategories)
    product.Specifications = to_list(product.Specifications)

    if request.method == 'POST':
        # Basic info
        product.ProductName = request.POST.get('product_name')
        product.CompanyName = request.POST.get('company_name')
        product.Stock = int(request.POST.get('stock', 0))
        product.Category_id = request.POST.get('category')
        product.SubCategories = request.POST.getlist('sub_category[]')

        # Units (with quantity field support)
        unit_names = request.POST.getlist('unit_name[]')
        unit_quantities = request.POST.getlist('unit_quantity[]')
        unit_prices = request.POST.getlist('unit_price[]')

        product.Units = [
            {'unit': unit_names, 'quantities': unit_quantities, 'price': unit_prices} for unit_names, unit_quantities, unit_prices 
            in zip(unit_names, unit_quantities, unit_prices) if unit_names and unit_quantities and unit_prices
        ]
       

        # Specifications
        spec_names = request.POST.getlist('spec_name[]')
        spec_values = request.POST.getlist('spec_value[]')
        product.Specifications = [
            {'name': n, 'value': v} for n, v in zip(spec_names, spec_values) if n and v
        ]

        # Description
        product.Description = request.POST.get('description', '')

        # Handle new image uploads
        files = request.FILES.getlist('images')
        if files:
            folder_path = os.path.join(settings.MEDIA_ROOT, 'products')
            os.makedirs(folder_path, exist_ok=True)
            new_images = []

            for f in files:
                ext = os.path.splitext(f.name)[1]
                unique_filename = f"{uuid.uuid4()}{ext}"
                fs = FileSystemStorage(location=folder_path)
                filename = fs.save(unique_filename, f)
                new_images.append(f"products/{filename}")

            # Append new images instead of replacing old ones
            product.Images.extend(new_images)

        # Save product (JSON fields handled automatically)
        product.save()

        messages.success(request, "Product updated successfully!")
        return redirect('products-index')

    context = {
        'product': product,
        'categories': categories,
        'specs': product.Specifications,
        'units': product.Units,
    }
    return render(request, 'SellerModule/EditProduct.html', context)

@seller_required
@login_required
def delete_product(request, product_id):
    user_id = request.session.get('uid')
    if not user_id:
        messages.error(request, "You must be logged in to delete a product.")
        return redirect('login')

    try:
        seller = Seller.objects.get(UserId__UserID=user_id, Status='accepted')
    except Seller.DoesNotExist:
        messages.error(request, "You are not an approved seller.")
        return redirect('dashboard')

    # Use ProductID instead of id
    product = get_object_or_404(Product, ProductID=product_id, SellerID__UserId__UserID=user_id)
    product.delete()
    messages.success(request, "Product deleted successfully.")
    return redirect('products-index')

@seller_required
@login_required
def AddCategory(request):
    if request.method == 'POST':
        category_name = request.POST.get('category_name', '').strip()
        category_image = request.FILES.get('category_image')

        # Validation
        errors = []
        if not category_name:
            errors.append("Category name is required.")
        if not category_image:
            errors.append("Category image is required.")

        if not errors:
            # Folder for category images
            folder_path = os.path.join(settings.MEDIA_ROOT, 'categories')
            os.makedirs(folder_path, exist_ok=True)

            # Generate unique filename using GUID
            ext = os.path.splitext(category_image.name)[1]
            unique_filename = f"{uuid.uuid4()}{ext}"

            # Save file
            fs = FileSystemStorage(location=folder_path)
            filename = fs.save(unique_filename, category_image)

            # File URL
            file_url = os.path.join('categories', filename)

            # Save to database
            Category.objects.create(
                name=category_name,
                image=file_url
            )

            return render(request, 'SellerModule/AddCategory.html', {
                'message': 'Category added successfully!',
                'file_url': file_url
            })

        # If errors exist
        return render(request, 'SellerModule/AddCategory.html', {'errors': errors})

    return render(request, 'SellerModule/AddCategory.html')

@seller_required
@login_required
def EditCategory(request, category_id):
    category = get_object_or_404(Category, category_id=category_id)

    if request.method == 'POST':
        category_name = request.POST.get('category_name', '').strip()
        category_image = request.FILES.get('category_image')
        status = request.POST.get('Status', 'active')

        # Validation
        if not category_name:
            messages.error(request, "Category name is required.")
        else:
            category.name = category_name
            category.status = status

            if category_image:
                # Save new image
                folder_path = os.path.join(settings.MEDIA_ROOT, 'categories')
                os.makedirs(folder_path, exist_ok=True)

                ext = os.path.splitext(category_image.name)[1]
                unique_filename = f"{uuid.uuid4()}{ext}"

                fs = FileSystemStorage(location=folder_path)
                filename = fs.save(unique_filename, category_image)

                file_url = os.path.join('categories', filename)

                # (Optional) delete old image
                if category.image and os.path.exists(os.path.join(settings.MEDIA_ROOT, str(category.image))):
                    try:
                        os.remove(os.path.join(settings.MEDIA_ROOT, str(category.image)))
                    except:
                        pass

                category.image = file_url

            category.save()
            messages.success(request, "Category updated successfully!")
            return redirect('category-index')

        # If errors, re-render form
        return render(request, 'SellerModule/EditCategory.html', {
            'category': category
        })

    return render(request, 'SellerModule/EditCategory.html', {'category': category})

@seller_required
@login_required
def DeleteCategory(request, category_id):
    category = get_object_or_404(Category, category_id=category_id)

    try:
        # (Optional) delete image file
        if category.image and os.path.exists(os.path.join(settings.MEDIA_ROOT, str(category.image))):
            try:
                os.remove(os.path.join(settings.MEDIA_ROOT, str(category.image)))
            except:
                pass

        category.delete()
        messages.success(request, "Category deleted successfully!")
    except Exception as e:
        messages.error(request, f"Error deleting category: {str(e)}")

    return redirect('category-index')


# Order Section
@seller_required
@login_required
def Order(request):
    user_id = request.session.get('uid')
    if not user_id:
        messages.error(request, "Please login to view orders.")
        return redirect('/')
    
    try:
        # 1. Get user
        user = Users.objects.get(UserID=user_id)
        
        # 2. Get seller using correct field name: UserId
        seller = Seller.objects.get(UserId=user)
        
        # 3. Get transactions for this seller
        all_transactions = Transaction.objects.filter(SellerID=seller).order_by('-CreatedAt')
        
        # 4. Apply search filter
        search_query = request.GET.get('search', '')
        transactions_list = []
        
        for transaction in all_transactions:
            # Skip if doesn't match search
            if search_query:
                if transaction.Products and len(transaction.Products) > 0:
                    product_data = transaction.Products[0]
                    product_name = product_data.get('product_name', '').lower()
                    if search_query.lower() not in product_name:
                        continue
            transactions_list.append(transaction)
        
        # 5. Apply status filter
        status_filter = request.GET.get('status', '')
        if status_filter:
            transactions_list = [t for t in transactions_list if t.Status == status_filter]
        
        # 6. Get product details for all transactions
        order_data = []
        
        for transaction in transactions_list:
            if transaction.Products and len(transaction.Products) > 0:
                product_data = transaction.Products[0]
                product_id = product_data.get('product_id')
                
                # Initialize product object
                product_obj = None
                
                # Try to get the actual Product object
                if product_id:
                    try:
                        product_obj = Product.objects.get(
                            ProductID=product_id,
                            SellerID=seller
                        )
                    except Product.DoesNotExist:
                        product_obj = None
                
                order_data.append({
                    'transaction': transaction,
                    'product_data': product_data,
                    'product_obj': product_obj,  # This will be None or Product object
                })
        
        # 7. Pagination
        paginator = Paginator(order_data, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'orders': page_obj,  # Changed from transactions_data to orders
            'search_query': search_query,
            'status_filter': status_filter,
            'total_orders': len(order_data),
        }
        
        return render(request, 'SellerModule/Order.html', context)
        
    except Users.DoesNotExist:
        messages.error(request, "User not found.")
        request.session.flush()
        return redirect('/')
    except Seller.DoesNotExist:
        messages.error(request, "Seller profile not found.")
        return redirect('/seller/')
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('/')
    
@seller_required
@login_required
def update_order_status(request, transaction_id, new_status=None):

    user_id = request.session.get('uid')
    if not user_id:
        messages.error(request, "Please login to update order status.")
        return redirect('user-index')
    
    try:
        # Get user and seller
        user = Users.objects.get(UserID=user_id)
        seller = Seller.objects.get(UserId=user)
        
        # Get the transaction
        transaction = Transaction.objects.get(
            TransactionID=transaction_id,
            SellerID=seller
        )
        
        # Get new_status from POST if not in URL
        if new_status is None and request.method == 'POST':
            new_status = request.POST.get('status')
        
        # Validate the new status
        valid_statuses = ['pending', 'completed', 'cancelled']
        if new_status not in valid_statuses:
            messages.error(request, "Invalid status provided.")
            return redirect('order-seller')
        
        # Update the status
        transaction.Status = new_status
        transaction.save()
        
        # Success message
        status_display = dict(Transaction.TRANSACTION_STATUS).get(new_status, new_status)
        messages.success(request, f"Order #{transaction_id} has been marked as {status_display}.")
        
        return redirect('order-detail', transaction_id=transaction_id)
        
    except Users.DoesNotExist:
        messages.error(request, "User not found.")
        request.session.flush()
        return redirect('user-index')
    except Seller.DoesNotExist:
        messages.error(request, "Seller profile not found.")
        return redirect('user-index')
    except Transaction.DoesNotExist:
        messages.error(request, "Order not found.")
        return redirect('order-seller')
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('order-seller')
    
@login_required
@seller_required
def order_detail_view(request, transaction_id):
    # Check if user is logged in
    user_id = request.session.get('uid')
    if not user_id:
        messages.error(request, "Please login to view order details.")
        return redirect('/')
    
    try:
        user = Users.objects.get(UserID=user_id)
        
        seller = Seller.objects.get(UserId=user)
        
        try:
            transaction = Transaction.objects.get(
                TransactionID=transaction_id,
                SellerID=seller
            )
        except Transaction.DoesNotExist:
            messages.error(request, "Order not found or you don't have permission to view it.")
            return redirect('order-seller')
        
        # 4. Parse products from JSON - USING THE EXACT STRUCTURE YOU SHARED
        order_items = []
        total_items = 0
        
        if transaction.Products:
            # Debug: Print the raw data
            print(f"DEBUG: Raw Products data: {transaction.Products}")
            print(f"DEBUG: Type: {type(transaction.Products)}")
            
            # Handle string or list
            products_data = transaction.Products
            if isinstance(transaction.Products, str):
                try:
                    import json
                    products_data = json.loads(transaction.Products)
                except json.JSONDecodeError:
                    products_data = []
            
            print(f"DEBUG: Parsed data: {products_data}")
            print(f"DEBUG: Number of items: {len(products_data)}")
            
            for product_data in products_data:
                print(f"DEBUG: Processing item: {product_data}")
                
                product_id = product_data.get('product_id')
                product_obj = None
                
                # Try to get the actual Product object
                if product_id:
                    try:
                        product_obj = Product.objects.get(
                            ProductID=product_id,
                            SellerID=seller
                        )
                        print(f"DEBUG: Found product object: {product_obj.ProductName}")
                    except Product.DoesNotExist:
                        print(f"DEBUG: Product with ID {product_id} not found")
                        product_obj = None
                
                # Extract data using your exact keys
                product_name = product_data.get('product_name', f'Product ID: {product_id}')
                quantity = product_data.get('quantity', 1)
                unit = product_data.get('unit', 'piece')
                price = product_data.get('unit_price', 0)
                subtotal = product_data.get('subtotal', quantity * price)
                
                order_item = {
                    'product_data': product_data,
                    'product': product_obj,  # This matches your template
                    'product_name': product_name,
                    'quantity': quantity,
                    'unit': unit,
                    'price': price,
                    'total': subtotal,  # Use subtotal from data
                }
                order_items.append(order_item)
                total_items += quantity
        
        print(f"DEBUG: Created {len(order_items)} order items")
        
        # 5. Calculate shipping cost
        shipping_cost = 0
        if transaction.TotalAmount < 500:
            shipping_cost = 50
        
        grand_total = transaction.TotalAmount + shipping_cost
        
        # 6. Get customer information
        customer = transaction.UserID
        
        # 7. Prepare context
        context = {
            'user': user,
            'seller': seller,
            'transaction': transaction,
            'customer': customer,
            'shipping_address': customer.Address if customer.Address else "Address not provided",
            'order_items': order_items,
            'total_items': total_items,
            'subtotal': transaction.TotalAmount,
            'shipping_cost': shipping_cost,
            'grand_total': grand_total,
            'status_choices': dict(Transaction.TRANSACTION_STATUS),
            'order_date': transaction.CreatedAt.strftime("%B %d, %Y"),
            'order_time': transaction.CreatedAt.strftime("%I:%M %p"),
            'has_products': len(order_items) > 0,
        }
        
        return render(request, 'SellerModule/OrderDetail.html', context)
        
    except Users.DoesNotExist:
        messages.error(request, "User not found. Please login again.")
        request.session.flush()
        return redirect('/')
    except Seller.DoesNotExist:
        messages.error(request, "You need a seller account to view order details.")
        return redirect('/seller/')
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in order_detail_view: {str(e)}", exc_info=True)
        
        messages.error(request, f"An error occurred while loading order details: {str(e)}")
        return redirect('order-seller')
 
  
def logout_accout(request):
    request.session.flush()  # clear session
    messages.success(request, "You have been logged out successfully.")
    return redirect('user-index') 