#!/usr/bin/python3
"""Module to test SSB REST-API Search from command line"""

import re
import json
import datetime
import os
import argparse
import urllib3
import requests

# This version uses the requests module but without using requests.Session()
# We have to handle the returned Authentication_token cookie ourselves for
# subsequent get() requests after login authentication done through the post
# request.

# Global parser for access by functions
parser = argparse.ArgumentParser(prog="api_test.py", \
    description='This utility performs searches against a Syslog-ng Store Box')

parser.add_argument('--logspace', help='Logspace to search', \
    default=os.environ.get('LOGSPACE'))
parser.add_argument('--search_expression', help='Search expression to be used against logspace', \
    default=os.environ.get('SEARCH_EXPRESSION'))
parser.add_argument('--from_time', help='Time to start search from in YYYY-MM-DDThh:mm:ss format', \
    default=os.environ.get('FROM_TIME'))
parser.add_argument('--to_time', help='Time to end searching from in YYYY-MM-DDThh:mm:ss format', \
    default=os.environ.get('TO_TIME'))
parser.add_argument('--ssb_host', help='SSB FQDN or IP Address', \
    default=os.environ.get('SSB_HOST'))
parser.add_argument('--ssb_username', help='Username to authenticate against SSB with', \
    default=os.environ.get('SSB_USERNAME'))
parser.add_argument('--ssb_password', help='Password for SSB authentication', \
    default=os.environ.get('SSB_PASSWORD'))
parser.add_argument('--verify', help='Require verified SSL certificates', \
    default=os.environ.get('VERIFY'), action="store_true")

# Parse cli options and environment variables
args = parser.parse_args()

# Ensure minimal parameters are provided
if args.ssb_host is None or args.ssb_username is None or args.ssb_password is None:
    parser.print_help()
    exit(1)

# Disable certificate validation unless verification is configured
VERIFY=True
if args.verify is None:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    VERIFY=False

# Validate from_time
if args.from_time is None or \
    re.match("^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}$", args.from_time) is None:
    print(f'No or invalid from_time specified ({args.from_time}), defaulting to 1 hour ago')
    timestamp = datetime.datetime.now() - datetime.timedelta(hours=1)
    args.from_time = datetime.datetime.strftime(timestamp, "%Y-%m-%dT%H:%M:%S")

# Validate to_time
if args.to_time is None or \
    re.match("^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}$", args.to_time) is None:
    print(f'No or invalid to_time specified ({args.to_time}), defaulting to now')
    args.to_time = datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%dT%H:%M:%S")

# Convert start and end times to Unix Timestamp (i.e., seconds since Jan. 1, 1970)
try:
    from_time = datetime.datetime.strptime(args.from_time,'%Y-%m-%dT%H:%M:%S')
    from_time = str(int(from_time.timestamp()))
except Exception as ex:
    print("Failed to convert {args.from_time} to Unix timestamp: {ex}")
    exit(1)

try:
    to_time = datetime.datetime.strptime(args.to_time,'%Y-%m-%dT%H:%M:%S')
    to_time = str(int(to_time.timestamp()))
except Exception as ex:
    print("Failed to convert {args.from_time} to Unix timestamp: {ex}")
    exit(1)

# make sure SSB returns the maximum number of results for each query
LIMIT = 1000

# login to SSB
credentials  = { 'username': args.ssb_username, 'password': args.ssb_password}
url = "https://"+args.ssb_host+"/api/4/login"
try:
    result = requests.post(url, verify=VERIFY, data=credentials, timeout=10)
except requests.exceptions.ReadTimeout:
    print("Timeout raised logging into SSB")
    exit(1)
except requests.exceptions.ConnectTimeout:
    #raise requests.exceptions.ConnectionError
    print("Can't connect to SSB")
    exit(1)
try:
    json.data=json.loads(result.text)
    token = json.data["result"]
except Exception as ex:
    print("Error decoding response %s : %s" % (result.text, ex))
    exit(1)
if not token:
    print("Authentication failure : %s" % result.text)
    exit(1)
header = {"Cookie": "AUTHENTICATION_TOKEN="+token}

# First get the number of messages that meet the search criteria
# SSB will only return a maximum of 1,000 results per query
# We will have to loop with multiple requests using the "offset" parameter.

url = "https://"+args.ssb_host+"/api/4/search/logspace/number_of_messages/"+ \
    args.logspace+"?from="+from_time+"&to="+to_time+"&search_expression="+args.search_expression
r = requests.get(url, verify=VERIFY, headers=header, timeout=10)
json.data = json.loads(r.text)
number_of_msgs =json.data["result"]
number_of_offsets = number_of_msgs//LIMIT + 1

for n in range(number_of_offsets) :

    offset =  n * LIMIT

    url = "https://"+args.ssb_host+"/api/4/search/logspace/filter/"+ \
        args.logspace+"?from="+from_time+"&to="+to_time+"&search_expression="+ \
        args.search_expression+"&offset="+str(offset)+"&limit="+str(LIMIT)

    # generate query (http get)
    r = requests.get(url, verify=VERIFY, headers=header, timeout=10)

    # convert api output json to python dict
    json.data = json.loads(r.text)
    if json.data["result"] is not None:
        for x in json.data["result"]:
            timestamp = int(x["timestamp"])
            x["timestamp"] = str(datetime.datetime.fromtimestamp(timestamp))
            x.pop('delimiters')
        print(*json.data["result"], sep="\n")
