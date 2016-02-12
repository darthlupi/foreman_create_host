#!/usr/bin/python

import getopt
import sys
import math
from mst_simple_foreman import simple_foreman

def main():
    # URL to your Foremsn host
    url = "https://foremanhost.com"
    # Default credentials to login to Satellite 6
    username = "user"
    password = "password"
    #Set the ORG
    org = "THEORG"
    #Set variables for options 
    hostgroup = '' 

    #Text for input errors and help
    input_help =  """Script requires the following format:"""
    #Attempt to pull in options
    try:
        options, remainder = getopt.getopt(sys.argv[1:], 'o:v', ['hostgroup='] )
    except getopt.GetoptError, e:
        print "Error!  Error! " + str(e)
        print input_help
        sys.exit()

    for opt, arg in options:
        if opt in '--hostgroup':
            hostgroup = arg
    #Setup api object
    sf = simple_foreman( username,password,org,url)
    #Retrieve partition tables based on hostgroup
    disk_sizes = sf.get_disk_size(hostgroup)
    print disk_sizes["sda"]
    
    for d in disk_sizes:
        print int( math.ceil(float(disk_sizes[d])/1024) )
    
if __name__ == "__main__":
    main()
