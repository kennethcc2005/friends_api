import psycopg2
import ast
import numpy as np
import simplejson
import urllib
import json
import re
from helpers import *
import os

def remove_event(full_trip_id, trip_locations_id, remove_event_id, username_id=1, remove_event_name=None, event_day=None, full_day = True):
    #may have some bugs if trip_locations_id != remove_event_id as last one:)   test and need to fix
    print 'init:', full_trip_id, trip_locations_id, remove_event_id
    conn = psycopg2.connect(conn_str)   
    cur = conn.cursor()

    if trip_locations_id == remove_event_id:
        if full_trip_id != trip_locations_id:
            # full_trip_id = full_trip_id[len(str(trip_locations_id))+1:]
            cur.execute("select trip_location_ids from full_trip_table_city where full_trip_id = '%s';" %(full_trip_id)) 
            # cur.execute("select trip_location_ids, details from full_trip_table where full_trip_id = '%s';" %(full_trip_id)) 
            trip_location_ids = cur.fetchone()[0]
            trip_location_ids = ast.literal_eval(trip_location_ids)
            trip_location_ids.remove(str(trip_locations_id))
            full_trip_details = []
            for trip_id in trip_location_ids:
                cur.execute("select details from day_trip_table_city where trip_locations_id = '%s';" %(trip_id)) 
                details = cur.fetchone()[0]
                trip_details = ast.literal_eval(details)
                full_trip_details.extend(trip_details)
            conn.close()
            new_full_trip_id = '-'.join(trip_location_ids)
            for index, detail in enumerate(full_trip_details):
                full_trip_details[index] = ast.literal_eval(detail)
                full_trip_details[index]['address'] = full_trip_details[index]['address'].strip(', ').replace(', ,',',')
            print full_trip_details, new_full_trip_id, trip_location_ids
            return new_full_trip_id, full_trip_details, trip_location_ids
        return '','',''
    
    print 'remove id: ', trip_locations_id
    cur.execute("select * from day_trip_table_city where trip_locations_id='%s'" %(trip_locations_id)) 
    (index, trip_locations_id, full_day, regular, county, state, detail, event_type, event_ids) = cur.fetchone()

    new_event_ids = json.loads(event_ids)
    remove_event_id = int(remove_event_id)
    new_event_ids.remove(remove_event_id)
    new_trip_locations_id = '-'.join(str(event_id) for event_id in new_event_ids)
    # if check_id:
    #     return new_trip_locations_id, check_id[-3]
    detail = ast.literal_eval(detail[1:-1])
    for index, trip_detail in enumerate(detail):
        if type(trip_detail) == str:
            if ast.literal_eval(trip_detail)['id'] == remove_event_id:
                remove_index = index
                break
        else:
            if trip_detail['id'] == remove_event_id:
                remove_index = index
                break

    new_detail = list(detail)
    new_detail.pop(remove_index)
    new_detail =  str(new_detail).replace("'","''")
    regular = False
    cur.execute("select * from day_trip_table_city where trip_locations_id='%s'" %(new_trip_locations_id))  
    check_id = cur.fetchone()
    if not check_id:
        cur.execute("select max(index) from day_trip_table_city;")
        new_index = cur.fetchone()[0]
        new_index+=1
        cur.execute("INSERT INTO day_trip_table_city VALUES (%s, %s, %s, %s, %s, %s, %s, %s,%s);" ,(new_index, new_trip_locations_id, full_day, regular, city, state, new_detail, event_type, new_event_ids))  
        conn.commit()
    conn.close()
    new_full_trip_id, new_full_trip_details,new_trip_location_ids = new_full_trip_afer_remove_event(full_trip_id, trip_locations_id, new_trip_locations_id, username_id=1)
    print 'delete trip details: ', new_full_trip_details
    return new_full_trip_id, new_full_trip_details,new_trip_location_ids, new_trip_locations_id

def new_full_trip_afer_remove_event(full_trip_id, old_trip_locations_id, new_trip_locations_id, username_id=1):
    conn = psycopg2.connect(conn_str)   
    cur = conn.cursor() 
    username_id = 1
    cur.execute("SELECT trip_location_ids, regular, city, state, details, n_days FROM full_trip_table_city WHERE full_trip_id = '{}' LIMIT 1;".format(full_trip_id))
    trip_location_ids, regular, county, state, details, n_days = cur.fetchone()
    trip_location_ids = ast.literal_eval(trip_location_ids)
    trip_location_ids[:] = [new_trip_locations_id if x==old_trip_locations_id else x for x in trip_location_ids]
    new_full_trip_id = '-'.join(trip_location_ids)
    new_full_trip_details = []
    for trip_locations_id in trip_location_ids:
        cur.execute("SELECT details FROM day_trip_table_city WHERE trip_locations_id = '{}' LIMIT 1;".format(trip_locations_id))
        detail = cur.fetchone()[0]
        # print detail, type(detail)
        detail = json.loads(detail)
        # print detail, type(detail)
        # detail[:] = [ast.literal_eval(x) if type(x) == str else x for x in detail]
        new_full_trip_details.extend(detail)
    regular=False
    if not check_full_trip_id(new_full_trip_id):
        cur.execute("SELECT max(index) FROM full_trip_table_city;")
        full_trip_index = cur.fetchone()[0] + 1
        cur.execute("INSERT INTO full_trip_table_city (index, username_id, full_trip_id,trip_location_ids, regular, city, state, details, n_days) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);" ,(full_trip_index, username_id, new_full_trip_id, json.dumps(trip_location_ids), regular, ciy, state, json.dumps(new_full_trip_details), n_days))
        conn.commit()
    conn.close()
    return new_full_trip_id, new_full_trip_details,trip_location_ids

if __name__ == '__main__':
    # poi_id="356"
    # poi_name="Golden Gate Park"
    # full_trip_id="352.0-371.0-376.0-366-357.0-364"
    # trip_location_id="352.0-371.0-376.0-366-357.0-364"
    full_trip_id="CALIFORNIA-SAN-FRANCISCO-1-2-0-352.0-371.0-356.0-361.0-363.0-359.0-375.0-364.0"
    event_id="364"
    trip_locations_id="352.0-371.0-356.0-361.0-363.0-359.0-375.0-364.0"
    a, b, c = remove_event(full_trip_id, trip_locations_id, event_id)
    print a, b, c
    # print result

