"""community_meetings URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
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
from django.urls import path, include
from django.conf import settings
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from meeting_platform.utils.customized.my_view import PingView

urlpatterns = [
    path('ping/', PingView.as_view()),
    path('/api/v1/meeting/', include('meeting.urls.web')),
    path('/inner/v1/meeting/', include('meeting.urls.inner')),

]

if settings.DEBUG:
    schema_view = get_schema_view(
        openapi.Info(
            title='Meeting-Platform API',
            default_version='V1',
            description='Meeting-Platform 接口文档',
            license=openapi.License(name='Apache 2.0 License'),
        ),
        public=True,
        permission_classes=[permissions.AllowAny, ]
    )

    urlpatterns.extend([
        path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    ])
