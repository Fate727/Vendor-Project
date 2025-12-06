from django.urls import path
from . import views

urlpatterns = [
    
    # UI sections
    path('', views.index, name='user-index'),
    path('shop', views.Shop, name='Shop-index'),
    path('store', views.Store, name='Store-index'),
    path('About', views.About, name='About-index'),
    path('Order', views.Order, name='Order-index'),
    path('Address', views.Address, name='Address'),
    path('Contact', views.Contact, name="Contact-index"),
 
    # Login section
    path('account-setting', views.AccountSetting, name='AccountSetting'),
    path('SignIn', views.SignIn, name='SignIn-index'),
    path('SignUp', views.SignUp, name='SignUp-index'),
    path('Forgot', views.Forgot, name='Forgot-index'),
    path('AccountLogout', views.logout_accout, name="LogoutAccount"),
    path('requestseller', views.request_seller, name="requestseller"),

    # Prodcut module section 
    path('product/quick-view/<int:product_id>/', views.product_quick_view, name='product_quick_view'),
    
    # Cart Sections
    path('Cart', views.Carts, name="Cart"),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path("update-cart-quantity/", views.update_quantity, name="update-cart-quantity"),
    path("remove-cart-item/", views.remove_cart_item, name="remove-cart-item"),

    # Check Out sections
    path('checkout/', views.checkout, name='checkout'),
]
