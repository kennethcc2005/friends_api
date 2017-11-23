import boto3
import psycopg2
import ast
import numpy as np
import simplejson
import requests
import urllib
import json
import re
import os
from collections import Counter
from geopy.geocoders import Nominatim        
from boto3.session import Session
current_path= os.getcwd()
with open(current_path + '/api_key_list.config') as key_file:
    api_key_list = json.load(key_file)
api_key = api_key_list["distance_api_key_list"]
conn_str = api_key_list["conn_str"]
aws_key = api_key_list["aws_key"]
aws_secret = api_key_list["aws_secret"]

def get_city_state_address(data):
    '''
    Return City, State, Address.
    If city and state not in data, get from address if possible
    '''
    city = data['city'] if data['city'] else None
    state = data['state'] if data['state'] in data else None
    postal_code = None
    if data['address']:
        address = data['address']
        if (not city) and (Counter(address)[','] >= 2):
            add_lst = data['address'].split(',')
            state = add_lst[-1].strip().split(' ')[0]
            city = add_lst[-2].strip() 
            postal_code = add_lst[-1].strip().split(' ')[1]
    else:
        address = None
    return city, state, postal_code, address

def get_coords(data):
    '''
    Return POI coord_lat, coord_long.
    If coord_lat or coord_long not in data, get from address using geolocator
    '''
    coord_lat, coord_long =  None, None
    if (not data['coord_lat']) or (not data['coord_long']):
        if (data['address']):
            geolocator = Nominatim()
            location = geolocator.geocode(data['address'])
            if location == None:
                import googlemaps
                gmaps = googlemaps.Client(api_key[0])
                # Geocoding an address
                geocode_result = gmaps.geocode(data['address'])
                coord_lat, coord_long = geocode_result[0]['geometry']['location']['lat'], geocode_result[0]['geometry']['location']['lng']
            else:
                coord_lat, coord_long = location.latitude, location.longitude
    else:
        coord_lat, coord_long = data['coord_lat'], data['coord_long']
    return coord_lat, coord_long

def upload_and_get_img_url(data, city, season, name, state):
    '''
    Update to boto3 and use from there.....
    '''
    session = Session(aws_access_key_id= aws_key,
                    aws_secret_access_key= aws_secret,
                    region_name='us-east-1')
    s3 = session.resource("s3")
    bucket_name_to_upload_image_to = 'travel-with-friends'  
    internet_image_url = data['photo_src']  
    img_ext = internet_image_url.split('.')[-1]     
    if city != None:      
        s3_image_filename = 'season_poi_images/{0}/{1}/{2}/{3}.{4}'.format(state, city.replace(' ','_'), season, name.replace(' ','_'), img_ext)
    else:
        s3_image_filename = 'season_poi_images/{0}/{1}/{2}.{3}'.format(state, season, name.replace(' ','_'), img_ext)
    req_for_image = requests.get(internet_image_url, stream=True)
    file_object_from_req = req_for_image.raw
    req_data = file_object_from_req.read()

    # Do the actual upload to s3
    s3.Bucket(bucket_name_to_upload_image_to).put_object(Key=s3_image_filename, Body=req_data)
    object_acl = s3.ObjectAcl(bucket_name_to_upload_image_to,s3_image_filename)
    response = object_acl.put(ACL='public-read')
    print 'Done uploading image to S3 Bucket travel-with-friends'
    return 'https://s3.amazonaws.com/travel-with-friends/' + s3_image_filename

def new_poi_seasonal(data):
    '''%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    CREATE TABLE seasonal_poi(
    index bigint PRIMARY KEY,
    name VARCHAR (255) NOT NULL,
    address text,
    city VARCHAR (50),
    state VARCHAR (50),
    coord_lat double precision,
    coord_long double precision,
    photo_url text,
    description text,
    season VARCHAR (25),
    link text,
    visit_length double precision,
    rating double precision,
    num_reviews big int,
    fee boolean,
    additional_info text
    );
    '''
    # try:
    #read dict data and check it is in the psql or not
    
    season, name = data['season'], data['poi_name']
    rating = data['rating'] if data['rating'] else None
    desc = data['desc'] if data['desc'] else None
    link = data['link'] if data['link'] else None
    add_info = data['additional_info'] if  data['additional_info'] else None
    visit_length = data['visit_length'] if data['visit_length'] else None
    num_reviews = data['num_reviews'] if data['num_reviews'] else None
    fee = data['fee'] if data['fee'] else None
    
    #Check City and State field and fill from address if needed
    city, state, postal_code, address = get_city_state_address(data)
    #Check POI coordinates and fill from address if needed
    coord_lat, coord_long = get_coords(data)
    
    #Get Photo and Save to S3 and get address
    s3_image_filename = upload_and_get_img_url(data, city, season, name, state) if 'photo_src' in data else None
    #Update POI if id is exisit
    conn = psycopg2.connect(conn_str)            
    cur = conn.cursor()
    if data['poi_id']:
        cur.execute("SELECT index,name FROM seasonal_poi WHERE index  = %s LIMIT 1;", (data['poi_id']))  
        result = cur.fetchone()
        if result != None:
            (index, name) = result
            cur.execute('''UPDATE seasonal_poi 
                                SET (name, address, city, state, coord_lat, coord_long, photo_url, descrption, season, link, visit_length, num_reviews, rating,       fee, additional_info) = (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
                            WHERE index = %s;''', 
                        (name, address, city, state, coord_long, coord_lat, s3_image_filename, desc, season, link, visit_length, num_reviews, rating, fee, add_info, index))  
    else:
        cur.execute("SELECT max(index) FROM seasonal_poi;")
        result = cur.fetchone()[0]
        if result != None:
            new_index = result + 1
        else:
            new_index = 0
        print '''INSERT INTO seasonal_poi (index, name, address, city, state, coord_lat, coord_long, photo_url, descrption, season, link, visit_length,                         num_reviews, rating, fee, additional_info)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);'''%(new_index, name, address, city, state, coord_long, coord_lat, s3_image_filename, desc, season, link, int(visit_length), float(num_reviews), float(rating), fee, add_info)
        cur.execute('''INSERT INTO seasonal_poi (index, name, address, city, state, coord_lat, coord_long, photo_url, description, season, link, visit_length,                         num_reviews, rating, fee, additional_info)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);''', (new_index, name, address, city, state, coord_long, coord_lat, s3_image_filename, desc, season, link, int(visit_length), float(num_reviews), float(rating), fee, add_info))
        print('check now!zz', cur.query)
        
    conn.commit()
    conn.close()
    return True
    # except:
    #     print('some errors, need to investigate: ', data)
    #     return False
        
def udpate_poi_address(data):
    '''
    Update POI Address, return False if poi_id and poi_name not correct.
    '''
    conn = psycopg2.connect(conn_str)            
    cur = conn.cursor()
    #Check City and State field and fill from address if needed
    city, state, address, postal_code = get_city_state_address(data)
    #Check POI coordinates and fill from address if needed
    coord_lat, coord_long = get_coords(data)
    if ('poi_id' not in data) and ('poi_name' not in data):
        print('Update POI Error: Needs either poi id or name to update address!')   
        conn.close()                 
        return False
    #If poi id not included and poi name has have too many results. return false
    elif ('poi_id' not in data) and ('poi_name' in data):
        name = data['poi_name']
        cur.execute('''SELECT index, name 
                         FROM poi_detail_table 
                        WHERE name = %s;''', 
                    (name))  
        name_lst = cur.fetchall()
        if len(name_lst) != 1:
            print('Update POI Error: POI name has multiple results or no results!')  
            conn.close()                                  
            return False
        else:
            index = name_lst[0][0]
            #read dict data and check it is in the psql or not
            cur.execute('''UPDATE poi_detail_table 
                              SET (address, city, state, coord_lat, coord_long, postal_code) = (%s, %s, %s, %s, %s, %s) 
                            WHERE index = %s and name = %s;''',
                        (address, city, state, coord_lat, coord_long, postal_code, index, name))  
            conn.commit()
    elif ('poi_id' in data) and ('poi_name' in data):
        index = data['poi_id']
        name = data['poi_name']
        cur.execute('''SELECT index, name 
                         FROM poi_detail_table 
                        WHERE index = %s 
                          AND name = %s;''', 
                    (index, name))  
        result = cur.fetchone()
        if result != None:
            cur.execute('''UPDATE poi_detail_table 
                              SET (address, city, state, coord_lat, coord_long, postal_code) = (%s, %s, %s, %s, %s, %s) 
                            WHERE index = %s and name = %s;''',
                        (address, city, state, coord_lat, coord_long, postal_code, index, name))  
            conn.commit()
        else:
            print('Update POI Error: POI ID and name not match each other!') 
            conn.close()                       
            return False
    else:
        index = data['poi_id']
        cur.execute('''SELECT index, name 
                         FROM poi_detail_table 
                        WHERE index = %s;''', 
                    (index))  
        result = cur.fetchone()
        if result != None:
            cur.execute('''UPDATE poi_detail_table 
                              SET (address, city, state, coord_lat, coord_long, postal_code) = (%s, %s, %s, %s, %s, %s) 
                            WHERE index = %s;''',
                        (address, city, state, coord_lat, coord_long, postal_code, index))  
            conn.commit()
        else:
            print('Update POI Error: POI ID not exist!')
            conn.close()            
            return False
    conn.close()
    return True
        
def new_poi_detail(data):
    '''
    Add new POI detail, return False if information not enough.
    '''
    try:
        conn = psycopg2.connect(conn_str)            
        cur = conn.cursor()
        #Check City and State field and fill from address if needed
        city, state, address, postal_code = get_city_state_address(data)
        #Check POI coordinates and fill from address if needed
        coord_lat, coord_long = get_coords(data)
        photo_url = upload_and_get_img_url(data) if 'photo_src' in data else None
        #If poi id not included and poi name has have too many results. return false
        name = data['poi_name']
        cur.execute('''SELECT index, name 
                            FROM poi_detail_table 
                        WHERE name = %s 
                            AND city = %s
                            AND state = %s;''', 
                    (name, city, state))  
        resuslt = cur.fetchone()
        if result != None:
            print('Update POI Error: POI name, city, address already exisit!', name, city, state)  
            conn.close()                                  
            return False
        else:
            cur.execute('''SELECT max(index)
                            FROM poi_detail_table;''')
            result = cur.fetchone()
            index = result[0] + 1 if result != None else 0  
            null = None
            #read dict data and check it is in the psql or not
            cur.execute('''INSERT INTO poi_detail_table (index, address, adjusted_visit_length, city, coord_lat, coord_long, country,                                                     county, description, fee, name, num_reviews, poi_type, postal_code, ranking, review_score, state, state_abb, street_address, tag,                       url, icon_url, check_full_address, img_url, interesting)
                           VALUES (%i, %s, %s, %s, %s, %s, %s,  %s, %s, %s, %s, %s, %s, %s, %s);''', 
                        (index, address, data['visit_length'], city, coord_lat, coord_long, 'United States', null, data['desc'], data['fee'], data['name'], data['num_reviews'], data['poi_type'], postal_code, null, data['rating'], null, state, null, null, data['link'], photo_url, 1, photo_url, True))
            conn.commit()
        conn.close()
        return True
    except:
        print('data not completed! error!', data)
        return False