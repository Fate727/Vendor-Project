# decorators.py
from django.shortcuts import redirect
from django.utils import timezone
from UserModule.models import Users
from functools import wraps

def login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'uid' not in request.session:
            return redirect('/')
        
        try:
            user = Users.objects.get(UserID=request.session['uid'])
            
            # Update login time
            user.LoginAt = timezone.now()
            user.save(update_fields=['LoginAt'])
            
            # Verify session consistency
            if (user.UserName != request.session.get('uname') or 
                user.Role != request.session.get('role')):
                request.session.flush()
                return redirect('/')
            
            # Add user to request object
            request.user_obj = user
            
            return view_func(request, *args, **kwargs)
            
        except Users.DoesNotExist:
            request.session.flush()
            return redirect('/')
        except Exception as e:
            print(f"Error in login_required decorator: {e}")
            return redirect('/')
    
    return wrapper


def seller_required(view_func):
    """
    For seller-only views - also ensures they stay in seller area
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'uid' not in request.session:
            return redirect('/')
        
        try:
            user = Users.objects.get(UserID=request.session['uid'])
            
            if user.Role != 'seller':
                return redirect('/')
            
            request.user_obj = user
            
            # Extra: If seller tries to access non-seller URL, redirect
            if not request.path.startswith('/seller/'):
                return redirect('seller-dashboard')
            
            return view_func(request, *args, **kwargs)
            
        except Users.DoesNotExist:
            request.session.flush()
            return redirect('/')
    
    return wrapper


def admin_required(view_func):
    """
    For admin-only views - also ensures they stay in admin area
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'uid' not in request.session:
            return redirect('/')
        
        try:
            user = Users.objects.get(UserID=request.session['uid'])
            
            if user.Role != 'admin':
                return redirect('/')
            
            request.user_obj = user
            
            # Extra: If admin tries to access non-admin URL, redirect
            if not request.path.startswith('/superadmin/'):
                return redirect('superadmin_dashboard')
            
            return view_func(request, *args, **kwargs)
            
        except Users.DoesNotExist:
            request.session.flush()
            return redirect('/')
    
    return wrapper


def role_based_redirect(view_func):
    """
    For homepage - redirects logged-in users to their dashboard
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'uid' in request.session:
            try:
                user = Users.objects.get(UserID=request.session['uid'])
                
                if user.Role == 'admin':
                    return redirect('superadmin_dashboard')
                elif user.Role == 'seller':
                    return redirect('seller-dashboard')
                # Basic users stay on homepage
                
            except Users.DoesNotExist:
                request.session.flush()
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def public_required(view_func):
    """
    For public pages - redirects logged-in users away
    (like login/signup pages when already logged in)
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'uid' in request.session:
            try:
                user = Users.objects.get(UserID=request.session['uid'])
                
                if user.Role == 'admin':
                    return redirect('superadmin_dashboard')
                elif user.Role == 'seller':
                    return redirect('seller-dashboard')
                # Basic users can stay
                
            except Users.DoesNotExist:
                request.session.flush()
        
        return view_func(request, *args, **kwargs)
    
    return wrapper