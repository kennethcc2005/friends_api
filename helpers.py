import json
import psycopg2
import simplejson
import urllib
import numpy as np
import os
import ast
import re
import distance
from collections import Counter

current_path= os.getcwd()
with open(current_path + '/api_key_list.config') as key_file:
    api_key_list = json.load(key_file)
api_key = api_key_list["distance_api_key_list"]
conn_str = api_key_list["conn_str"]


def check_valid_state(state):
    '''
    Only valid within the U.S.
    '''
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    state = state.replace('_', ' ')
    cur.execute("SELECT DISTINCT state FROM poi_detail_table WHERE state = '%s';" % (state.title()))
    c = cur.fetchone()
    conn.close()
    return bool(c)

def check_valid_city(city, state):
    '''
    Only valid within the U.S.
    '''
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    state = state.replace('_', ' ')
    city = city.replace('_', ' ')
    cur.execute("SELECT DISTINCT city, state FROM poi_detail_table WHERE city = '%s' AND state = '%s';" % (city.title(), state.title()))
    c = cur.fetchone()
    conn.close()
    return bool(c)

def find_county(state, city):
    '''
    Only valid within the U.S.
    '''
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    city = city.replace('_', ' ')
    cur.execute("SELECT DISTINCT county FROM county_table WHERE city = '%s' AND state = '%s';" % (city.title(), state.title()))

    county = cur.fetchone()
    conn.close()
    if county:
        return county[0]
    else:
        return None

def db_start_location(county, state, city):
    '''
    Get numpy array of county related POIs.
    '''
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    if county:
        cur.execute("SELECT index, coord_lat, coord_long, adjusted_visit_length, ranking, review_score, num_reviews FROM poi_detail_table WHERE county = '%s' AND state = '%s' AND NOT poi_type = 'Tour';" % (county.upper(), state.title()))
    else:
        cur.execute("SELECT index, coord_lat, coord_long, adjusted_visit_length, ranking, review_score, num_reviews FROM poi_detail_table WHERE city = '%s' AND state = '%s' AND NOT poi_type = 'Tour';" % (city.title(), state.title()))
    a = cur.fetchall()
    conn.close()
    return np.array(a)

def get_event_ids_list(trip_locations_id):
    '''
    Input: trip_locations_id
    Output: evnet_ids, event_type = ['big', 'small', 'med', 'add',]
    '''
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    cur.execute("SELECT event_ids,event_type FROM day_trip_table WHERE trip_locations_id = '%s';" % (trip_locations_id))
    event_ids, event_type = cur.fetchone()
    print "At helper.get_event_ids_list before convert_event_ids_to_lst", event_ids, type(event_ids)
    event_ids = convert_event_ids_to_lst(event_ids)
    print "At helper.get_event_ids_list after convert_event_ids_to_lst", event_ids, type(event_ids)
    conn.close()
    return event_ids, event_type


def db_event_cloest_distance(trip_locations_id=None, event_ids=None, event_type='add', new_event_id=None, city_name=None):
    '''
    Get matrix cloest distance
    '''
    if new_event_id or not event_ids:
        event_ids, event_type = get_event_ids_list(trip_locations_id)
        if new_event_id:
            event_ids.append(new_event_id)
            
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    points=[]
    # points = np.zeros((len(event_ids), 3))
    for i, v in enumerate(event_ids):
        cur.execute("SELECT index, coord_lat, coord_long, city , ranking FROM poi_detail_table WHERE index = %i;" %(float(v)))
        points.append(cur.fetchone())
    conn.close()

    points = check_NO_1(points, city_name)
    n, D = distance.mk_matrix(points[:,1:3], distance.geopy_dist)
    if len(points) >= 3:
        # if event_type == 'add':
        
        tour = distance.nearest_neighbor(n, 0, D)
        # create a greedy tour, visiting city 'i' first
        z = distance.length(tour, D)
        z = distance.localsearch(tour, z, D)
        return np.array(event_ids)[tour], event_type

        #need to figure out other cases
        # else:
        #     tour = distance.nearest_neighbor(n, 0, D)
        #     # create a greedy tour, visiting city 'i' first
        #     z = distance.length(tour, D)
        #     z = distance.localsearch(tour, z, D)
        #     return np.array(event_ids)[tour], event_type
    else:
        return np.array(event_ids), event_type

def check_NO_1(poi_list, city_name):
    '''
    
    '''
    city_name = city_name.replace('_',' ')
    if len(poi_list)==1:
        return np.array(poi_list)
    for i, poi in enumerate(poi_list):
        if (poi[3] == city_name) and (poi[4] ==1):
            number_one = poi_list.pop(i)
            return np.vstack((np.array(number_one),np.array(poi_list)))
    return np.array(poi_list)


def check_full_trip_id(full_trip_id, debug=True):
    '''
    Check full trip id exist or not.  
    '''
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    cur.execute("SELECT details FROM full_trip_table WHERE full_trip_id = '%s';" %(full_trip_id))
    a = cur.fetchone()
    conn.close()
    if bool(a):
        if not debug:
            return a[0]
        else:
            return True
    else:
        return False

def check_day_trip_id(day_trip_id):
    '''
    Check day trip id exist or not.  
    '''
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor() 
    cur.execute("SELECT details FROM day_trip_table WHERE trip_locations_id = '%s';" % (day_trip_id))
    a = cur.fetchone()
    conn.close()
    if bool(a):
        return True
    else:
        return False

def check_travel_time_id(new_id):
    '''
    Check google driving time exisit or not for the 2 point poi id.
    '''
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    cur.execute("SELECT google_driving_time FROM google_travel_time_table WHERE id_field = '%s';" % (new_id))
    a = cur.fetchone()
    conn.close()
    if bool(a):
        return True
    else:
        return False

#May need to improve by adding #reviews in this. :)
def sorted_events(info,ix):
    '''
    find the event_id, ranking AND review_score, num_reviews columns
    sorted base on ranking then review_score, num_reviews
    
    return sorted list 
    '''
    event_ = info[ix][:, [0, 4, 5, 6]]
    return np.array(sorted(event_, key=lambda x: (x[1], -x[3], -x[2])))

#Need to make this more efficient
def create_event_id_list(big_, medium_, small_):
    event_type = ''
    if big_.shape[0] >= 1:
        if (medium_.shape[0] < 2) or (big_[0, 1] <= medium_[0, 1]):
            if small_.shape[0] >= 6:
                event_ids = list(np.concatenate((big_[:1, 0], small_[0:6, 0]), axis=0))
            elif small_.shape[0] > 0:
                event_ids = list(np.concatenate((big_[:1, 0], small_[:, 0]), axis=0))
            else:
                event_ids = list(np.array(sorted(big_[0:, :], key=lambda x: (x[1], -x[2])))[:, 0])
            event_type = "big"
        else:
            if small_.shape[0] >= 8:
                event_ids = list(np.concatenate((medium_[0:2, 0], small_[0:8, 0]), axis=0))
            elif small_.shape[0] > 0:
                event_ids = list(np.concatenate((medium_[0:2, 0], small_[:, 0]), axis=0))
            else:
                event_ids = list(np.array(sorted(medium_[0:, :], key=lambda x: (x[1], -x[2])))[:, 0])
            event_type = "med"
    elif medium_.shape[0] >= 2:
        if small_.shape[0] >= 8:
            event_ids = list(np.concatenate((medium_[0:2, 0], small_[0:8, 0]), axis=0))
        elif small_.shape[0] > 0:
            event_ids = list(np.concatenate((medium_[0:2, 0], small_[:, 0]), axis=0))
        else:
            event_ids = list(np.array(sorted(medium_[0:, :], key=lambda x: (x[1], -x[2])))[:, 0])
        event_type = "med"
    else:
        if small_.shape[0] >= 10:
            if medium_.shape[0] ==0:
                event_ids = list(np.array(sorted(small_[0:10, :], key=lambda x: (x[1], -x[2])))[:, 0])
            else:
                event_ids = list(np.array(sorted(np.vstack((medium_[:1, :], small_[0:10, :])), key=lambda x: (x[1], -x[2])))[:, 0])
        elif small_.shape[0] > 0:
            if medium_.shape[0]==0:
                event_ids = list(np.array(sorted(small_[0:, :], key=lambda x: (x[1], -x[2])))[:, 0])
            else:
                event_ids = list(np.array(sorted(np.vstack((medium_, small_)), key=lambda x: (x[1], -x[2])))[:, 0])

        else:
            event_ids = list(np.array(sorted(medium_[0:, :], key=lambda x: (x[1], -x[2])))[:, 0])
        event_type = "small"

    return event_ids, event_type

def db_google_driving_walking_time(event_ids, event_type):
    '''
    Get estimated travel time FROM google api.  
    Limit 1000 calls per day.
    '''
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    google_ids = []
    driving_time_list = []
    walking_time_list = []
    name_list = []
    api_i = 0
    for i,v in enumerate(event_ids[:-1]):
        id_ = str(int(v)) + '0000'+str(int(event_ids[i+1]))
        result_check_travel_time_id = check_travel_time_id(id_)
        if not result_check_travel_time_id:
            cur.execute("SELECT name, coord_lat, coord_long FROM poi_detail_table WHERE index = %s;" % (v))
            orig_name, orig_coord_lat, orig_coord_long = cur.fetchone()
            orig_idx = v
            cur.execute("SELECT name, coord_lat, coord_long FROM poi_detail_table WHERE index = %s;" % (event_ids[i + 1]))
            dest_name, dest_coord_lat, dest_coord_long = cur.fetchone()
            dest_idx = event_ids[i + 1]
            orig_coords = str(orig_coord_lat) + ',' + str(orig_coord_long)
            dest_coords = str(dest_coord_lat) + ',' + str(dest_coord_long)

            google_result = find_google_result(orig_coords, dest_coords, orig_name, dest_name, api_i)
            while google_result == False:
                api_i += 1
                if api_i > len(api_key)-1:
                    print "all api_key are used"
                    
                google_result = find_google_result(orig_coords, dest_coords, orig_name, dest_name, api_i)
            driving_result, walking_result, google_driving_url, google_walking_url = google_result

            if (driving_result['rows'][0]['elements'][0]['status'] == 'NOT_FOUND') and (walking_result['rows'][0]['elements'][0]['status'] == 'NOT_FOUND'):
                new_event_ids = list(event_ids)
                new_event_ids.pop(i + 1)
                new_event_ids, event_type = db_event_cloest_distance(event_ids=new_event_ids, event_type=event_type)
                return db_google_driving_walking_time(new_event_ids, event_type)
            try:
                google_driving_time = driving_result['rows'][0]['elements'][0]['duration']['value'] / 60
            except: 
                print "id :", v
                print"id_id: ", id_
                print "result (please check location--most likely cannot drive between location):", driving_result  #need to debug for this
                print "we assume 60 mins for the transportation time"
                google_driving_time = 60
            try:
                google_walking_time = walking_result['rows'][0]['elements'][0]['duration']['value'] / 60
            except:
                google_walking_time = 9999
            
            cur.execute("SELECT max(index) FROM  google_travel_time_table;")
            index = cur.fetchone()[0] + 1
            driving_result = str(driving_result).replace("'", '"')
            walking_result = str(walking_result).replace("'", '"')
            orig_name = orig_name.replace("'", "''")
            dest_name = dest_name.replace("'", "''")

            cur.execute("INSERT INTO google_travel_time_table VALUES (%i, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s','%s', '%s', '%s', '%s', '%s', '%s', %s, %s);" %(index, id_, orig_name, orig_idx, dest_name, dest_idx, orig_coord_lat, orig_coord_long, dest_coord_lat, dest_coord_long, orig_coords, dest_coords, google_driving_url, google_walking_url, str(driving_result), str(walking_result), google_driving_time, google_walking_time))
            conn.commit()
            name_list.append(orig_name + " to " + dest_name)
            google_ids.append(id_)
            driving_time_list.append(google_driving_time)
            walking_time_list.append(google_walking_time)
        else:
            
            cur.execute("SELECT orig_name, dest_name, google_driving_time, google_walking_time FROM google_travel_time_table WHERE id_field = '%s';" % (id_))
            orig_name, dest_name, google_driving_time, google_walking_time = cur.fetchone()
            name_list.append(orig_name + " to " + dest_name)
            google_ids.append(id_)
            driving_time_list.append(google_driving_time)
            walking_time_list.append(google_walking_time)
    conn.close()
    # return event_ids, google_ids, name_list, driving_time_list, walking_time_list
    return event_ids, driving_time_list, walking_time_list

def find_google_result(orig_coords, dest_coords, orig_name, dest_name, i):
    google_driving_url = "https://maps.googleapis.com/maps/api/distancematrix/json?origins={0}&destinations={1}&mode=driving&language=en-EN&sensor=false&key={2}".format(orig_coords.replace(' ', ''), dest_coords.replace(' ', ''), api_key[i])
    google_walking_url = "https://maps.googleapis.com/maps/api/distancematrix/json?origins={0}&destinations={1}&mode=walking&language=en-EN&sensor=false&key={2}".format(orig_coords.replace(' ', ''), dest_coords.replace(' ', ''), api_key[i])
    driving_result = simplejson.load(urllib.urlopen(google_driving_url))
    walking_result = simplejson.load(urllib.urlopen(google_walking_url))
    if (driving_result['status'] == 'OVER_QUERY_LIMIT') or (walking_result['status'] == 'OVER_QUERY_LIMIT'):
        return False

    if driving_result['rows'][0]['elements'][0]['status'] == 'ZERO_RESULTS':
        google_driving_url = "https://maps.googleapis.com/maps/api/distancematrix/json?origins={0}&destinations={1}&mode=driving&language=en-EN&sensor=false&key={2}".format(orig_name.replace(' ', '+').replace('-', '+'), dest_name.replace(' ', '+').replace('-', '+'), api_key[i])
        driving_result = simplejson.load(urllib.urlopen(google_driving_url))

    if walking_result['rows'][0]['elements'][0]['status'] == 'ZERO_RESULTS':
        google_walking_url = "https://maps.googleapis.com/maps/api/distancematrix/json?origins={0}&destinations={1}&mode=walking&language=en-EN&sensor=false&key={2}".format(orig_name.replace(' ', '+').replace('-', '+'), dest_name.replace(' ', '+').replace('-', '+'), api_key[i])
        walking_result= simplejson.load(urllib.urlopen(google_walking_url))
    google_driving_url = google_driving_url.replace("'s", "%27")
    google_walking_url = google_walking_url.replace("'s", "%27")
    return [driving_result, walking_result, google_driving_url, google_walking_url]

def db_remove_extra_events(event_ids, driving_time_list, walking_time_list, max_time_spent=600):
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    if len(event_ids) > 1:
        cur.execute("SELECT DISTINCT SUM(adjusted_visit_length) FROM poi_detail_table WHERE index IN %s;" % (tuple(event_ids),))
        time_spent = cur.fetchone()[0]
        conn.close()
    else:
        cur.execute("SELECT DISTINCT SUM(adjusted_visit_length) FROM poi_detail_table WHERE index = %s;" % (event_ids))
        time_spent = cur.fetchone()[0]
        conn.close()
    travel_time = int(sum(np.minimum(np.array(driving_time_list), np.array(walking_time_list))))
    time_spent = int(time_spent) + travel_time
    if time_spent > max_time_spent:
        update_event_ids = event_ids[:-1]
        update_driving_time_list = driving_time_list[:-1]
        update_walking_time_list = walking_time_list[:-1]
        return db_remove_extra_events(update_event_ids, update_driving_time_list, update_walking_time_list)
    else:
        return event_ids, driving_time_list, walking_time_list, time_spent

def db_adjust_events(event_ids, driving_time_list, walking_time_list, not_visited_poi_lst, event_type, city, max_time_spent=600):
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    if len(event_ids) > 1:
        cur.execute("SELECT DISTINCT SUM(adjusted_visit_length) FROM poi_detail_table WHERE index IN %s;" % (tuple(event_ids),))
        time_spent = cur.fetchone()[0]
        conn.close()
    else:
        cur.execute("SELECT DISTINCT SUM(adjusted_visit_length) FROM poi_detail_table WHERE index = %s;" % (event_ids[0]))
        time_spent = cur.fetchone()[0]
        conn.close()
    travel_time = int(sum(np.minimum(np.array(driving_time_list), np.array(walking_time_list))))
    time_spent = int(time_spent) + travel_time

    if (time_spent > max_time_spent):

        update_event_ids = event_ids[:-1]
        update_driving_time_list = driving_time_list[:-1]
        update_walking_time_list = walking_time_list[:-1]
        conn = psycopg2.connect(conn_str)
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT adjusted_visit_length FROM poi_detail_table WHERE index = %s;" % (event_ids[-1]))
        if cur.fetchone()[0] <= 240:
            not_visited_poi_lst.append(event_ids[-1])
        conn.close()
        return db_adjust_events(update_event_ids, update_driving_time_list, update_walking_time_list, not_visited_poi_lst, event_type, city)
    elif (time_spent < max_time_spent - 240) and (len(not_visited_poi_lst) > 1):
        event_ids = list(event_ids)
        event_ids.extend(not_visited_poi_lst)
        event_ids, event_type = db_event_cloest_distance(event_ids=event_ids, event_type=event_type, city_name=city)
        event_ids, driving_time_list, walking_time_list = db_google_driving_walking_time(event_ids, event_type)
        return db_adjust_events(event_ids, driving_time_list, walking_time_list, [], event_type, city)
    else:
        return event_ids, driving_time_list, walking_time_list, time_spent, not_visited_poi_lst


def db_day_trip_details(event_ids, i):
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    details = []
    #details dict includes: id, name,address, day
    for event_id in event_ids:
        cur.execute("SELECT index, name, address, coord_lat, coord_long, city, state, icon_url, check_full_address, poi_type, adjusted_visit_length, img_url FROM poi_detail_table WHERE index = %s;" % (event_id))
        a = cur.fetchone()
        details.append({'id': a[0],'name': a[1],'address': a[2], 'day': i, 'coord_lat': a[3], 'coord_long': a[4], 'city': a[5], 'state': a[6], 'icon_url': a[7], 'check_full_address': a[8], 'poi_type': a[9], 'adjusted_visit_length': a[10], 'img_url': a[11]})
    conn.close()
    return details

def check_address(index):
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    cur.execute("SELECT address FROM poi_detail_table  WHERE index = %s;" % (index))
    a = cur.fetchone()[0]
    conn.close()
    if a:
        return True
    else:
        return False

def db_address(event_ids):
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    for i in event_ids[:-1]:
        if not check_address(i):
            cur.execute("SELECT driving_result FROM google_travel_time_table WHERE orig_idx = %s;" % (i))
            a = cur.fetchone()[0]
            add = ast.literal_eval(a)['origin_addresses'][0]
            cur.execute("update poi_detail_table  set address = '%s' WHERE index = %s;" % (add, i))
            conn.commit()
    last = event_ids[-1]
    if not check_address(last):
        cur.execute("SELECT driving_result FROM google_travel_time_table WHERE dest_idx = %s;" % (last))
        a = cur.fetchone()[0]
        add = ast.literal_eval(a)['destination_addresses'][0]
        cur.execute("update poi_detail_table  set address = '%s' WHERE index = %s;" % (add, last))
        conn.commit()
    conn.close()

def kmeans_leabels_day_order(day_labels):
    return [k for k, v in Counter(day_labels).most_common()]

def find_ip_geo_location(ip_address):
    import socket
    import struct
    packedIP = socket.inet_aton(ip_address)
    ip_number = struct.unpack("!L", packedIP)[0]
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    cur.execute("SELECT country_code, country_name, region_name, city_name FROM ip2location_db3 WHERE ip_FROM<{0} AND ip_to>{0} limit 1;".format(ip_number))
    a = cur.fetchone()
    conn.close()
    return a

def convert_event_ids_to_lst(event_ids):
    try:
        if type(ast.literal_eval(event_ids)) == list:
            event_ids = map(float, ast.literal_eval(event_ids))
            new_event_ids = map(int, (event_ids))
        else: 
            event_ids = re.sub("\s+", ",", event_ids.strip())
            event_ids = event_ids.replace('.', '')
            event_ids = map(float, event_ids.strip('[').strip(']').strip(',').split(','))
            new_event_ids = map(int, (event_ids))
    except:
        event_ids = re.sub("\s+", ",", event_ids.strip())
        event_ids = event_ids.replace('.', '')
        event_ids = map(float, event_ids.strip('[').strip(']').strip(',').split(','))
        new_event_ids = map(int, (event_ids))
        return new_event_ids


def abb_to_full_state(state):
    
    #may need to check by using dict.
    # please see outside.helpers.check_state()

    '''
    Convert state_abb to full state name
    '''
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT state FROM city_state_coords_table WHERE state_abb = '{}';".format(state))
    full_state = cur.fetchone()
    conn.close()
    if full_state:
        return full_state[0]
    else:
        return state

def serach_city_state(city_state):
    '''
    Only valid within the U.S.
    Create new table for city_coords with state_abb
    create table city_state_coords_table as SELECT a.*, b.state_abb 
        FROM all_cities_coords_table as a left join 
        (SELECT DISTINCT state, state_abb FROM county_table order by state_abb) as b 
        on a.state = b.state order by a.index;
    update city_state_coords_table set state_abb = 'DC' WHERE state_abb is null;
    '''
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    if ',' in city_state:
        city = city_state.split(',')[0].strip()
        state = city_state.split(',')[1].strip()
        # cur.execute("SELECT city, state_abb FROM city_state_coords_table WHERE city % '{0}' AND (state % '{1}' or state_abb % '{1}') order by similarity(city, '{0}') desc limit 5;".format(city,state))
        cur.execute("SELECT temp.city, temp.state_abb, concat_ws(', ',temp.city::text, temp.state_abb::text) FROM (select distinct city, state_abb, state FROM poi_detail_table) AS temp WHERE temp.city % '{0}' AND (temp.state % '{1}' OR temp.state_abb % '{1}') ORDER BY similarity(temp.city, '{0}') DESC LIMIT 5;".format(city, state))
    else:
        city = city_state.strip()
        # cur.execute("SELECT city, state_abb, concat_ws(', ',city::text, state_abb::text) FROM city_state_coords_table WHERE city % '{0}' order by similarity(city, '{0}') desc limit 5;".format(city))
        cur.execute("SELECT temp.city, temp.state_abb, concat_ws(', ',temp.city::text, temp.state_abb::text) FROM (select distinct city, state_abb FROM poi_detail_table) AS temp WHERE temp.city % '{0}' ORDER BY similarity(temp.city, '{0}') DESC LIMIT 5;".format(city))
    c = cur.fetchall()
    conn.close()
    return c


