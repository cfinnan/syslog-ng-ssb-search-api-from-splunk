import sys
import re
import requests
import ssl
import socket
import json
import csv
import urllib3
import splunk.Intersplunk
import time
import datetime
# This version uses the requests module but without using requests.Session()
# We have to handle the returned Authentication_token cookie ourselves for
# subsequent get() requests after login authentication done through the post
# request.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
if len(sys.argv) != 6:
    print("requires five arguments: first argument is the logspace name,\n \
    second argument is the search string, third argument is start date,\n,\
    fourth argument is the end date\n \
    fifth argurment is the address or hosthame of the target SSB")
    exit(1)
#logspace = sys.argv[1]
logspace = sys.argv[1].split("=")[1]
#searchstring = sys.argv[2]
searchstring = sys.argv[2].split("=")[1]
#print("searchstring = ", searchstring)
s_begin = sys.argv[3].split("=")[1]
s_end   = sys.argv[4].split("=")[1]
server = sys.argv[5].split("=")[1]
arg3chk = re.match("^\d{2}/\d{2}/\d{4}$", s_begin)
arg4chk = re.match("^\d{2}/\d{2}/\d{4}$", s_end)
if (arg3chk) == None or (arg4chk) == None:
    print("date format must be mm/dd/yyyy")
    exit(1)

# need to convert interval start to Unix Timestamp (i.e., seconds since Jan. 1, 1970)
from_time = int(time.mktime(datetime.datetime.strptime(s_begin, "%m/%d/%Y").timetuple()))
to_time = int(time.mktime(datetime.datetime.strptime(s_end, "%m/%d/%Y").timetuple()))
# make sure SSB returns the maximum number of results for each query
limit = 1000

# login to SSB
mysslcontext = ssl.create_default_context()
mysslcontext.keylog_filename = "/root/secrets.log"
credentials  = { 'username': 'ssbrest', 'password': 'Api$earch101'}
url = "https://"+server+"/api/4/login"
result = requests.post(url, credentials, verify=False)
json.data=json.loads(result.text)
error = json.data.get('error', {}).get('code')
message = json.data.get('error', {}).get('message')
if not error == None:
   print("response code =", error,"\nmessage =", message)
   exit(1)
token = json.data["result"]
header = {"Cookie": "AUTHENTICATION_TOKEN="+token}
#
#
# check that a valid, indexed logspace name has been specified
url = "https://"+server+"/api/4/search/logspace/list_logspaces"
r = requests.get(url,verify=False, headers=header)
json.data = json.loads(r.text)
logspace_list = json.data["result"]
if not logspace in logspace_list:
    print("invalid logspace name")
    exit(1)
# First get the number of messages that meet the search criteria
# SSB will only return a maximum of 1,000 results per query
# We will have to loop with multiple requests using the "offset" parameter.
url = "https://"+server+"/api/4/search/logspace/number_of_messages/%s?from=%d&to=%s&search_expression=%s&limit=%s" % (logspace, from_time, to_time, searchstring, limit)
r = requests.get(url, verify=False, headers=header)
json.data = json.loads(r.text)
json_output = json.dumps(json.data, indent=2)
number_of_msgs =json.data["result"]
number_of_offsets = number_of_msgs//1000 + 1
for n in range(number_of_offsets) :

#
##############################################################
    offset =  n
    #print(offset)
    url = "https://"+server+"/api/4/search/logspace/filter/%s?from=%d&to=%s&search_expression=%s&offset=%s&limit=%s" % (logspace, from_time, to_time, searchstring, offset,limit)
# generate query (http get)
    r = requests.get(url, verify=False, headers=header)

# convert api output json to python dict
    json.data = json.loads(r.text)
    number_msgs = len(json.data["result"])
    for x in json.data["result"]:
       timestamp = int(x["timestamp"]) 
       x["timestamp"] = str(datetime.datetime.fromtimestamp(timestamp))
#
       x.pop('delimiters')
       # mydata = [x]
#        mydata = json.dumps(x)
#splunk.Intersplunk.outputResults(mydata)
    splunk.Intersplunk.outputResults(json.data["result"])
