# sha/urls.py - SHA app urls
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Authentication
    path('', auth_views.LoginView.as_view(template_name='admin/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
    # Dashboard
    path('admin-dashbaord/', views.admin_dashboard, name='admin_dashboard'),
    
    
    # Add more URLs as you build more views
    # path('members/', views.member_list, name='member_list'),
    # path('members/<uuid:pk>/', views.member_detail, name='member_detail'),
    # path('claims/', views.claim_list, name='claim_list'),
    # etc.
]