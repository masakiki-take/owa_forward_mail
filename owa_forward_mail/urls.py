from django.conf.urls import url
from django.contrib import admin

from . import views
from .accounts import views as accounts_views
from .dashboard import views as dashboard_views


urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^login/$', accounts_views.LoginView.as_view(), name='login'),
    url(r'^logout/$', accounts_views.LogoutView.as_view(), name='logout'),
    url(r'^dashboard/$', dashboard_views.DashboardView.as_view(), name='dashboard'),
    url(r'^account/$', accounts_views.AccountView.as_view(), name='account'),
    url(r'^edit_email/$', accounts_views.EditEmailView.as_view(), name='edit_email'),
    url(r'^email/confirm/(?P<token>[^/]+)/$', accounts_views.EmailConfirmationView.as_view(), name='confirm_email'),
    url(r'^dashboard/edit_forward_type/$', dashboard_views.EditForwardTypeView.as_view(), name='edit_forward_type'),
    url(r'^dashboard/resend/$', dashboard_views.ResendEmailView.as_view(), name='resend'),
    url(r'^admin/', admin.site.urls),
]
