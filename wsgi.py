from django.contrib import admin
from django.urls import path, include
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# ensure_csrf_cookie forces Django to set the csrftoken cookie
# whenever Swagger UI is opened — this is the requirement
schema_view = get_schema_view(
    openapi.Info(
        title="Authentication API",
        default_version='v1',
        description="Cookie-based authentication system with OTP email verification",
        contact=openapi.Contact(email="admin@authapp.com"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

# Wrap swagger view with ensure_csrf_cookie so the
# csrftoken cookie is automatically set when /swagger/ is visited
swagger_view = ensure_csrf_cookie(schema_view.with_ui('swagger', cache_timeout=0))
redoc_view  = ensure_csrf_cookie(schema_view.with_ui('redoc',   cache_timeout=0))

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('authentication.urls')),
    # Swagger UI — visiting this page auto-sets CSRF cookie
    path('swagger/', swagger_view, name='schema-swagger-ui'),
    path('redoc/',   redoc_view,   name='schema-redoc'),
]

# Serve frontend demo
from django.views.generic import TemplateView
from django.views.decorators.csrf import ensure_csrf_cookie
urlpatterns += [
    path('', ensure_csrf_cookie(TemplateView.as_view(template_name='index.html')), name='home'),
]
