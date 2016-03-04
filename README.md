# Data Wrangling with MongoDB 
## Description
A set of python scripts used to wrangle OpenstreetMaps data related to the city of Douala in Cameroon and store it in a MongoDB data base.  
This project is part of the [Udacity's Data Analyst Nanodegree curriculum](https://www.udacity.com/nanodegrees-new-s/nd002).  
## Usage
You can run any python file individually to wrangle your data:
* Use mapparser.py to identify the the different tags from the file.
* Use tags.py to make sure that every tag is a valid MongoDB key.
* Use audit.py to map abbreviations and street names with typos to standard street names.
* Use data.py to transform the data into MongoDB documents.
* Use users.py to find out the dinstincts contributors to the map.