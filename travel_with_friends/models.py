# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
'''
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

users = User.objects.all()
for user in users:
    token, created = Token.objects.get_or_create(user=user)
    print user.username, token.key

spatial db:
brew install gdal --HEAD
brew tap osgeo/osgeo4mac
brew install gdal2
brew install --upgrade gdal
CREATE EXTENSION postgis;
CREATE EXTENSION pg_trgm;
ALTER TABLE poi_detail_table_v2 ADD COLUMN geom geometry(POINT,4326);
UPDATE poi_detail_table_v2 SET geom = ST_SetSRID(ST_MakePoint(coord_long,coord_lat),4326);
CREATE INDEX idx_poi_geom ON poi_detail_table_v2 USING GIST(geom);

SELECT name, city, state
FROM poi_detail_table_v2
WHERE ST_Distance_Sphere(geom, ST_MakePoint(-122.6659597,45.5083437)) <= 100 * 1609.34


Create new table for city_coords with state_abb
create table city_state_coords_table as select a.*, b.state_abb 
    from all_cities_coords_table as a left join 
    (select distinct state, state_abb from county_table order by state_abb) as b 
    on a.state = b.state order by a.index;
update city_state_coords_table set state_abb = 'DC' where state_abb is null;
delete from county_table where city = 'San Francisco' and county = 'SAN MATEO';
DELETE 1;
'''

from __future__ import unicode_literals

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from django.conf import settings

# This code is triggered whenever a new user has been created and saved to the database
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)

class AllCitiesCoordsTable(models.Model):
    index = models.BigIntegerField(primary_key=True)
    city = models.TextField(blank=True, null=True)
    state = models.TextField(blank=True, null=True)
    nation = models.TextField(blank=True, null=True)
    coord_lat = models.FloatField(blank=True, null=True)
    coord_long = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'all_cities_coords_table'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=80)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.CharField(unique=True, max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class CountyTable(models.Model):
    index = models.BigIntegerField(primary_key=True)
    city = models.TextField(blank=True, null=True)
    state_abb = models.TextField(blank=True, null=True)
    state = models.TextField(blank=True, null=True)
    county = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'county_table'


class DayTripTable(models.Model):
    index = models.BigIntegerField(primary_key=True)
    trip_locations_id = models.TextField(blank=True, null=True)
    full_day = models.NullBooleanField()
    regular = models.NullBooleanField()
    county = models.TextField(blank=True, null=True)
    state = models.TextField(blank=True, null=True)
    details = models.TextField(blank=True, null=True)
    event_type = models.TextField(blank=True, null=True)
    event_ids = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'day_trip_table'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class FullTripTable(models.Model):
    index = models.BigIntegerField(primary_key=True)
    username = models.ForeignKey('auth.User', related_name = 'full_trips', on_delete=models.CASCADE, default = 1)
    full_trip_id = models.TextField(blank=True, null=True)
    trip_location_ids = models.TextField(blank=True, null=True)
    regular = models.NullBooleanField()
    county = models.TextField(blank=True, null=True)
    state = models.TextField(blank=True, null=True)
    details = models.TextField(blank=True, null=True)
    n_days = models.FloatField(blank=True, null=True)
    visible = models.BooleanField(default=False, blank=True)
    day_created = models.DateTimeField(blank=True, null=True)
    day_modified = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'full_trip_table'


class GoogleTravelTimeTable(models.Model):
    index = models.BigIntegerField(primary_key=True)
    id_field = models.TextField(blank=True, null=True)  # Field renamed because it ended with '_'.
    orig_name = models.TextField(blank=True, null=True)
    orig_idx = models.FloatField(blank=True, null=True)
    dest_name = models.TextField(blank=True, null=True)
    dest_idx = models.FloatField(blank=True, null=True)
    orig_coord_lat = models.FloatField(blank=True, null=True)
    orig_coord_long = models.FloatField(blank=True, null=True)
    dest_coord_lat = models.FloatField(blank=True, null=True)
    dest_coord_long = models.FloatField(blank=True, null=True)
    orig_coords = models.TextField(blank=True, null=True)
    dest_coords = models.TextField(blank=True, null=True)
    google_driving_url = models.TextField(blank=True, null=True)
    google_walking_url = models.TextField(blank=True, null=True)
    driving_result = models.TextField(blank=True, null=True)
    walking_result = models.TextField(blank=True, null=True)
    google_driving_time = models.FloatField(blank=True, null=True)
    google_walking_time = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'google_travel_time_table'

class PoiDetailTableV2(models.Model):
    index = models.BigIntegerField(primary_key=True)
    name = models.TextField(blank=True, null=True)
    street_address = models.TextField(blank=True, null=True)
    city = models.TextField(blank=True, null=True)
    state_abb = models.TextField(blank=True, null=True)
    state = models.TextField(blank=True, null=True)
    postal_code = models.TextField(blank=True, null=True)
    country = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    coord_lat = models.FloatField(blank=True, null=True)
    coord_long = models.FloatField(blank=True, null=True)
    num_reviews = models.BigIntegerField(blank=True, null=True)
    review_score = models.FloatField(blank=True, null=True)
    ranking = models.BigIntegerField(blank=True, null=True)
    tag = models.TextField(blank=True, null=True)
    raw_visit_length = models.TextField(blank=True, null=True)
    fee = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    url = models.TextField(blank=True, null=True)
    geo_content = models.TextField(blank=True, null=True)
    poi_type = models.TextField(blank=True, null=True)
    adjusted_visit_length = models.BigIntegerField(blank=True, null=True)
    county = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'poi_detail_table'

class OutsideRouteTable(models.Model):
    index = models.BigIntegerField(primary_key=True)
    outside_route_id = models.TextField(blank=True, null=True)
    full_day = models.NullBooleanField()
    regular = models.NullBooleanField()
    origin_city = models.TextField(blank=True, null=True)
    origin_state = models.TextField(blank=True, null=True)
    target_direction = models.TextField(blank=True, null=True)
    details = models.TextField(blank=True, null=True)
    event_type = models.TextField(blank=True, null=True)
    event_ids = models.TextField(blank=True, null=True)
    route_num = models.IntegerField(blank=True, null=True)
    route_theme =  models.TextField(blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'outside_route_table'


class OutsideTripTable(models.Model):
    index = models.BigIntegerField(primary_key=True)
    username = models.ForeignKey('auth.User', related_name = 'outside_trips', on_delete=models.CASCADE, default=1)
    outside_trip_id = models.TextField(blank=True, null=True)
    outside_route_ids = models.TextField(blank=True, null=True)
    event_id_lst = models.TextField(blank=True, null=True)
    origin_city = models.TextField(blank=True, null=True)
    origin_state = models.TextField(blank=True, null=True)
    target_direction = models.TextField(blank=True, null=True)
    n_routes = models.FloatField(blank=True, null=True)
    regular = models.NullBooleanField()
    full_day = models.NullBooleanField()
    outside_trip_details = models.TextField(blank=True, null=True)
    day_created = models.DateTimeField(blank=True, null=True)
    day_modified = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'outside_trip_table'
