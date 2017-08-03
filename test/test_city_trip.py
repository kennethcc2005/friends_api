import psycopg2
import ast
import numpy as np
import simplejson
import urllib
import json
import re
from helpers import *
import os

def switch_suggest_event(full_trip_id, update_trip_location_id, update_suggest_event, username_id=1): 
    conn = psycopg2.connect(conn_str)   
    cur = conn.cursor()   
    cur.execute("SELECT trip_location_ids FROM full_trip_table_city WHERE full_trip_id = '%s';" %(full_trip_id)) 
    # cur.execute("select trip_location_ids, details from full_trip_table where full_trip_id = '%s';" %(full_trip_id)) 
    trip_location_ids = ast.literal_eval(cur.fetchone()[0])
    update_suggest_event = ast.literal_eval(update_suggest_event)
    full_trip_details = []
    full_trip_trip_locations_id = []
    new_update_trip_location_id = ''
    # for trip_location_id in trip_location_ids:
    #     cur.execute("SELECT * FROM day_trip_table_city WHERE trip_locations_id  = '%s' LIMIT 1;" %(trip_location_id)) 
    #     (index, trip_locations_id, full_day, regular, county, state, detail, event_type, event_ids) = cur.fetchone()
    #     event_ids = convert_event_ids_to_lst(event_ids)
    #     detail = list(ast.literal_eval(detail[1:-1]))

    #     #make sure detail type is dict!
    #     for i,v in enumerate(detail):
    #         if type(v) != dict:
    #             detail[i] = ast.literal_eval(v)
    #     full_day = True
    #     event_type = 'suggest'
    #     for idx, event_id in enumerate(event_ids):
    #         if str(event_id) in update_suggest_event:
    #             regular = False
    #             replace_event_detail = update_suggest_event[str(event_id)]
    #             replace_event_detail['day'] = detail[idx]['day']
    #             detail[idx] = replace_event_detail
    #             event_ids[idx] = replace_event_detail['id']
    #     if not regular:
    #         trip_locations_id = '-'.join(map(str,event_ids))
    #         # if not check_day_trip_id(trip_locations_id):
    #         if not check_day_trip_id_city(trip_locations_id):
    #             cur.execute("SELECT max(index) FROM day_trip_table_city;")
    #             new_index = cur.fetchone()[0] + 1
    #             cur.execute("INSERT INTO day_trip_table_city VALUES (%i, '%s',%s,%s,'%s','%s','%s','%s','%s');" %(new_index, trip_locations_id, full_day, regular, county, state, str(detail).replace("'",'"'),event_type,event_ids))
    #             conn.commit()
    #     if update_trip_location_id == trip_location_id:
    #         new_update_trip_location_id = trip_locations_id
    #     full_trip_details.extend(detail)
    #     full_trip_trip_locations_id.append(trip_locations_id)


    # print 'return:',full_trip_id, full_trip_details, full_trip_trip_locations_id, new_update_trip_location_id
    # if full_trip_trip_locations_id != trip_location_ids:
    #     new_full_trip_id = '-'.join(full_trip_trip_locations_id)
    #     if not check_full_trip_id(new_full_trip_id):
    #         n_days = len(trip_location_ids)
    #         regular =False
    #         cur.execute("SELECT max(index) FROM full_trip_table_city;")
    #         new_index = cur.fetchone()[0] + 1
    #         cur.execute("INSERT INTO full_trip_table_city VALUES (%s, %s, '%s', '%s', %s, '%s', '%s', '%s', %s);" %(new_index, username_id, new_full_trip_id, str(full_trip_trip_locations_id).replace("'","''"), regular, county, state, str(full_trip_details).replace("'","''"), n_days))
    #         conn.commit()
    #         conn.close()
    #     return new_full_trip_id, full_trip_details, full_trip_trip_locations_id, new_update_trip_location_id
    # if new_update_trip_location_id == '':
    #     new_update_trip_location_id = update_trip_location_id
    # return full_trip_id, full_trip_details, full_trip_trip_locations_id, new_update_trip_location_id



if __name__ == '__main__':

    result = switch_suggest_event("CALIFORNIA-SAN-JOSE-1-4", 4633, 246)
    print result

