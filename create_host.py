#!/usr/bin/python

import getopt
import sys
from mst_simple_foreman import simple_foreman

def main():
    # URL to your Foreman server
    url = "https://foremanhost.com"
    # Default credentials to login to Foreman server
    username = "user"
    password = "password"
    # Name of the organization to be either created or used
    org = "THEORG"
    #Set up all of the variables to create a host
    hostname = ''
    ip = ''
    ip2 = ''
    loc = '' 
    hostgroup = '' 
    compute_profile = '' 
    compute_resource = '' 
    cluster = ''
    power = ''
    cpu = ''
    memory_mb = ''
    hd0_size = ''
    hd0_ds = ''
    hd1_size = ''
    hd1_ds = ''
    network_label = ''
    network_label2 = ''
    app = ''
    fob = ''
    sysowner = ''
    env = ''

    #Text for input errors and help
    input_help =  """Script requires the following format:
        ./mst_create_host.py  \\ 
        --hostname lindev18 \\
        --ip 11.48.191.18 \\ #Optional - set for static IP
        --hostgroup 'MST Base' \\ 
        --compute_profile 2-Medium \\ 
        --compute_resource JC-Midrange"""
    #Attempt to pull in options
    try:
        options, remainder = getopt.getopt(sys.argv[1:], 'o:v', ['hostname=',
                                                                 'ip=',
                                                                 'ip2=',
                                                                 'loc=',
                                                                 'hostgroup=',
                                                                 'compute_profile=',
                                                                 'compute_resource=',
                                                                 'cluster=',
                                                                 'cpu=',
                                                                 'memory_mb=',
                                                                 'hd0_size=',
                                                                 'hd0_ds=',
                                                                 'hd1_size=',
                                                                 'hd1_ds=',
                                                                 'power=',
                                                                 'network_label=',
                                                                 'network_label2=',
                                                                 'app=',
                                                                 'fob=',
                                                                 'sysowner=',
                                                                 'env='
                                                                 ])
    except getopt.GetoptError, e:
        print "Error!  Error! " + str(e)
        print input_help
        sys.exit()

    for opt, arg in options:
        if opt in ('--hostname'):
            hostname = arg
        elif opt in ('--ip'):
            ip = arg
        elif opt in ('--ip2'):
            ip2 = arg
        elif opt in '--loc':
            loc = arg
        elif opt in '--hostgroup':
            hostgroup = arg
        elif opt in ('--compute_profile'):
            compute_profile = arg
        elif opt in '--compute_resource':
            compute_resource = arg
        elif opt in '--cluster':
            cluster = arg
        elif opt in '--cpu':
            cpu = arg
        elif opt in '--memory_mb':
            memory_mb = arg
        elif opt in '--hd0_size':
            hd0_size = arg
        elif opt in '--hd0_ds':
            hd0_ds = arg
        elif opt in '--hd1_size':
            hd1_size = arg
        elif opt in '--hd1_ds':
            hd1_ds = arg
        elif opt in '--power':
            power = arg
        elif opt in '--network_label':
            network_label = arg
        elif opt in '--network_label2':
            network_label2 = arg
        elif opt in '--app':
            app = arg
        elif opt in '--fob':
            fob = arg
        elif opt in '--sysowner':
            sysowner = arg
        elif opt in '--env':
            env = arg





    """Setup api object"""
    sf = simple_foreman( username,password,org,url)
    """Run method to create the host"""
    new_host = sf.add_host(hostname,ip,ip2,org,loc,hostgroup,compute_profile,compute_resource,cluster,cpu,memory_mb,hd0_size,hd0_ds,hd1_size,hd1_ds,power,network_label,network_label2)
    print new_host
    if 'error' in new_host.keys():
       print "ERROR Build failed!"
       print  new_host["error"]["message"]
    else:
       print "Build complete for host " + new_host["name"] + "."

if __name__ == "__main__":
    main()
