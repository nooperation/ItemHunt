from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^activate_item$', views.ActivateItemView.as_view(), name='activate_item'),
    url(r'^register_item$', views.RegisterItemView.as_view(), name='register_item'),
    url(r'^get_total_points$', views.GetTotalPointsView.as_view(), name='get_total_points'),
    url(r'^purge_expired_tokens$', views.PurgeExpiredTokensView.as_view(), name='purge_expired_tokens'),
]
