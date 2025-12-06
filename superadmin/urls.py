from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='superadmin_dashboard'),
    path('users',views.users, name='userslist-index'),
    path('addusers', views.addusers, name='addusers-index'),
    path("<int:user_id>/edit/", views.edit_user, name="edit_user"),
    path("<int:user_id>/delete/", views.delete_item, name="delete_item"),
    path('logout', views.logout_user, name='logout'),
    path('vendors', views.vendorsrequest, name='vendorrequest'),
     path('vendorrequests/accept/<int:seller_id>/', views.seller_accept, name='seller_accept'),
    path('vendorrequests/reject/<int:seller_id>/', views.seller_reject, name='seller_reject'),
]
