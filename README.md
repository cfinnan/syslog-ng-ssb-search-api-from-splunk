# syslog-ng-ssb-search-api-from-splunk
This is a Python script that implements a custom Splunk search command that enables users to perform
a search of log messages stored in a syslog-ng Store Box logspace directly from the Splunk search iterface.
The script employs the SSB's Rest API. It uses the /search/logspace/filter endpoint of the Rest API.
The filter command is the main command of the Search API. It retrieves log message records from SSB, the 
received records are filtered by time interval and search expression. The search is executed in Splunk using 
the following syntax:

| ssb logspace=center searchstring="jsmith AND host:myhost.mydomain.com" fromdate=01/01/2022 todate=08/24/2022 server=ssb

The required parameters are entered as key-value pairs and include:
1. logspace name to search
2. the search string, which uses the native search syntax of the SSB 
3.,4. the search interval (granularity of days) by entering the start and end dates
5. the hostname (or ip address) of the target SSB appliance on which the search will be performed

Only the values of the parameters are significant, the key part is arbitrary. For instance, the above search 
can be implemented as follows:

| ssb space=center mysearch=" cfinnan AND host:192.168.38.154" foo=01/01/2022 bar=08/24/2022 target=ssb

and identical results will be returned. The keys and values must be separated by "=".

This has to be associated with a Splunk custom app. You will have create the app in Splunk, and place the Python script in the app's bin
directory. In the app's local directory, you will need a file named commands.conf that points to your Python script in bin.
