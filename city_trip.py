from helpers import *
import ast
def get_fulltrip_data(state, city, n_days, full_day = True, regular = True, debug = True):
    '''
    Get the default full trip data for each city(county)
    '''
    print 'state, city, ndays', state, city, n_days
    county = find_county(state, city)
    n_days = int(n_days)
    if county:
        full_trip_id = '-'.join([str(state.upper()), str(county.upper().replace(' ','-')),str(int(regular)), str(n_days)])
    else:
        full_trip_id = '-'.join([str(state.upper()), str(city.upper().replace(' ','-')),str(int(regular)), str(n_days)])
    print full_trip_id
    if not check_full_trip_id(full_trip_id, debug):
        trip_location_ids, full_trip_details =[],[]
        county_list_info = db_start_location(county, state, city)
        # print county_list_info
        if county_list_info.shape[0] == 0:
            print city, state, county, "is not in our database!!!!?"
            return [city, state, county, "is not in our database!!!!?"]
        new_end_day = max(county_list_info.shape[0]/6, 1)

        if  n_days > new_end_day:
            return get_fulltrip_data(state, city, new_end_day) 
        time_spent = county_list_info[:,3]
        poi_coords = county_list_info[:,1:3]
        kmeans = KMeans(n_clusters=n_days).fit(poi_coords)
        day_labels = kmeans.labels_
        day_order = kmeans_leabels_day_order(day_labels)
        # print day_labels, day_order
        not_visited_poi_lst = []
        for i,v in enumerate(day_order):
            if county:
                day_trip_id = '-'.join([str(state), str(county.upper().replace(' ','-')),str(int(regular)), str(n_days),str(i)])
            else:
                day_trip_id = '-'.join([str(state), str(city.upper().replace(' ','-')),str(int(regular)), str(n_days),str(i)])
            current_events, big_ix, small_ix, med_ix = [],[],[],[]
            for ix, label in enumerate(day_labels):
                if label == v:
                    time = county_list_info[ix,3]
                    event_ix = county_list_info[ix,0]
                    current_events.append(event_ix)
                    if time > 180 :
                        big_ix.append(ix)
                    elif time >= 120 :
                        med_ix.append(ix)
                    else:
                        small_ix.append(ix)
            # print big_ix, med_ix, small_ix
            big_ = sorted_events(county_list_info, big_ix)
            med_ = sorted_events(county_list_info, med_ix)
            small_ = sorted_events(county_list_info, small_ix)
            # if len(big_)+len(med_)+len(small_)==0:
            #     print "not more event for days " , day_trip_id
            #     # return [day_trip_id, "not more event for days " ]
            #     break 
            # print big_, med_, small_
            event_ids, event_type = create_event_id_list(big_, med_, small_)
            # print event_ids, event_type
            event_ids, event_type = db_event_cloest_distance(event_ids = event_ids, event_type = event_type, city_name = city)
            # event_ids, google_ids, name_list, driving_time_list, walking_time_list = \
            event_ids, driving_time_list, walking_time_list = db_google_driving_walking_time(event_ids, event_type)
            # print 'event_ids, google_ids, name_list', event_ids, google_ids, name_list
            # print 'driving and walking time list: ', driving_time_list, walking_time_list
            # event_ids, driving_time_list, walking_time_list, total_time_spent = db_remove_extra_events(event_ids, driving_time_list, walking_time_list)
            event_ids, driving_time_list, walking_time_list, total_time_spent, not_visited_poi_lst = \
                db_adjust_events(event_ids, driving_time_list, walking_time_list, not_visited_poi_lst, event_type, city)
            # db_address(event_ids)
            details = db_day_trip_details(event_ids, i)
            #insert to day_trip ....
            conn = psycopg2.connect(conn_str)
            cur = conn.cursor()
            cur.execute('select max(index) from day_trip_table;')
            max_index = cur.fetchone()[0]
            index = max_index+1

            #if exisitng day trip id..remove those...
            if check_day_trip_id(day_trip_id):
                cur.execute("SELECT index FROM day_trip_table WHERE trip_locations_id = '%s';" %(day_trip_id))
                index = cur.fetchone()[0]
                cur.execute("DELETE FROM day_trip_table WHERE trip_locations_id = '%s';" %(day_trip_id))
                conn.commit()

            cur.execute("insert into day_trip_table (index, trip_locations_id, full_day, regular, county, state, details, event_type, event_ids) VALUES ( %s, '%s', %s, %s, '%s', '%s', '%s', '%s', '%s');" %( index, day_trip_id, full_day, regular, county, state, str(details).replace("'", "''"), event_type, event_ids))
            conn.commit()
            conn.close()
            trip_location_ids.append(day_trip_id)
            full_trip_details.extend(details)

        # full_trip_id = '-'.join([str(state.upper()), str(county.upper().replace(' ','-')),str(int(regular)), str(n_days)])
        username_id = 1
        conn = psycopg2.connect(conn_str)
        cur = conn.cursor()
        cur.execute("select max(index) from full_trip_table;")
        full_trip_index = cur.fetchone()[0] + 1
        cur.execute("insert into full_trip_table(index, username_id, full_trip_id,trip_location_ids, regular, county, state, details, n_days) VALUES (%s, %s, '%s', '%s', %s, '%s', '%s', '%s', %s);" %(full_trip_index, username_id, full_trip_id, str(trip_location_ids).replace("'","''"), regular, county, state, str(full_trip_details).replace("'","''"), n_days))
        conn.commit()
        conn.close()
        print "finish update %s, %s into database" %(state, county)
    else:
        print "%s, %s already in database" %(state, county) 
        conn = psycopg2.connect(conn_str)
        cur = conn.cursor()
        cur.execute("select trip_location_ids, details from full_trip_table where full_trip_id = '%s';" %(full_trip_id)) 
        trip_location_ids, details = cur.fetchone()      
        conn.close()
        full_trip_details = ast.literal_eval(details)
        trip_location_ids = ast.literal_eval(trip_location_ids)
    from bs4 import BeautifulSoup as BS
    import requests
    from requests.utils import quote
    user_agent = 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_4; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.472.63 Safari/534.3'
    headers = { 'User-Agent' : user_agent }
    for index, detail in enumerate(full_trip_details):
        full_trip_details[index] = ast.literal_eval(detail)
        poi_name = full_trip_details[index]['name']
        # googleUrl = "https://www.google.com/search?tbm=isch&q=" + quote(poi_name, safe='')
        # response = requests.get(googleUrl, headers=headers)
        # soup = BS(response.text, 'html.parser')
        # img_url = soup.select("[data-src]")[1]['data-src']
        img_url = 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS1GF_GCEwlEYvzdAOPz9AxL-oSKsTpSWVYRHxjwV-Boidvtzuf'
        full_trip_details[index]['url'] = img_url
        full_trip_details[index]['address'] = full_trip_details[index]['address'].strip(', ').replace(', ,',',')
        print full_trip_details[index]['url']
    return full_trip_id, full_trip_details, trip_location_ids
