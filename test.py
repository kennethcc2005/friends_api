import psycopg2
import ast
import numpy as np
import simplejson
import urllib
import json
import re
from helpers import *
import os

def outside_add_search_event(poi_name, outside_route_id):
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    cur.execute("SELECT origin_city, origin_state, event_ids FROM outside_route_table WHERE outside_route_id =  '%s' LIMIT 1;" %(outside_route_id))
    city, state, event_ids = cur.fetchone()
    print city, state, event_ids

    event_ids = map(int,map(float,event_ids.replace("[","").replace("]","").replace(" ","").split(",")))


    new_event_ids = tuple(event_ids)
    print new_event_ids
    cur.execute("SELECT index, coord_lat, coord_long FROM all_cities_coords_table WHERE city ='%s' AND state = '%s';" % (city, state))
    id_, start_lat, start_long = cur.fetchone()
    cur.execute("SELECT index, name FROM poi_detail_table WHERE index NOT IN {0} AND interesting = True AND ST_Distance_Sphere(geom, ST_MakePoint({2},{3})) <= 150 * 1609.34 and name % '{1}'  ORDER BY similarity(name, '{1}') DESC LIMIT 7;".format(new_event_ids, poi_name, start_long, start_lat))

    results = cur.fetchall()
    if results > 0:
        poi_ids, poi_lst = [int(row[0]) for row in results], [row[1] for row in results]
    else:
        poi_ids, poi_lst = [], []
    print 'add search result: ', poi_ids, poi_lst
    if 7-len(poi_lst)>0:
        event_ids.extend(poi_ids)
        new_event_ids = str(tuple(event_ids))
        cur.execute("SELECT index, name FROM poi_detail_table WHERE index NOT IN {0} AND interesting = True AND ST_Distance_Sphere(geom, ST_MakePoint({1},{2})) <= 150 * 1609.34 ORDER BY num_reviews DESC LIMIT {3};".format(new_event_ids, start_long, start_lat, 7-len(poi_ids)))

        results.extend(cur.fetchall())
    poi_dict = {d[1]:d[0] for d in results}
    poi_names = [d[1] for d in results]
    conn.close()

    return poi_dict, poi_names

if __name__ == '__main__':
	type_input = "abc"
	outside_route_id =  'CALIFORNIA-SAN-FRANCISCO-E-1-1-1'

	poi_dict, poi_names= outside_add_search_event(type_input,outside_route_id)
	print poi_dict, poi_names

