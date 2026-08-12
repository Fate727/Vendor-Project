from django.urls import path
from . import views

urlpatterns = [
    path('', views.superadmin_dashboard, name='superadmin-dashboard'),
    path('admin-profile/',views.admin_profile ,name="admin_profile"),
    
    #User list and Management.
    path('users/', views.users, name='userslist-index'),  
    path('addusers/', views.addusers, name='addusers-index'), 
    path("<int:user_id>/edit/", views.edit_user, name="edit_user"),
    path("<int:user_id>/delete/", views.delete_user, name="delete_user"),
    
    # Seller/vendor management.    
    path('vendors', views.vendorsrequest, name='vendorrequest'),
    path('vendorrequests/accept/<int:seller_id>/', views.seller_accept, name='seller_accept'),
    path('vendorrequests/reject/<int:seller_id>/', views.seller_reject, name='seller_reject'),

    # Transcations
    

    #Feedback
    path('Feedback/', views.feedback_list, name='Feedback'),
    path('Feedback/<int:pk>/resolve/', views.feedback_resolve, name='feedback_resolve'),
    path('Feedback/<int:pk>/close/', views.feedback_close, name='feedback_close'),  

    path('logout', views.logout_user, name='logout'),
]
