# -*- coding: utf-8 -*-
import psycopg2
import ast
import numpy as np
import simplejson
import urllib
from helpers import *
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(BASE_DIR, 'travel_with_friends_api/api_key_list.config')) as key_file:
    api_key_list = json.load(key_file)
api_key = api_key_list["distance_api_key_list"]
conn_str = api_key_list["conn_str"]

def angle_between(p1, p2):
    ang1 = np.arctan2(*p1[::-1])
    ang2 = np.arctan2(*p2[::-1])
    return np.rad2deg((ang1 - ang2) % (2 * np.pi))

def calculate_initial_compass_bearing(pointA, pointB):
    """
    Calculates the bearing between two points.
    The formulae used is the following:
    theta = atan2(sin(delta(long)).cos(lat2),
                  cos(lat1).sin(lat2) − sin(lat1).cos(lat2).cos(delta(long)))
    :Parameters:
      - `pointA: The tuple representing the latitude/longitude for the
        first point. Latitude and longitude must be in decimal degrees
      - `pointB: The tuple representing the latitude/longitude for the
        second point. Latitude and longitude must be in decimal degrees
    :Returns:
      The bearing in degrees
    :Returns Type:
      float
    """
    if (type(pointA) != tuple) or (type(pointB) != tuple):
        raise TypeError("Only tuples are supported as arguments")

    lat1 = math.radians(pointA[0])
    lat2 = math.radians(pointB[0])

    diffLong = math.radians(pointB[1] - pointA[1])

    x = math.sin(diffLong) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1)
            * math.cos(lat2) * math.cos(diffLong))

    initial_bearing = math.atan2(x, y)

    # Now we have the initial bearing but math.atan2 return values
    # from -180° to + 180° which is not what we want for a compass bearing
    # The solution is to normalize the initial bearing as shown below
    initial_bearing = math.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360

    return compass_bearing

def direction_from_orgin(start_coord_long,  start_coord_lat, target_coord_long, target_coord_lat):
    angle = calculate_initial_compass_bearing((start_coord_lat, start_coord_long), (target_coord_lat, target_coord_long))
    if (angle > 45) and (angle < 135):
        return 'E'
    elif (angle > 135) and (angle < 215):
        return 'S'
    elif (angle > 215) and (angle < 305):
        return 'W'
    else:
        return 'N'

def check_direction(start_lat, start_long, outside_lat, outside_long, target_direction):
    angle_dict={"E":range(45,135), "S":range(135,215), "W":range(215,305), "N":range(0,45) + range(305,360)}
    angle = calculate_initial_compass_bearing((start_lat, start_long), (outside_lat, outside_long))

    if int(angle) in angle_dict[target_direction]:
        return True
    else: 
        return False

def travel_outside_coords(current_city, current_state, direction=None, n_days=1):
    conn = psycopg2.connect(conn_str)   
    cur = conn.cursor() 
    #coord_long, coord_lat
    cur.execute("select index, coord_lat, coord_long from all_cities_coords_table where city ='%s' and state = '%s';" %(current_city, current_state)) 
    id_, coord_lat, coord_long = cur.fetchone()
    #city, coord_lat, coord_long
    cur.execute("select distinct city, coord_lat, coord_long from all_cities_coords_table where city !='%s' and state = '%s';" %(current_city, current_state))  
    coords = cur.fetchall()     
    conn.close()
    
    return id_, coords, coord_lat, coord_long

def travel_outside_with_direction (origin_city,origin_state, target_direction, furthest_len, n_days=1):
    poi_info = []
    conn = psycopg2.connect(conn_str)   
    cur = conn.cursor() 
    #coord_long, coord_lat
    cur.execute("select index, coord_lat, coord_long from all_cities_coords_table where city ='%s' and state = '%s';" %(origin_city,origin_state)) 
    id_, start_lat, start_long = cur.fetchone()

    cur.execute("SELECT index, coord_lat, coord_long, adjusted_visit_length, ranking, review_score, num_reviews FROM poi_detail_table_v2 WHERE city != '%s' and ST_Distance_Sphere(geom, ST_MakePoint(%s,%s)) <= %s * 1609.34;"%(origin_city, start_long, start_lat,furthest_len)) 
    item = cur.fetchall()
    conn.close()
    for coords in item:
        if check_direction(start_lat, start_long, coords[1] ,coords[2], target_direction):
            poi_info.append(coords)
    return id_, start_lat, start_long, np.array(poi_info)
    

def check_outside_trip_id(outside_trip_id, debug):
    '''
    Check outside trip id exist or not.  
    '''
    conn = psycopg2.connect(conn_str)  
    cur = conn.cursor()  
    cur.execute("select outside_trip_id from outside_trip_table where outside_trip_id = '%s'" %(outside_trip_id)) 
    a = cur.fetchone()
    # print 'outside stuff id', a, bool(a)
    conn.close()
    if bool(a):
        if not debug: 
            return a[0]
        else:
            return True
    else:
        return False

def db_outside_route_trip_details(event_ids, route_i):
    conn=psycopg2.connect(conn_str)
    cur = conn.cursor()
    details = []
    #details dict includes: id, name,address, day
    for event_id in event_ids:
        cur.execute("select index, name, address, coord_lat, coord_long, city, state from poi_detail_table_v2 where index = %s;" %(event_id))
        a = cur.fetchone()
        details.append({'id': a[0],'name': a[1],'address': a[2], 'coord_lat': a[3], 'coord_long':a[4], 'route': route_i, 'city': a[5], 'state': a[6]})
    conn.close()
    return details

def db_outside_google_driving_walking_time(city_id, start_coord_lat, start_coord_long, event_ids, event_type, origin_city, origin_state):
    '''
    Get estimated travel time from google api.  
    Limit 1000 calls per day.
    '''
    conn = psycopg2.connect(conn_str)  
    cur = conn.cursor()  
    google_ids = []
    driving_time_list = []
    walking_time_list = []
    name_list = []
    city_to_poi_id = str(city_id) + '0000'+str(event_ids[0])
    if not check_city_to_poi(city_to_poi_id):
        cur.execute("select name, coord_lat, coord_long from poi_detail_table_v2 where index = %s "%(event_ids[0]))
        dest_name, dest_coord_lat, dest_coord_long = cur.fetchone()
        orig_coords = str(start_coord_lat)+','+str(start_coord_long)
        dest_coords = str(dest_coord_lat)+','+str(dest_coord_long)
        google_driving_url = "https://maps.googleapis.com/maps/api/distancematrix/json?origins={0}&destinations={1}&mode=driving&language=en-EN&sensor=false&key={2}".\
                                format(orig_coords.replace(' ',''),dest_coords.replace(' ',''),api_key[0])
        google_walking_url = "https://maps.googleapis.com/maps/api/distancematrix/json?origins={0}&destinations={1}&mode=walking&language=en-EN&sensor=false&key={2}".\
                                format(orig_coords.replace(' ',''),dest_coords.replace(' ',''),api_key[0])
        driving_result= simplejson.load(urllib.urlopen(google_driving_url))
        walking_result= simplejson.load(urllib.urlopen(google_walking_url))
        orig_name = origin_city.upper().replace(' ','+').replace('-','+') + '+' + origin_state.upper().replace(' ','+').replace('-','+')
        if driving_result['rows'][0]['elements'][0]['status'] == 'ZERO_RESULTS':
            google_driving_url = "https://maps.googleapis.com/maps/api/distancematrix/json?origins={0}&destinations={1}&mode=driving&language=en-EN&sensor=false&key={2}".\
                                format(orig_name,dest_name.replace(' ','+').replace('-','+'),api_key[0])
            driving_result= simplejson.load(urllib.urlopen(google_driving_url))
        if walking_result['rows'][0]['elements'][0]['status'] == 'ZERO_RESULTS':
            google_walking_url = "https://maps.googleapis.com/maps/api/distancematrix/json?origins={0}&destinations={1}&mode=walking&language=en-EN&sensor=false&key={2}".\
                                    format(orig_name,dest_name.replace(' ','+').replace('-','+'),api_key[0])
            walking_result= simplejson.load(urllib.urlopen(google_walking_url))
        if (driving_result['rows'][0]['elements'][0]['status'] == 'NOT_FOUND') and (walking_result['rows'][0]['elements'][0]['status'] == 'NOT_FOUND'):
            new_event_ids = list(event_ids)
            new_event_ids.pop(0)
            new_event_ids = db_outside_event_cloest_distance(start_coord_lat, start_coord_long, event_ids=new_event_ids, event_type = event_type)
            return db_outside_google_driving_walking_time(city_id, start_coord_lat, start_coord_long, new_event_ids, event_type,origin_city, origin_state)
        try:
            city_to_poi_driving_time = driving_result['rows'][0]['elements'][0]['duration']['value']/60
        except:            
            print city, state, dest_name, driving_result #need to debug for this
        try:
            city_to_poi_walking_time = walking_result['rows'][0]['elements'][0]['duration']['value']/60
        except:
            city_to_poi_walking_time = 9999 

        '''
        Need to work on rest of it!
        '''
        cur.execute("select max(index) from  google_city_to_poi_table")
        index = cur.fetchone()[0]+1
        driving_result = str(driving_result).replace("'",'"')
        walking_result = str(walking_result).replace("'",'"')
        orig_name = orig_name.replace("'","''")
        dest_name = dest_name.replace("'","''")
        cur.execute("INSERT INTO google_city_to_poi_table VALUES (%i, %s, %i, '%s','%s', '%s','%s', '%s', '%s', '%s', '%s', '%s','%s', '%s', '%s', '%s', '%s', '%s', %s, %s);" \
                    %(index, city_to_poi_id, city_id, origin_city.replace("'","''"), origin_state, orig_name, dest_name, event_ids[0], start_coord_lat, start_coord_long, dest_coord_lat,\
                   dest_coord_long, orig_coords, dest_coords, google_driving_url, google_walking_url,\
                   str(driving_result), str(walking_result), city_to_poi_driving_time,city_to_poi_walking_time))
        conn.commit()
        name_list.extend([orig_name+" to "+ dest_name,dest_name+" to "+ orig_name])
        google_ids.extend([city_to_poi_id]*2)
        driving_time_list.extend([city_to_poi_driving_time]*2)
        walking_time_list.extend([city_to_poi_walking_time]*2)
    else:
        cur.execute("select orig_name, dest_name, city_to_poi_driving_time, city_to_poi_walking_time from google_city_to_poi_table \
                    where city_to_poi_id = %s " %(city_to_poi_id))
        orig_name, dest_name, city_to_poi_driving_time, city_to_poi_walking_time = cur.fetchone()
        name_list.append(orig_name+" to "+ dest_name)
        google_ids.extend([city_to_poi_id]*2)
        driving_time_list.extend([city_to_poi_driving_time]*2)
        walking_time_list.extend([city_to_poi_walking_time]*2)
    
    for i,v in enumerate(event_ids[:-1]):
        id_ = str(v) + '0000'+str(event_ids[i+1])
        result_check_travel_time_id = check_travel_time_id(id_)
        if not result_check_travel_time_id:
            cur.execute("select name, coord_lat, coord_long from poi_detail_table_v2 where index = %s"%(v))
            orig_name, orig_coord_lat, orig_coord_long = cur.fetchone()
            orig_idx = v
            cur.execute("select name, coord_lat, coord_long from poi_detail_table_v2 where index = %s "%(event_ids[i+1]))
            dest_name, dest_coord_lat, dest_coord_long = cur.fetchone()
            dest_idx = event_ids[i+1]
            orig_coords = str(orig_coord_lat)+','+str(orig_coord_long)
            dest_coords = str(dest_coord_lat)+','+str(dest_coord_long)
            google_driving_url = "https://maps.googleapis.com/maps/api/distancematrix/json?origins={0}&destinations={1}&mode=driving&language=en-EN&sensor=false&key={2}".\
                                    format(orig_coords.replace(' ',''),dest_coords.replace(' ',''),api_key[0])
            google_walking_url = "https://maps.googleapis.com/maps/api/distancematrix/json?origins={0}&destinations={1}&mode=walking&language=en-EN&sensor=false&key={2}".\
                                    format(orig_coords.replace(' ',''),dest_coords.replace(' ',''),api_key[0])
                
            driving_result= simplejson.load(urllib.urlopen(google_driving_url))
            walking_result= simplejson.load(urllib.urlopen(google_walking_url))
            if driving_result['rows'][0]['elements'][0]['status'] == 'ZERO_RESULTS':
                google_driving_url = "https://maps.googleapis.com/maps/api/distancematrix/json?origins={0}&destinations={1}&mode=driving&language=en-EN&sensor=false&key={2}".\
                                    format(orig_name.replace(' ','+').replace('-','+'),dest_name.replace(' ','+').replace('-','+'),api_key[0])
                driving_result= simplejson.load(urllib.urlopen(google_driving_url))
                
            if walking_result['rows'][0]['elements'][0]['status'] == 'ZERO_RESULTS':
                google_walking_url = "https://maps.googleapis.com/maps/api/distancematrix/json?origins={0}&destinations={1}&mode=walking&language=en-EN&sensor=false&key={2}".\
                                        format(orig_name.replace(' ','+').replace('-','+'),dest_name.replace(' ','+').replace('-','+'),api_key[0])
                walking_result= simplejson.load(urllib.urlopen(google_walking_url))
            if (driving_result['rows'][0]['elements'][0]['status'] == 'NOT_FOUND') and (walking_result['rows'][0]['elements'][0]['status'] == 'NOT_FOUND'):
                new_event_ids = list(event_ids)
                new_event_ids.pop(i+1)
                new_event_ids = db_event_cloest_distance(event_ids=new_event_ids, event_type = event_type)
                return db_google_driving_walking_time(new_event_ids, event_type)
            try:
                google_driving_time = driving_result['rows'][0]['elements'][0]['duration']['value']/60
            except:            
                print v, id_, driving_result #need to debug for this
            try:
                google_walking_time = walking_result['rows'][0]['elements'][0]['duration']['value']/60
            except:
                google_walking_time = 9999
        
            cur.execute("select max(index) from  google_travel_time_table")
            index = cur.fetchone()[0]+1
            driving_result = str(driving_result).replace("'",'"')
            walking_result = str(walking_result).replace("'",'"')
            orig_name = orig_name.replace("'","''")
            dest_name = dest_name.replace("'","''")
            cur.execute("INSERT INTO google_travel_time_table VALUES (%i, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s','%s', '%s', '%s', '%s', '%s', '%s', %s, %s);"%(index, id_, orig_name, orig_idx, dest_name, dest_idx, orig_coord_lat, orig_coord_long, dest_coord_long,\
                                   dest_coord_long, orig_coords, dest_coords, google_driving_url, google_walking_url,\
                                   str(driving_result), str(walking_result), google_driving_time, google_walking_time))
            conn.commit()
            name_list.append(orig_name+" to "+ dest_name)
            google_ids.append(id_)
            driving_time_list.append(google_driving_time)
            walking_time_list.append(google_walking_time)
        else:
            
            cur.execute("select orig_name, dest_name, google_driving_time, google_walking_time from google_travel_time_table \
                         where id_field = '%s'" %(id_))
            orig_name, dest_name, google_driving_time, google_walking_time = cur.fetchone()
            name_list.append(orig_name+" to "+ dest_name)
            google_ids.append(id_)
            driving_time_list.append(google_driving_time)
            walking_time_list.append(google_walking_time)
    conn.close()
    return event_ids, google_ids, name_list, driving_time_list, walking_time_list

def db_outside_event_cloest_distance(coord_lat, coord_long, trip_locations_id=None,event_ids=None, event_type = 'add',new_event_id = None):
    '''
    Get matrix cloest distance
    '''
    if new_event_id or not event_ids:
        event_ids, event_type = get_event_ids_list(trip_locations_id)
        if new_event_id:
            event_ids.append(new_event_id)
            
    conn = psycopg2.connect(conn_str)  
    cur = conn.cursor()
    points = np.zeros((len(event_ids), 3))
    for i,v in enumerate(event_ids):
        cur.execute("select index, coord_lat, coord_long from poi_detail_table_v2 where index = %i;"%(float(v)))
        points[i] = cur.fetchone()
    conn.close()
    points = np.vstack((np.array([0, coord_lat, coord_long]),points))
    n,D = mk_matrix(points[:,1:], geopy_dist)
    if len(points) >= 3:
        if event_type == 'add':
            tour = nearest_neighbor(n, 0, D)
            # create a greedy tour, visiting city 'i' first
            z = length(tour, D)
            z = localsearch(tour, z, D)
            tour = np.array(tour[1:])-1
            event_ids = np.array(event_ids)
            return np.array(event_ids)[tour[1:]], event_type
        #need to figure out other cases
        else:
            tour = nearest_neighbor(n, 0, D)
            # create a greedy tour, visiting city 'i' first
            z = length(tour, D)
            z = localsearch(tour, z, D)
            tour = np.array(tour[1:])-1
            event_ids = np.array(event_ids)
            return event_ids[tour], event_type
    else:
        return np.array(event_ids), event_type

def check_city_to_poi(city_to_poi_id):
    conn = psycopg2.connect(conn_str)   
    cur = conn.cursor()   
    cur.execute("select index from google_city_to_poi_table \
                    where city_to_poi_id = %s " %(city_to_poi_id))
    a = cur.fetchone()
    conn.close()
    if bool(a):
        return True
    else:
        return False

def db_remove_outside_extra_events(event_ids, driving_time_list,walking_time_list, max_time_spent=600):
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()  
    if len(event_ids) == 1:
        cur.execute("SELECT DISTINCT SUM(adjusted_visit_length) FROM poi_detail_table_v2 WHERE index = %s;" %(event_ids[0]))
    else:
        cur.execute("SELECT DISTINCT SUM(adjusted_visit_length) FROM poi_detail_table_v2 WHERE index IN %s;" %(tuple(event_ids),))
    total_travel_time = sum(np.minimum(np.array(driving_time_list),np.array(walking_time_list)))
    time_spent = float(cur.fetchone()[0]) + float(total_travel_time)
    conn.close()
    if len(event_ids) == 1:
        return event_ids, driving_time_list, walking_time_list, time_spent
    if time_spent > max_time_spent:
        update_event_ids = event_ids[:-1]
        update_driving_time_list = driving_time_list[:-1]
        update_walking_time_list = walking_time_list[:-1]
        return db_remove_outside_extra_events(update_event_ids, update_driving_time_list, update_walking_time_list)
    else:
        return event_ids, driving_time_list, walking_time_list, time_spent


def check_outside_route_id(outside_route_id, debug = True):
    '''
    Check day trip id exist or not.  
    '''
    conn = psycopg2.connect(conn_str)  
    cur = conn.cursor()  
    cur.execute("select details from outside_route_table where outside_route_id = '%s'" %(outside_route_id)) 
    a = cur.fetchone()
    conn.close()
    if bool(a):
        if not debug: 
            return a[0]
        else:
            return True
    else:
        return False

def sorted_outside_events(info,ix):
    '''
    find the event_id, ranking and review_score, num_reviews columns
    sorted base on ranking then review_score, num_reviews
    
    return sorted list 
    '''
    event_ = info[ix][:,[0,4,5,6]]
    return np.array(sorted(event_, key=lambda x: (-x[3], x[1], -x[2],)))
    #num_reviews, ranking, review_score

def create_outside_event_id_list(big_,medium_,small_):
    # print big_,medium_,small_
    event_type = ''
    if big_.shape[0] >= 1:
        if (medium_.shape[0] < 2) or (big_[0,1] >= medium_[0,1]):
            if small_.shape[0] >= 6:
                event_ids = list(np.concatenate((big_[:1,0], small_[0:6,0]),axis=0))  
            elif small_.shape[0]>0:
                event_ids = list(np.concatenate((big_[:1,0], small_[:,0]),axis=0)) 
            else:
                event_ids = list(np.array(sorted(big_[0:,:], key=lambda x: (-x[1], x[2])))[:,0])
            event_type = 'big'
        else:
            if small_.shape[0] >= 8:
                event_ids = list(np.concatenate((medium_[0:2,0], small_[0:8,0]),axis=0))
            elif small_.shape[0]>0:
                event_ids = list(np.concatenate((medium_[0:2,0], small_[:,0]),axis=0))
            else:
                event_ids = list(np.array(sorted(medium_[0:,:], key=lambda x: (-x[1], x[2])))[:,0])
            event_type = 'med'
    elif medium_.shape[0] >= 2:
        if small_.shape[0] >= 8:
            event_ids = list(np.concatenate((medium_[0:2,0], small_[0:8,0]),axis=0))
        elif small_.shape[0]>0:
            event_ids = list(np.concatenate((medium_[0:2,0], small_[:,0]),axis=0))
        else:
            event_ids = list(np.array(sorted(medium_[0:,:], key=lambda x: (-x[1], x[2])))[:,0])
        event_type = 'med'
    else:
        if small_.shape[0] >= 10:
            if medium_.shape[0]==0:
                event_ids = list(np.array(sorted(small_[0:10,:], key=lambda x: (-x[1], x[2])))[:,0])
            else:
                event_ids = list(np.array(sorted(np.vstack((medium_[:1,:], small_[0:10,:])), key=lambda x: (-x[1], x[2])))[:,0])
        elif small_.shape[0] > 0:
            if medium_.shape[0]==0:
                event_ids = list(np.array(sorted(small_[0:,:], key=lambda x: (-x[1], x[2])))[:,0])
            else:
                event_ids = list(np.array(sorted(np.vstack((medium_, small_)), key=lambda x: (-x[1], x[2])))[:,0])

        else:
            event_ids = list(np.array(sorted(medium_[0:,:], key=lambda x: (x[1],-x[2])))[:,0])
        event_type = 'small'
    # else:

    return event_ids, event_type

