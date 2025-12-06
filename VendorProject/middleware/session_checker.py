from django.shortcuts import redirect
from django.utils import timezone
from UserModule.models import Users  

class SessionCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.user_obj = None
        request.role = None
        
        # Public paths that anyone can access
        PUBLIC_PATHS = [
            '/', '/SignIn', '/SignUp', '/About', '/shop', '/store', 
            '/Contact', '/Address', '/static/', '/media/'
        ]

        # Allow public paths
        if any(request.path.startswith(p) for p in PUBLIC_PATHS):
            return self.get_response(request)

        user_id = request.session.get('uid')
        user = None
        role = None

        if user_id:
            try:
                user = Users.objects.get(UserID=user_id)
                role = user.Role
                request.role = role
                request.user_obj = user
            except Users.DoesNotExist:
                request.session.flush()
                return redirect('/')  # Redirect to home instead of SignIn

        if not user or not role:
            # Not logged in - redirect to home page
            return redirect('/')  # Changed from '/SignIn'

        # Update LastLogin in DB
        user.LastLogin = timezone.now()
        user.save()

        # Role-based access
        role_lower = role.lower()
        path = request.path.lower()

        if role_lower == 'admin':
            if not path.startswith('/superadmin'):
                return redirect('/superadmin/')
        elif role_lower == 'seller':
            if not path.startswith('/seller'):
                return redirect('/seller/')  # Note: lowercase to match URL
        elif role_lower in ['basic', 'user']:
            if path.startswith('/superadmin') or path.startswith('/seller'):
                return redirect('/')

        return self.get_response(request)