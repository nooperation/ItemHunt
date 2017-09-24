from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^activate_item$', views.ActivateItemView.as_view(), name='activate_item'),
    url(r'^get_total_points$', views.GetTotalPointsView.as_view(), name='get_total_points'),
]
