from django.urls import path
from . import views
from django.conf.urls.static import static


urlpatterns = [
    path('', views.dashboard, name='seller-dashboard'),
    
    # Prodcut sections
    path('products', views.productSection, name='products-index'),
    path('products/ajax/', views.ajax_products, name='ajax_products'),
    path('addproducts', views.AddProduct, name='Addproduct'),
    path('delete-product/<int:product_id>/', views.delete_product, name='delete-product'),
    path('edit-product/<int:product_id>/', views.edit_product, name='edit-product'),
    path('delete-product-image/<int:product_id>/<int:image_index>/', 
         views.DeleteProductImage, 
         name='delete-product-image'),
    
    # Category Section
    path('category', views.categorySection, name='category-index'),
    path('addcategory', views.AddCategory, name='AddCategory'),
    path("categories/ajax/", views.ajax_categories, name="ajax_categories"), 
    path('categories/edit/<int:category_id>/', views.EditCategory, name='edit_category'),
    path('categories/delete/<int:category_id>/', views.DeleteCategory, name='delete_category'),

    # Order Section
    path('Seller-Order', views.Order, name='order-seller'),
    path('order/<int:transaction_id>/update-status/<str:new_status>/', 
         views.update_order_status, 
         name='update-order-status'),
    path('Order-details', views.Orderdetail, name='Order-details'),

    path('SellerLogout', views.logout_accout, name="LogoutSeller"),

]
