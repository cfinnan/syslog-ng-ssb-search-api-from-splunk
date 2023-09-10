#!/usr/bin/python3
import sys
import re
import json
import datetime
import urllib3
import requests
# This version uses the requests module but without using requests.Session()
# We have to handle the returned Authentication_token cookie ourselves for
# subsequent get() requests after login authentication done through the post
# request.
# run as follows from the directory in which you store the script:
#  ./api_test.py logspace=center search="<search terms>" start=2023-01-18T11:34:00 end=2023-08-30T09:36:00 server=<ssb hostname>
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
if len(sys.argv) != 6:
    print("requires five arguments: first argument is the logspace name,\n \
    second argument is the search string, third argument is start date/time,\n,\
    fourth argument is the end date/time\n \
    fifth argurment is the address or hosthame of the target SSB")
    exit(1)
logspace = sys.argv[1].split("=")[1]
searchstring = sys.argv[2].split("=")[1]
s_begin = sys.argv[3].split("=")[1]
s_end   = sys.argv[4].split("=")[1]
server = sys.argv[5].split("=")[1]
arg3chk = re.match("^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}$", s_begin)
arg4chk = re.match("^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}$", s_end)
if (arg3chk) is None or (arg4chk) is None:
    print("date format must be YYYY-MM-DDThh:mm:ss")
    exit(1)
#
# need to convert interval start and end to Unix Timestamp (i.e., seconds since Jan. 1, 1970)
from_time = datetime.datetime.strptime(s_begin,'%Y-%m-%dT%H:%M:%S')
from_time = int(from_time.timestamp())
to_time = datetime.datetime.strptime(s_end,'%Y-%m-%dT%H:%M:%S')
to_time = int(to_time.timestamp())
# make sure SSB returns the maximum number of results for each query
LIMIT = 1000

# login to SSB
credentials  = { 'username': '<username>', 'password': '<password>'}
url = "https://"+server+"/api/4/login"
result = requests.post(url, credentials, verify=False)
json.data=json.loads(result.text)
token = json.data["result"]
header = {"Cookie": "AUTHENTICATION_TOKEN="+token}

# First get the number of messages that meet the search criteria
# SSB will only return a maximum of 1,000 results per query
# We will have to loop with multiple requests using the "offset" parameter.

url = "https://"+server+"/api/4/search/logspace/number_of_messages/%s?from=%d&to=%s&search_expression=%s" % (logspace, from_time, to_time, searchstring)
r = requests.get(url, verify=False, headers=header)
json.data = json.loads(r.text)
number_of_msgs =json.data["result"]
number_of_offsets = number_of_msgs//LIMIT + 1

for n in range(number_of_offsets) :

#
##############################################################
    offset =  n * 1000
    #print(offset)
    url = "https://"+server+"/api/4/search/logspace/filter/%s?from=%d&to=%s&search_expression=%s&offset=%s&limit=%s" % (logspace, from_time, to_time, searchstring, offset,limit)
# generate query (http get)
    r = requests.get(url, verify=False, headers=header)
# convert api output json to python dict
    json.data = json.loads(r.text)
    if json.data["result"] is not None:
        for x in json.data["result"]:
           timestamp = int(x["timestamp"]) 
           x["timestamp"] = str(datetime.datetime.fromtimestamp(timestamp))
#
           x.pop('delimiters')
        print(*json.data["result"], sep="\n")
