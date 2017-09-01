import boto3
import psycopg2
import helpers
import os
import json
current_path= os.getcwd()
with open(current_path + '/api_key_list.config') as key_file:
    api_key_list = json.load(key_file)
api_key = api_key_list["distance_api_key_list"]
conn_str = api_key_list["conn_str"]
client = boto3.client('ses')

def email(bodytext = 'No data...check your function arguments', toAddress= 'dayumikoda@gmail.com', subject='test subject', dftoconvert = None, replace=False):
    region = 'us-east-1'
    me = 'support@zoesh.com'
    destination = { 'ToAddresses' : [toAddress],
                    'CcAddresses' : [],
                    'BccAddresses' : []}
    try:
        bodyhtml = dftoconvert.to_html(float_format = lambda x: '({:15,.2f})'.format(abs(x)) if x < 0 else '+{:15,.2f}+'.format(abs(x)))
        # use no-break space instead of two spaces next to each other
        if replace:
            bodyhtml = bodyhtml.replace('  ', '&nbsp;')
        message = {'Subject' : {'Data' : subject},
                   'Body': {'Html' : {'Data' : bodyhtml}}}
    except: #If there is no data to convert to html
        message = {'Subject' : {'Data' : subject},
                   'Body': {'Text' : {'Data' : bodytext}}}
    result = client.send_email(Source = me, 
                               Destination = destination, 
                               Message = message)    
    return result if 'ErrorResponse' in result else ''

def compose_full_trip(full_trip_id):
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    cur.execute("SELECT trip_location_ids, city, state, details from full_trip_table_city where full_trip_id = '%s';" % (full_trip_id))
    trip_location_ids, city, state, details = cur.fetchone()
    conn.close()
    return json.loads(details), city, state

def send_email_full_trip(email_address,full_trip_id):
    details,city, state = compose_full_trip(full_trip_id)
    subject = "Your trip to %s, %s" %(city, state)
    email(str(details),email_address, subject)


