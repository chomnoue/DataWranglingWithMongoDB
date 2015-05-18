# -*- coding: utf-8 -*-
"""
Created on Fri Dec 05 15:34:27 2014

@author: chomnoue
"""

#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET
import pprint
import re
import codecs
import json
from pymongo import MongoClient
"""
Your task is to wrangle the data and transform the shape of the data
into the model we mentioned earlier. The output should be a list of dictionaries
that look like this:

{
"id": "2406124091",
"type: "node",
"visible":"true",
"created": {
          "version":"2",
          "changeset":"17206049",
          "timestamp":"2013-08-03T16:43:42Z",
          "user":"linuxUser16",
          "uid":"1219059"
        },
"pos": [41.9757030, -87.6921867],
"address": {
          "housenumber": "5157",
          "postcode": "60625",
          "street": "North Lincoln Ave"
        },
"amenity": "restaurant",
"cuisine": "mexican",
"name": "La Cabana De Don Luis",
"phone": "1 (773)-271-5176"
}

You have to complete the function 'shape_element'.
We have provided a function that will parse the map file, and call the function with the element
as an argument. You should return a dictionary, containing the shaped data for that element.
We have also provided a way to save the data in a file, so that you could use
mongoimport later on to import the shaped data into MongoDB. You could also do some cleaning
before doing that, like in the previous exercise, but for this exercise you just have to
shape the structure.

In particular the following things should be done:
- you should process only 2 types of top level tags: "node" and "way"
- all attributes of "node" and "way" should be turned into regular key/value pairs, except:
    - attributes in the CREATED array should be added under a key "created"
    - attributes for latitude and longitude should be added to a "pos" array,
      for use in geospacial indexing. Make sure the values inside "pos" array are floats
      and not strings. 
- if second level tag "k" value contains problematic characters, it should be ignored
- if second level tag "k" value starts with "addr:", it should be added to a dictionary "address"
- if second level tag "k" value does not start with "addr:", but contains ":", you can process it
  same as any other tag.
- if there is a second ":" that separates the type/direction of a street,
  the tag should be ignored, for example:

<tag k="addr:housenumber" v="5158"/>
<tag k="addr:street" v="North Lincoln Avenue"/>
<tag k="addr:street:name" v="Lincoln"/>
<tag k="addr:street:prefix" v="North"/>
<tag k="addr:street:type" v="Avenue"/>
<tag k="amenity" v="pharmacy"/>

  should be turned into:

{...
"address": {
    "housenumber": 5158,
    "street": "North Lincoln Avenue"
}
"amenity": "pharmacy",
...
}

- for "way" specifically:

  <nd ref="305896090"/>
  <nd ref="1719825889"/>

should be turned into
"node_ref": ["305896090", "1719825889"]
"""


lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
#patterns used describe street names
street_name=re.compile(r'^(Avenue|Rue|Boulevard).*$',re.IGNORECASE)
street_name_followed_by_number=re.compile(r'^((Avenue|Rue|Boulevard)[^\(]*)\(\s*N\xb0\s*([^\)]*)\)$',re.IGNORECASE)
street_number_only=re.compile(r'^(Avenue|Rue|Boulevard)\s*(\d\.\d+)$',re.IGNORECASE)
street_number_followed_by_allias=re.compile(r'^((Avenue|Rue|Boulevard)\s*(\d\.\d+))\s*\((Alias)*\s*([^\)]*)\)$',re.IGNORECASE)
street_name_followed_by_allias=re.compile(r'^((Avenue|Rue|Boulevard)\s*([^\(]*))\((Alias)*\s*([^\)]*)\)$',re.IGNORECASE)

client = MongoClient()
db = client.test_database


CREATED = [ "version", "changeset", "timestamp", "user", "uid"]


def shape_element(element):
    from collections import defaultdict
    elem=element
    node = defaultdict(dict)
    if element.tag == "node" or element.tag == "way" or element.tag == "relation" :
        # YOUR CODE HERE
        node['type']=elem.tag
        for key in elem.attrib.keys():
            value=elem.attrib[key]
            if key in CREATED:
                node['created'][key]=value
            else:
                node[key]=value
        if 'lat' in node:
            lat=float(node['lat'])
            lon=float(node['lon'])
            node['pos']=[lat,lon]
            del(node['lat'])
            del(node['lon'])
        for tag in elem.iter('tag'):
            key=tag.attrib['k']
            value=tag.attrib['v'].strip()
            if key.startswith("addr:street:") or problemchars.search(key):
                continue
            addr="addr:"
            if key.startswith(addr):
                key=key[len(addr):]
                node['address'][key]=value
            elif key=='name':                
                if not street_name.match(value):
                    node['name']=value
                else:
                    #extratc number and alias from street names
                    name,number,allias=get_name_number_and_allias(value)
                    node['name']=name.strip()
                    if number:node['street_number']=number.strip()
                    if allias:node['street_allias']=allias.strip()
            else:node[key]=value
        if element.tag == "way":
            node["node_refs"]=[]
            for nd in elem.iter('nd'):
                node["node_refs"].append(nd.attrib['ref'])
        if element.tag == "relation":
            node["member_refs"]=[]
            for member in elem.iter('member'):
                node["member_refs"].append(member.attrib)
        return dict(node)
    else:
        return None


def process_map(file_in, pretty = False):
    # You do not need to change this file
    file_out = "{0}.json".format(file_in)
    data = []
    with codecs.open(file_out, "w") as fo:
        for _, element in ET.iterparse(file_in):
            el = shape_element(element)
            if el:
                data.append(el)
                if pretty:
                    fo.write(json.dumps(el, indent=2)+"\n")
                else:
                    fo.write(json.dumps(el) + "\n")
    return data

def process_and_insert_in_db(filename,db):
    for _, element in ET.iterparse(filename):
        el = shape_element(element)
        if el:
            db.nodes.insert(el)
    
def get_name_number_and_allias(name):
    """
    extract number and allias from street names
    """
    match=street_name_followed_by_number.match(name)
    if match:
        return match.group(1),match.group(3),None
    match=street_number_only.match(name)
    if match:
        return match.group(0),match.group(2),None
    match=street_number_followed_by_allias.match(name)
    if match:
        return match.group(1),match.group(3),match.group(5)
    match=street_name_followed_by_allias.match(name)
    if match:
        return match.group(1),None,match.group(5)
    return name,None,None
    
def process():
    filename='example.osm'
    process_and_insert_in_db(filename,db)
    
    

