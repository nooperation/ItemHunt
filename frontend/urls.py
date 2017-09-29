from django.conf.urls import url
from . import views

app_name = 'frontend'

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^register_token', views.RegisterTokenView.as_view(), name='register_token'),
]
