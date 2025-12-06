from SellerModule.models import Users

def seller_info(request):
    uid = request.session.get('uid')  # fetch stored user ID
    if uid:
        try:
            user = Users.objects.get(UserID=uid)
            return {
                'seller_name': user.FullName or user.UserName,
                'seller_email': user.Email,
            }
        except Users.DoesNotExist:
            pass
    return {
        'seller_name': 'Guest',
        'seller_email': '',
    }
