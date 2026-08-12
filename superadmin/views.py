from django.shortcuts import render, redirect,get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from UserModule.models import Transaction, Users, Feedback
from SellerModule.models import Seller, Product
from UserModule.models import Users
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from decorators import admin_required, login_required
import json
from datetime import timedelta, datetime
from django.db.models import Sum, Count, Q
import re
from django.views.decorators.http import require_POST

@admin_required
def superadmin_dashboard(request):
    # Get the current admin user (already set by decorator)
    admin_user = request.user_obj
    
    today = timezone.now()
    thirty_days_ago = today - timedelta(days=30)
    
    # ========== GET FILTER PARAMETERS ==========
    # Get selected year and month from request (default to current)
    selected_year = request.GET.get('year', today.year)
    selected_month = request.GET.get('month', today.month)
    
    # Convert to integers
    try:
        selected_year = int(selected_year)
        selected_month = int(selected_month)
    except (ValueError, TypeError):
        selected_year = today.year
        selected_month = today.month
    
    # Validate month range
    if selected_month < 1 or selected_month > 12:
        selected_month = today.month
    
    # Create date range for selected month/year
    month_start = datetime(selected_year, selected_month, 1)
    if selected_month == 12:
        month_end = datetime(selected_year + 1, 1, 1)
    else:
        month_end = datetime(selected_year, selected_month + 1, 1)
    
    # Convert to timezone aware if needed
    if timezone.is_naive(month_start):
        month_start = timezone.make_aware(month_start)
    if timezone.is_naive(month_end):
        month_end = timezone.make_aware(month_end)
    
    # ========== MONTHS LIST FOR TEMPLATE ==========
    months_list = [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ]
    
    # Years range (last 5 years + current year)
    years_range_list = list(range(today.year - 5, today.year + 1))
    
    # ========== TOTAL PLATFORM STATISTICS ==========
    
    # Total Users Statistics (all time)
    total_users = Users.objects.filter(Q(Role='seller') | Q(Role='basic')).count()
    total_sellers = Users.objects.filter(Role='seller').count()
    total_customers = Users.objects.filter(Role='basic').count()
    
    # New users in selected month
    new_users_month = Users.objects.filter(
        CreatedAt__gte=month_start,
        CreatedAt__lt=month_end
    ).count()
    
    # Seller application statistics (all time)
    total_seller_applications = Seller.objects.all().count()
    pending_sellers = Seller.objects.filter(Status='pending').count()
    accepted_sellers = Seller.objects.filter(Status='accepted').count()
    rejected_sellers = Seller.objects.filter(Status='rejected').count()
    
    # ========== TOP SELLERS (FOR SELECTED MONTH) ==========
    
    # Get all sellers first
    all_sellers = Seller.objects.filter(Status='accepted')
    
    # Calculate seller sales for selected month
    formatted_top_sellers = []
    for seller in all_sellers:
        # Get transactions for this seller in selected month
        seller_transactions = Transaction.objects.filter(
            SellerID=seller,
            Status='completed',
            CreatedAt__gte=month_start,
            CreatedAt__lt=month_end
        )
        
        total_sales = seller_transactions.aggregate(
            total=Sum('TotalAmount')
        )['total'] or 0
        
        transaction_count = seller_transactions.count()
        
        if total_sales > 0:  # Only include sellers with sales
            formatted_top_sellers.append({
                'id': seller.SellerID,
                'store_name': seller.StoreName or 'Unnamed Store',
                'owner_name': seller.UserId.UserName,
                'total_sales': total_sales,
                'transactions': transaction_count,
                'avg_sale': total_sales / transaction_count if transaction_count > 0 else 0
            })
    
    # Sort by total sales (highest first)
    formatted_top_sellers.sort(key=lambda x: x['total_sales'], reverse=True)
    # Take top 10
    formatted_top_sellers = formatted_top_sellers[:10]
    
    # ========== FINANCIAL STATISTICS ==========
    
    # Total platform revenue (all time)
    total_revenue = Transaction.objects.filter(
        Status='completed'
    ).aggregate(total=Sum('TotalAmount'))['total'] or 0
    
    # Monthly revenue for selected month
    monthly_revenue = Transaction.objects.filter(
        Status='completed',
        CreatedAt__gte=month_start,
        CreatedAt__lt=month_end
    ).aggregate(total=Sum('TotalAmount'))['total'] or 0
    
    # Transaction counts
    total_transactions = Transaction.objects.all().count()
    monthly_transactions = Transaction.objects.filter(
        CreatedAt__gte=month_start,
        CreatedAt__lt=month_end
    ).count()
    
    # ========== CHART DATA (FOR SELECTED MONTH) ==========
    
    # Get daily sales for the selected month
    daily_sales = Transaction.objects.filter(
        Status='completed',
        CreatedAt__gte=month_start,
        CreatedAt__lt=month_end
    ).extra({'date': "date(CreatedAt)"}).values('date').annotate(
        daily_total=Sum('TotalAmount')
    ).order_by('date')
    
    # Process to get only days with sales
    date_labels = []
    daily_totals = []
    
    for day in daily_sales:
        date_obj = day['date']
        daily_total = float(day['daily_total'] or 0)
        
        if daily_total > 0:  # Only include days with sales
            date_labels.append(date_obj.strftime('%b-%d'))
            daily_totals.append(daily_total)
    
    # Prepare chart data - only include days with actual sales
    chart_data = {
        'dates': date_labels,
        'series': [{
            'name': f'Sales - {month_start.strftime("%B %Y")}',
            'data': daily_totals,
            'color': '#4e73df'
        }]
    }
    
    chart_data_json = json.dumps(chart_data)
    
    # ========== RECENT TRANSACTIONS (ALL TIME) ==========
    
    # Get recent transactions
    recent_transactions = Transaction.objects.select_related(
        'UserID', 'SellerID'
    ).order_by('-CreatedAt')[:15]
    
    formatted_recent_transactions = []
    
    for trans in recent_transactions:
        formatted_recent_transactions.append({
            'id': trans.TransactionID,
            'order_number': f"#TR{str(trans.TransactionID).zfill(6)}",
            'customer': trans.UserID.UserName if trans.UserID else "Unknown",
            'seller': trans.SellerID.StoreName if trans.SellerID else "Unknown",
            'seller_owner': trans.SellerID.UserId.UserName if trans.SellerID and trans.SellerID.UserId else "Unknown",
            'amount': f"Rs. {trans.TotalAmount:,.2f}",
            'date': trans.CreatedAt.strftime('%d %b %Y'),
            'status': trans.Status,
            'status_class': {
                'pending': 'bg-warning',
                'completed': 'bg-success',
                'cancelled': 'bg-danger'
            }.get(trans.Status, 'bg-secondary')
        })
    
    # ========== PREPARE CONTEXT ==========
    
    context = {
        # Admin info
        'admin_user': admin_user,
        
        # Filter parameters
        'selected_year': selected_year,
        'selected_month': selected_month,
        'current_year': today.year,
        'current_month': today.month,
        'month_name': month_start.strftime('%B'),
        
        # Template dropdown data
        'months': months_list,
        'years_range': years_range_list,
        
        # Platform statistics
        'total_users': total_users,
        'total_sellers': total_sellers,
        'total_customers': total_customers,
        'new_users_month': new_users_month,
        
        # Seller application statistics
        'total_seller_applications': total_seller_applications,
        'pending_sellers': pending_sellers,
        'accepted_sellers': accepted_sellers,
        'rejected_sellers': rejected_sellers,
        
        # Financial statistics
        'total_revenue': total_revenue,
        'monthly_revenue': monthly_revenue,
        'total_transactions': total_transactions,
        'monthly_transactions': monthly_transactions,
        
        # Top sellers data
        'top_sellers': formatted_top_sellers,
        'top_sellers_count': len(formatted_top_sellers),
        
        # Recent transactions
        'recent_transactions': formatted_recent_transactions,
        
        # Chart data
        'chart_data_json': chart_data_json,
        
        # Summary statistics
        'top_seller': formatted_top_sellers[0] if formatted_top_sellers else None,
        'total_monthly_sales': monthly_revenue,
        'chart_has_data': len(date_labels) > 0,
        'chart_days_count': len(date_labels),
    }
    
    return render(request, 'superadmin/dashboard.html', context)


@login_required
@admin_required
def admin_profile(request):
    # Get user ID from session
    user_id = request.session.get('uid')
    
    if not user_id:
        messages.error(request, "Please login to access admin profile")
        return redirect('login')
    
    try:
        user = Users.objects.get(UserID=user_id)
    except Users.DoesNotExist:
        messages.error(request, "User not found")
        return redirect('login')
    
    # Get admin statistics
    total_sellers = Seller.objects.count()
    active_sellers = Seller.objects.filter(Status='accepted').count()
    pending_sellers = Seller.objects.filter(Status='pending').count()
    rejected_sellers = Seller.objects.filter(Status='rejected').count()
    
    # Get total products across all sellers
    total_products = Product.objects.count()
    
    # Calculate total sales from completed transactions
    # Sum of TotalAmount for all completed transactions
    total_sales_result = Transaction.objects.filter(
        Status='completed'
    ).aggregate(
        total=Sum('TotalAmount')
    )
    
    # Get the total or default to 0 if no completed transactions
    total_sales = total_sales_result['total'] or 0
    
    # Calculate total transactions count
    total_transactions = Transaction.objects.count()
    completed_transactions = Transaction.objects.filter(Status='completed').count()
    
    # Get today's sales
    from datetime import date
    today = date.today()
    today_sales_result = Transaction.objects.filter(
        Status='completed',
        CreatedAt__date=today
    ).aggregate(total=Sum('TotalAmount'))
    
    today_sales = today_sales_result['total'] or 0
    
    if request.method == 'POST':
        form_type = request.POST.get('form_type', '')
        
        if form_type == 'personal_info':
            return handle_personal_info(request, user)
        elif form_type == 'change_password':
            return handle_password_change(request, user)
    
    context = {
        'user': user,
        'total_sellers': total_sellers,
        'active_sellers': active_sellers,
        'pending_sellers': pending_sellers,
        'rejected_sellers': rejected_sellers,
        'total_products': total_products,
        'total_sales': total_sales,
        'total_transactions': total_transactions,
        'completed_transactions': completed_transactions,
        'today_sales': today_sales,
    }
    
    return render(request, 'superadmin/admin-profile.html', context)


# Helper functions (similar to seller but without store info)
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
            return redirect('admin_profile')
        
        # Email validation
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            messages.error(request, "Please enter a valid email address")
            return redirect('admin_profile')
        
        # Phone validation
        if not re.match(r'^\+?[0-9\s\-\(\)]{7,15}$', phone):
            messages.error(request, "Please enter a valid phone number")
            return redirect('admin_profile')
        
        # Check email uniqueness
        if Users.objects.filter(Email=email).exclude(UserID=user.UserID).exists():
            messages.error(request, "Email is already registered with another account")
            return redirect('admin_profile')
        
        # Update user
        user.FullName = full_name
        user.Email = email
        user.Phone = phone
        user.Address = address
        user.save()
        
        messages.success(request, "Personal information updated successfully!")
        
    except Exception as e:
        messages.error(request, f"Error updating personal information: {str(e)}")
    
    return redirect('admin_profile')

def handle_password_change(request, user):
    """Handle password change"""
    try:
        current_password = request.POST.get('current_password', '').strip()
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        
        # Validation
        if not all([current_password, new_password, confirm_password]):
            messages.error(request, "All password fields are required")
            return redirect('admin_profile')
        
        # Check current password
        if not check_password(current_password, user.Password):
            messages.error(request, "Current password is incorrect")
            return redirect('admin_profile')
        
        # Check password length
        if len(new_password) < 6:
            messages.error(request, "New password must be at least 6 characters long")
            return redirect('admin_profile')
        
        # Check password match
        if new_password != confirm_password:
            messages.error(request, "New password and confirmation do not match")
            return redirect('admin_profile')
        
        # Check if new password is different
        if check_password(new_password, user.Password):
            messages.error(request, "New password must be different from current password")
            return redirect('admin_profile')
        
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
        return redirect('admin_profile')

@login_required
@admin_required
def users(request):
    # Get search query and filters
    search_query = request.GET.get('q', '')
    role_filter = request.GET.get('role', '')
    
    # Start with all users
    users_list = Users.objects.all().order_by('-UserID')
    
    # Apply search filter if provided
    if search_query:
        users_list = users_list.filter(
            Q(UserName__icontains=search_query) |
            Q(Email__icontains=search_query) |
            Q(Phone__icontains=search_query)
        )
    
    # Apply role filter if provided
    if role_filter:
        users_list = users_list.filter(Role=role_filter)
    
    # Setup pagination - 10 users per page
    paginator = Paginator(users_list, 10)
    page_number = request.GET.get('page', 1)
    
    try:
        users = paginator.page(page_number)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)
    
    # Calculate range for "Showing X to Y of Z"
    start_index = (users.number - 1) * paginator.per_page + 1
    end_index = min(start_index + paginator.per_page - 1, paginator.count)
    
    context = {
        'users': users,
        'search_query': search_query,
        'role_filter': role_filter,
        'start_index': start_index,
        'end_index': end_index,
        'total_count': paginator.count,
    }
    
    return render(request, 'superadmin/Users.html', context)

@login_required
@admin_required
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

@login_required
@admin_required
def delete_user(request, user_id):
    if request.method == "POST":
        user = get_object_or_404(Users, UserID=user_id)
        user.delete()
        messages.success(request, "User deleted successfully.")
    return redirect('userslist-index')


#Vendors/Sellers
@login_required
@admin_required
def vendorsrequest(request):
    # Get search query and status filter from GET parameters
    search_query = request.GET.get('q', '')
    status_filter = request.GET.get('stat', '')
    
    # Start with all sellers
    sellers_list = Seller.objects.select_related('UserId').all().order_by('-SellerID')
    
    # Apply search filter
    if search_query:
        sellers_list = sellers_list.filter(
            Q(UserId__UserName__icontains=search_query) |
            Q(UserId__Email__icontains=search_query) |
            Q(StoreName__icontains=search_query) |
            Q(StoreAddress__icontains=search_query) |
            Q(ProductionLicenseNumber__icontains=search_query) |
            Q(PAN__icontains=search_query)
        )
    
    # Apply status filter
    if status_filter:
        sellers_list = sellers_list.filter(Status=status_filter)
    
    # Pagination - 5 sellers per page
    paginator = Paginator(sellers_list, 5)
    page = request.GET.get('page', 1)
    
    try:
        sellers = paginator.page(page)
    except PageNotAnInteger:
        sellers = paginator.page(1)
    except EmptyPage:
        sellers = paginator.page(paginator.num_pages)
    
    # Calculate display range
    start_index = (sellers.number - 1) * paginator.per_page + 1
    end_index = min(start_index + paginator.per_page - 1, paginator.count)
    
    context = {
        'sellers': sellers,
        'search_query': search_query,
        'status_filter': status_filter,
        'start_index': start_index,
        'end_index': end_index,
        'total_count': paginator.count,
        'status_choices': Seller.STATUS_CHOICES,
    }
    
    return render(request, "superadmin/vendorrequest.html", context)

@login_required
@admin_required
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

@login_required
@admin_required
def seller_reject(request, seller_id):
    if request.method == "POST":
        seller = get_object_or_404(Seller, SellerID=seller_id)
        seller.Status = "rejected"
        seller.save()
       
        Users = seller.UserId
        Users.Role = "basic"
        Users.save()
        
        messages.error(request, f"Seller request for '{seller.StoreName}' rejected.")
    return redirect("vendorrequest")

#logout
@login_required
@admin_required
def logout_user(request):
    request.session.flush()  # clear session
    messages.success(request, "You have been logged out successfully.")
    return redirect('SignIn-index') 



@login_required
@admin_required
def feedback_list(request):
    search_query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("stat", "").strip()

    qs = Feedback.objects.select_related("submitted_by").order_by("-created_at")

    if search_query:
        qs = qs.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(title__icontains=search_query) |
            Q(message__icontains=search_query)
        )

    if status_filter:
        qs = qs.filter(status=status_filter)

    paginator = Paginator(qs, 20)
    page_number = request.GET.get("page", 1)
    feedbacks = paginator.get_page(page_number)

    start_index = feedbacks.start_index()
    end_index = feedbacks.end_index()
    total_count = paginator.count

    return render(request, "superadmin/feedback.html", {
        "feedbacks": feedbacks,
        "search_query": search_query,
        "status_filter": status_filter,
        "start_index": start_index,
        "end_index": end_index,
        "total_count": total_count,
    })


@login_required
@admin_required
@require_POST
def feedback_resolve(request, pk):
    fb = get_object_or_404(Feedback, pk=pk)
    fb.status = "resolved"
    fb.save()
    messages.success(request, f"Feedback from {fb.first_name} marked as resolved.")
    return redirect("Feedback")


@login_required
@admin_required
@require_POST
def feedback_close(request, pk):
    fb = get_object_or_404(Feedback, pk=pk)
    fb.status = "closed"
    fb.save()
    messages.info(request, f"Feedback from {fb.first_name} closed.")
    return redirect("Feedback")