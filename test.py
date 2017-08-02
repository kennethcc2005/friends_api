import psycopg2
import ast
import numpy as np
import simplejson
import urllib
import json
import re
from helpers import *
import os

def add_event_day_trip(poi_id, poi_name, trip_locations_id, full_trip_id, full_day = True, unseen_event = False, username_id=1):
    #day number is sth to remind! need to create better details maybe
    #
    #click buttom
    #
    #
    conn = psycopg2.connect(conn_str)   
    cur = conn.cursor()
    username_id = 1   
    cur.execute("select full_day, event_ids, details from day_trip_table_city where trip_locations_id='%s'" %(trip_locations_id))  
    (full_day, event_ids, day_details) = cur.fetchone()
    cur.execute("select trip_location_ids, details, city, state, n_days from full_trip_table_city where full_trip_id='%s'" %(full_trip_id))  
    (trip_location_ids, full_trip_details, city, state, n_days) = cur.fetchone()
    event_ids = json.loads(event_ids)
    event_ids = map(int, event_ids)
    print event_ids
    day_details = json.loads(day_details)
    if not poi_id:
        print 'type event_ids', type(event_ids), type(poi_name),str(poi_name).replace(' ','-').replace("'",''), '-'.join(map(str,event_ids))
        new_trip_location_id = '-'.join(map(str,event_ids))+'-'+str(poi_name).replace(' ','-').replace("'",'')
        cur.execute("select details from day_trip_table_city where trip_locations_id='%s'" %(new_trip_location_id))
        a = cur.fetchone()
        if bool(a):
            conn.close()
            details = ast.literal_eval(a[0])
            return trip_locations_id, new_trip_location_id, details
        else:
            cur.execute("select max(index) from day_trip_table_city;")
            new_index = cur.fetchone()[0]+1
            #need to make sure the type is correct for detail!
            day = day_details[-1]['day']
            new_event_detail = {"name": poi_name, "day": day, "coord_lat": "None", "coord_long": "None","address": "None", "id": "None", "city": "", "state": ""}
            for index, detail in enumerate(day_details):
                if type(detail) == str:
                    day_details[index] = ast.literal_eval(detail)
            day_details.append(new_event_detail)
            #get the right format of detail: change from list to string and remove brackets and convert quote type
            day_detail = str(day_details).replace("'","''")
            event_ids.append(poi_name)
            event_ids = str(event_ids).replace("'","''")
            cur.execute("INSERT INTO day_trip_table_city VALUES (%i, '%s',%s,%s,'%s','%s','%s','%s','%s');" %(new_index, new_trip_location_id, full_day, False, county, state, day_detail,'add',event_ids))
            
            conn.commit()
            conn.close()
            return trip_locations_id, new_trip_location_id, day_detail
    else:
        if trip_locations_id.isupper() or trip_locations_id.islower():
            new_trip_location_id = '-'.join(map(str,event_ids))+'-'+str(poi_id)
        else:
            # db_event_cloest_distance(trip_locations_id=None,event_ids=None, event_type = 'add',new_event_id = None, city_name =None)
            print 'add: ', trip_locations_id, poi_id
            event_ids, event_type = db_event_cloest_distance(trip_locations_id=trip_locations_id, new_event_id=poi_id)
            event_ids=event_ids.tolist()
            event_ids=map(float, event_ids)
            print event_ids, type(event_ids)
            event_ids, driving_time_list, walking_time_list = db_google_driving_walking_time(event_ids,event_type = 'add')
            new_trip_location_id = '-'.join(map(str,event_ids))
            event_ids = map(int,list(event_ids))
        cur.execute("select details from day_trip_table_city where trip_locations_id='%s'" %(new_trip_location_id)) 
        a = cur.fetchone()
        if not a:
            details = []
            if type(day_details[0]) == dict:
                event_day = day_details[0]['day']
            else:
                event_day = ast.literal_eval(day_details[0])['day']
            for item in event_ids:
                cur.execute("select index, name, address, coord_lat, coord_long, city, state, icon_url, check_full_address, poi_type, adjusted_visit_length, img_url from poi_detail_table where index = '%s';" %(item))
                a = cur.fetchone()
                detail = {'id': a[0],'name': a[1],'address': a[2], 'day': event_day, 'coord_lat': a[3], 'coord_long': a[4], 'city': a[5], 'state': a[6], 'icon_url': a[7], 'check_full_address': a[8], 'poi_type': a[9], 'adjusted_visit_length': a[10], 'img_url': a[11]}
                details.append(detail)
            #need to make sure event detail can append to table!
            cur.execute("select max(index) from day_trip_table_city;")
            new_index = cur.fetchone()[0] +1
            event_type = 'add'
            cur.execute("insert into day_trip_table_city (index, trip_locations_id,full_day, regular, city, state, details, event_type, event_ids) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)" ,(new_index, new_trip_location_id, full_day, False, city, state, json.dumps(details), event_type, json.dumps(event_ids)))
            conn.commit()
            conn.close()
            return trip_locations_id, new_trip_location_id, details
        else:
            conn.close()
            #need to make sure type is correct.
            if type(a[0]) == str:
                return trip_locations_id, new_trip_location_id, ast.literal_eval(a[0])
            else:
                return trip_locations_id, new_trip_location_id, a[0]

if __name__ == '__main__':
    poi_id="356"
    poi_name="Golden Gate Park"
    full_trip_id="352.0-371.0-376.0-366-357.0-364"
    trip_location_id="352.0-371.0-376.0-366-357.0-364"

    a, b, c = add_event_day_trip(poi_id, poi_name, trip_location_id, full_trip_id)
    print a, b, c
    # print result

