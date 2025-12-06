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

def dashboard(request):
    return render(request, 'SellerModule/dashboard.html')


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
    
def update_order_status(request, transaction_id, new_status):
    # Check if user is logged in
    user_id = request.session.get('uid')
    if not user_id:
        messages.error(request, "Please login to update order status.")
        return redirect('user-index')  # Redirect to user home page
    
    try:
        # Get the user
        user = Users.objects.get(UserID=user_id)
        
        # Check if user is a seller
        try:
            seller = Seller.objects.get(UserId=user)
        except Seller.DoesNotExist:
            # User is not a seller, redirect to user dashboard
            messages.error(request, "Seller profile not found. Please register as a seller.")
            return redirect('user-index')  # Redirect to user home/dashboard
        
        # Get the transaction (ensure it belongs to this seller)
        transaction = Transaction.objects.get(
            TransactionID=transaction_id,
            SellerID=seller
        )
        
        # Validate the new status
        valid_statuses = ['pending', 'completed', 'cancelled']
        if new_status not in valid_statuses:
            messages.error(request, "Invalid status provided.")
            return redirect('order-index')  # Redirect to seller order list
        
        # Update the status
        transaction.Status = new_status
        transaction.save()
        
        # Success message based on new status
        status_display = dict(Transaction.TRANSACTION_STATUS).get(new_status, new_status)
        messages.success(request, f"Order #{transaction_id} has been marked as {status_display}.")
        
    except Users.DoesNotExist:
        messages.error(request, "User not found.")
        request.session.flush()
        return redirect('user-index')  # Redirect to user home/login
    
    except Transaction.DoesNotExist:
        # Order doesn't exist or doesn't belong to this seller
        messages.error(request, "Order not found or you don't have permission to update it.")
        return redirect('order-seller')  # Redirect to seller order list
    
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('order-seller')  # Redirect to seller order list
    
    # Redirect back to seller order list
    return redirect('order-seller')

def Orderdetail(request):
    return render(request, 'SellerModule/OrderDetaio.html')
    
def logout_accout(request):
    request.session.flush()  # clear session
    messages.success(request, "You have been logged out successfully.")
    return redirect('user-index') 