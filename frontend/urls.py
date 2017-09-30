from django.conf.urls import url
from . import views

app_name = 'frontend'

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^register_token/(?P<token>[a-zA-Z0-9-_=]+)', views.RegisterTokenView.as_view(), name='register_token'),
]
