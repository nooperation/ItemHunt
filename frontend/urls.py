from django.conf.urls import url
from . import views

app_name = 'frontend'

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^register_token/(?P<token>[a-zA-Z0-9-_=]+)', views.RegisterTokenView.as_view(), name='register_token'),
    url(r'^hunt/(?P<hunt_id>[0-9]+)$', views.HuntView.as_view(), name='view_hunt'),
    url(r'^hunt/(?P<hunt_id>[0-9]+)/players$', views.HuntPlayersView.as_view(), name='view_hunt_players'),
    url(r'^hunt/(?P<hunt_id>[0-9]+)/items$', views.HuntItemsView.as_view(), name='view_hunt_items'),
    url(r'^hunt/(?P<hunt_id>[0-9]+)/prizes$', views.HuntPrizesView.as_view(), name='view_hunt_prizes'),
    url(r'^hunt/(?P<hunt_id>[0-9]+)/regions$', views.HuntRegionsView.as_view(), name='view_hunt_regions'),
    url(r'^hunt/(?P<hunt_id>[0-9]+)/region/(?P<region_id>[0-9]+)/items$', views.RegionItemsView.as_view(), name='view_hunt_region_items'),
    url(r'^hunt/(?P<hunt_id>[0-9]+)/region/(?P<region_id>[0-9]+)/prizes$', views.RegionPrizesView.as_view(), name='view_hunt_region_prizes'),
    url(r'^hunt/(?P<hunt_id>[0-9]+)/generate_token$', views.GenerateTokenView.as_view(), name='generate_token'),
    url(r'^hunt/(?P<hunt_id>[0-9]+)/item/(?P<item_id>[0-9]+)$', views.ItemView.as_view(), name='view_item'),
    url(r'^hunt/(?P<hunt_id>[0-9]+)/player/(?P<player_id>[0-9]+)$', views.PlayerView.as_view(), name='view_player'),
]
