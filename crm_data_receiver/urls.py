"""
URL configuration for crm_data_receiver project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from receiver.views import receiver_list

urlpatterns = [
   path('admin/', admin.site.urls),
    path('api/', include('receiver.urls')),
    path('inquiries/', receiver_list, name='receiver_list'),
    
    
    path('', include('stockmanagement.urls')),  
    
    # this api is testing for pratice level in 
    path('api/', include('reports.urls')),
    
    
]
