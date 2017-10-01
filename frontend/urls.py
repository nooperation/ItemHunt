from django.conf.urls import url
from . import views

app_name = 'frontend'

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^register_token/(?P<token>[a-zA-Z0-9-_=]+)', views.RegisterTokenView.as_view(), name='register_token'),
    url(r'^hunt/(?P<hunt_id>[0-9]+)$', views.HuntView.as_view(), name='view_hunt'),
    url(r'^hunt/(?P<hunt_id>[0-9]+)/generate_token$', views.GenerateTokenView.as_view(), name='generate_token'),
    url(r'^hunt/(?P<hunt_id>[0-9]+)/item/(?P<item_id>[0-9]+)$', views.ItemView.as_view(), name='view_item'),
    url(r'^hunt/(?P<hunt_id>[0-9]+)/player/(?P<player_id>[0-9]+)$', views.PlayerView.as_view(), name='view_player'),
]
