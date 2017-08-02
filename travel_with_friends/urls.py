from django.conf.urls import url, include
from travel_with_friends import views
from rest_framework.routers import DefaultRouter

from django.conf import settings
from django.conf.urls.static import static
# from . import views as local_views
from rest_framework.authtoken import views as rest_framework_views
# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'users', views.UserViewSet)
# router.register(r'accounts', views.UserView, 'list')

# The API URLs are now determined automatically by the router.
# Additionally, we include the login URLs for the browsable API.
urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'full_trip/(?P<full_trip_id>[^\.]+)/$', views.FullTripDetail.as_view(), name='full_trip_detail'),
    url(r'outside_trip/(?P<outside_trip_id>[^\.]+)/$', views.OutsideTripDetail.as_view(), name='outside_trip_detail'),
    url(r'^full_trip_search/$', views.FullTripSearch.as_view(), name='full_trip_detail'),
    url(r'^outside_trip_search/$', views.OutsideTripSearch.as_view(), name='outside_trip_detail'),
    url(r'^city_state_search/$', views.CityStateSearch.as_view(), name='city_state_detail'), 
    url(r'^update_trip/delete/$', views.FullTripDeleteEvent.as_view(), name='full_trip_delete'), 
    url(r'^update_trip/suggest_search/$', views.FullTripSuggestArray.as_view(), name='full_trip_suggest_search'), 
    url(r'^update_trip/suggest_confirm/$', views.FullTripSuggestConfirm.as_view(), name='full_trip_suggest_confirm'), 
    url(r'^update_trip/add_search/$', views.FullTripAddSearch.as_view(), name='full_trip_add_search'), 
    url(r'^update_trip/add/$', views.FullTripAddEvent.as_view(), name='full_trip_add_event'), 
    url(r'^create_full_trip/$', views.FullTripCreate.as_view(), name='full_trip_create'), 
    url(r'^update_outside_trip/add_search/$', views.OutsideTripAddSearch.as_view(), name='Outside_Trip_Add_Search'), 
    

    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    # url(r'^login/$', local_views.get_auth_token, name='login'),
    # url(r'^logout/$', local_views.logout_user, name='logout'),
    # url(r'^auth/$', local_views.login_form, name='login_form'),
    url(r'^account/get_auth_token/$', rest_framework_views.obtain_auth_token, name='get_auth_token'),
    url(r'^account/register', views.create_auth, name='register_user'),

    url(r'^iplocation/$', views.IPGeoLocation.as_view()),

    # url(r'^api/', include(router.urls)),
    # url(r'^users/create_user', views.CreateUserView),
]