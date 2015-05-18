# -*- coding: utf-8 -*-
"""
Created on Tue Dec 02 14:26:23 2014

@author: chomnoue

utility methods used to audit the map
"""


import xml.etree.ElementTree as ET
import pprint
from collections import defaultdict
from bs4 import BeautifulSoup

filename='example.osm'
map_features_file='Map_Features.htm'
MAIN_TAGS={'node','way','relation'}
def count_tag_keys(filename):
    """
    count the number of occurences of each tag key in the map
    """
    keys=defaultdict(int)
    for event,elem in ET.iterparse(filename,events=('start',)):
        if elem.tag=='tag':
            keys[elem.attrib['k']]+=1        
    return keys

def find_distinct_tag_values(filename,key):
    """
    return the disting values occuring for a particular key in the map
    """
    values=set()
    for event,elem in ET.iterparse(filename,events=('start',)):
        if elem.tag=='tag':
            if elem.attrib['k']==key:
                values.add(elem.attrib['v'].strip())
    return values

def extract_Features(filename):
    """
    extract features desribed in the openstreetmap wiki page at wiki.openstreetmap.org/wiki/Map_features
    and return a dictionnary matching each feature to a set of expected values
    """
    with open(filename, "r") as html:
        soup=BeautifulSoup(html)
        features=defaultdict(set)
        for table in soup.find_all('table',class_='wikitable'):
            for tr in table.find_all('tr'):
                tds=tr.find_all('td')
                if len(tds)>1:
                    key=tds[0].text.strip()
                    #managing <br>
                    value=tds[1].get_text("|", strip=True).split("|")
                    #managing '/'
                    value={definitive.strip() for val in value for definitive in val.split('/') }
                    features[key]|=(value)
        return features



def find_tags_containing_the_same_key_more_than_once(filename):
    """
    try to see if there are duplicated keys in some tags
    """
    elems=set()
    for event,elem in ET.iterparse(filename,events=('start',)):
            if elem.tag in MAIN_TAGS:
                keys=set()
                for tag in elem.findall('tag'):
                    key=tag.attrib['k']
                    if key in keys:
                        elems.add(elem)
                        break
                    keys.add(key)
    return elems      
    
def find_tags_containing_key(key,filename):
    """
    used to visualise the enclosing tags containing a key
    """
    elems=[]
    enclosing=None
    for event,elem in ET.iterparse(filename,events=('start',)):
        if elem.tag=='tag':
                if elem.attrib['k']==key:
                    elems.append(enclosing)
        elif elem.tag in MAIN_TAGS: enclosing=elem
    #print len(elems)
    return elems

def find_tags_in_elements(key,elems_list,value=None):
    """
    used to extract tags containing a particular key from a provided set of tags
    """
    elems=set()
    for elem in elems_list:
        for tag in elem.findall('tag'):
            if tag.attrib['k']==key and (not value or tag.attrib['v']==value):
                elems.add(elem)
    return elems

def find_unexpected_values(filename,features):
    """
    validate the value of the tags in our file against those in the documentation
    """
    user_defined= {'user defined'.upper(),'URL','NUMBER','TEXT'}
    defined={key for key in features.keys() if all([val.upper() not in user_defined for val in features[key]])}
    unexpected=defaultdict(set)
    for event,elem in ET.iterparse(filename,events=('start',)):
        if elem.tag=='tag':
            key=elem.attrib['k']
            if key in defined:
                value=elem.attrib['v']
                if value not in features[key]:
                    unexpected[key].add(value)
    return unexpected
    
    
def print_elems(elems):
    for elem in elems:
        ET.dump(elem)

def main():    
    keys = count_tag_keys(filename)
    pprint.pprint(keys)

def unexpected_Features(tag_keys,features):
    return set(tag_keys.keys())-set(features.keys())
    

    

    

    
    

#if __name__ == "__main__":
    #main()