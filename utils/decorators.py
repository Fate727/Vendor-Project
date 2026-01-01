# decorators.py
from django.shortcuts import redirect
from django.utils import timezone
from django.http import HttpResponseForbidden
from UserModule.models import Users
from SellerModule.models import Seller
from functools import wraps

def login_required(view_func):
    """
    Simple login_required decorator that checks session uid
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Debug: Print current path and session
        print(f"[LOGIN_REQUIRED] Checking access to: {request.path}")
        print(f"[LOGIN_REQUIRED] Session uid: {request.session.get('uid')}")
        
        if 'uid' not in request.session:
            print(f"[LOGIN_REQUIRED] No uid in session, redirecting to login")
            return redirect('user-index')  # Redirect to your login page
        
        try:
            user = Users.objects.get(UserID=request.session['uid'])
            print(f"[LOGIN_REQUIRED] User found: {user.UserName}, Role: {user.Role}")
            
            # Update login time
            user.LoginAt = timezone.now()
            user.save(update_fields=['LoginAt'])
            
            # Verify session consistency
            if (user.UserName != request.session.get('uname') or 
                user.Role != request.session.get('role')):
                print(f"[LOGIN_REQUIRED] Session inconsistency, flushing session")
                request.session.flush()
                return redirect('user-index')
            
            # Add user to request object
            request.user_obj = user
            
            print(f"[LOGIN_REQUIRED] Access granted to {user.UserName}")
            return view_func(request, *args, **kwargs)
            
        except Users.DoesNotExist:
            print(f"[LOGIN_REQUIRED] User {request.session.get('uid')} not found in DB")
            request.session.flush()
            return redirect('user-index')
        except Exception as e:
            print(f"[LOGIN_REQUIRED] Error: {e}")
            request.session.flush()
            return redirect('user-index')
    
    return wrapper


def seller_required(view_func):
    """
    For seller-only views
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        print(f"[SELLER_REQUIRED] Checking access to: {request.path}")
        print(f"[SELLER_REQUIRED] Session uid: {request.session.get('uid')}")
        
        if 'uid' not in request.session:
            print(f"[SELLER_REQUIRED] No uid in session, redirecting to login")
            return redirect('user-index')
        
        try:
            user = Users.objects.get(UserID=request.session['uid'])
            print(f"[SELLER_REQUIRED] User found: {user.UserName}, Role: {user.Role}")
            
            # Check if user has seller role
            if user.Role != 'seller':
                print(f"[SELLER_REQUIRED] User is not seller, role: {user.Role}")
                return HttpResponseForbidden("Access Denied: Seller Only")
            
            # Check if user has an accepted seller application
            try:
                seller = Seller.objects.get(UserId=user)
                print(f"[SELLER_REQUIRED] Seller found: {seller.StoreName}, Status: {seller.Status}")
                
                if seller.Status != 'accepted':
                    if seller.Status == 'pending':
                        return redirect('requestseller')
                    elif seller.Status == 'rejected':
                        return redirect('requestseller')
                    else:
                        return HttpResponseForbidden("Seller application not approved")
                
                # Attach both user and seller objects to request
                request.user_obj = user
                request.seller_obj = seller
                
            except Seller.DoesNotExist:
                print(f"[SELLER_REQUIRED] No seller application found for user")
                return redirect('requestseller')
            
            print(f"[SELLER_REQUIRED] Seller access granted to {seller.StoreName}")
            return view_func(request, *args, **kwargs)
            
        except Users.DoesNotExist:
            print(f"[SELLER_REQUIRED] User not found in DB")
            request.session.flush()
            return redirect('user-index')
        except Exception as e:
            print(f"[SELLER_REQUIRED] Error: {e}")
            return HttpResponseForbidden("Error accessing seller resources")
    
    return wrapper


def admin_required(view_func):
    """
    Fixed admin_required decorator - no tuple index errors
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        print(f"[ADMIN_REQUIRED] Checking access to: {request.path}")
        print(f"[ADMIN_REQUIRED] Session uid: {request.session.get('uid')}")
        
        if 'uid' not in request.session:
            print(f"[ADMIN_REQUIRED] No uid in session, redirecting to login")
            return redirect('user-index')
        
        try:
            user = Users.objects.get(UserID=request.session['uid'])
            print(f"[ADMIN_REQUIRED] User found: {user.UserName}, Role: {user.Role}")
            
            if user.Role != 'admin':
                print(f"[ADMIN_REQUIRED] User is not admin, role: {user.Role}")
                return HttpResponseForbidden("Access Denied: Admin Only")
            
            # Attach user to request
            request.user_obj = user
            print(f"[ADMIN_REQUIRED] Admin access granted to {user.UserName}")
            
            # CORRECT: Pass all arguments to the view function
            return view_func(request, *args, **kwargs)
            
        except Users.DoesNotExist:
            print(f"[ADMIN_REQUIRED] User not found in DB")
            request.session.flush()
            return redirect('user-index')
        except Exception as e:
            print(f"[ADMIN_REQUIRED] Error: {str(e)}")
            print(f"[ADMIN_REQUIRED] Error type: {type(e)}")
            import traceback
            print(f"[ADMIN_REQUIRED] Traceback: {traceback.format_exc()}")
            return HttpResponseForbidden(f"Error: {str(e)}")
    
    return wrapper


def role_based_redirect(view_func):
    """
    For homepage - redirects logged-in users to their dashboard
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        print(f"[ROLE_REDIRECT] Checking role for homepage")
        
        if 'uid' in request.session:
            try:
                user = Users.objects.get(UserID=request.session['uid'])
                print(f"[ROLE_REDIRECT] User logged in: {user.UserName}, Role: {user.Role}")
                
                if user.Role == 'admin':
                    return redirect('superadmin-dashboard')
                elif user.Role == 'seller':
                    return redirect('seller-dashboard')
                # Basic users stay on homepage
                
            except Users.DoesNotExist:
                request.session.flush()
        
        print(f"[ROLE_REDIRECT] Showing public homepage")
        return view_func(request, *args, **kwargs)
    
    return wrapper


def public_required(view_func):
    """
    For public pages (login/signup) - redirects logged-in users away
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        print(f"[PUBLIC_REQUIRED] Checking if user should see public page")
        
        if 'uid' in request.session:
            try:
                user = Users.objects.get(UserID=request.session['uid'])
                print(f"[PUBLIC_REQUIRED] User logged in: {user.UserName}, Role: {user.Role}")
                
                if user.Role == 'admin':
                    return redirect('superadmin-dashboard')
                elif user.Role == 'seller':
                    return redirect('seller-dashboard')
                # Basic users can stay on public pages
                
            except Users.DoesNotExist:
                request.session.flush()
        
        return view_func(request, *args, **kwargs)
    
    return wrapper