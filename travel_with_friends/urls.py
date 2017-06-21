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
    url(r'^full_trip_search/$', views.FullTripSearch.as_view(), name='full-trip-detail'),
    url(r'^outside_trip_search/$', views.OutsideTripSearch.as_view(), name='outside-trip-detail'),
    url(r'^city_state_search/$', views.CityStateSearch.as_view(), name='city-state-detail'), 
    url(r'^update_trip/delete/$', views.FullTripDeleteEvent.as_view(), name='full-trip-delete'), 
    url(r'^update_trip/suggest_search/$', views.FullTripSuggestArray.as_view(), name='full-trip-suggest-search'), 
    url(r'^update_trip/suggest_confirm/$', views.FullTripSuggestConfirm.as_view(), name='full-trip-suggest-confirm'), 
    url(r'^update_trip/add_search/$', views.FullTripAddSearch.as_view(), name='full-trip-add-search'), 
    url(r'^update_trip/add/$', views.FullTripAddEvent.as_view(), name='full-trip-add-event'), 
    url(r'^create_full_trip/$', views.FullTripCreate.as_view(), name='full-trip-create'), 

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