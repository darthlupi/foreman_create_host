#!/usr/bin/python
import math
import json
import sys
import ipaddress

try:
    import requests
    requests.packages.urllib3.disable_warnings()
except ImportError:
    print "Please install the python-requests module."
    sys.exit(-1)

class simple_foreman:
    def __init__(self,username,password,org,url):
        self.username = username
        self.password = password
        self.org = org
        self.url = url
        self.foreman_api = "%s/api/v2/" % url
        self.ssl_verify = False
		
    def get_json(self,api_loc):
        try:
            #Performs a GET using the passed URL api_loc
            r = requests.get(api_loc, auth=(self.username, self.password), verify=self.ssl_verify)
        except Exception, e:
            print repr(e)
            sys.exit()
        return r.json()
	
    def post_json(self,api_loc, json_data):
        try:
            #Performs a POST and passes the data to the URL api_loc
            post_headers = {'content-type': 'application/json'}
            result = requests.post(
                api_loc,
                data=json_data,
                auth=(self.username, self.password),
                verify=self.ssl_verify,
                headers=post_headers)
        except Exception, e:
            print repr(e)
            sys.exit()
        return result.json()
	
    def put_json(self,api_loc, json_data):
        try:
            #Performs a POST and passes the data to the URL api_loc
            post_headers = {'content-type': 'application/json'}
            result = requests.put(
                api_loc,
                data=json_data,
                auth=(self.username, self.password),
                verify=self.ssl_verify,
                headers=post_headers)
        except Exception, e:
            print repr(e)
            sys.exit()
        return result.json()
		
    def get_id(self,match_value,api_function):
        #Returns id for mathcing name based on api_function
        return_id = False #Resulting id for search
        #Get json formated data
        data = self.get_json(self.foreman_api + api_function  ) 
        """If you are debugging it might be a good idea to print the
        the contents of the full json formated data returned."""
        #print data 
        #Loop through the results search for the id matching on name provided
        for dict in data['results']:        
            if match_value == dict['name']:
                return_id = dict['id'] 
        #Return the resulting id if one is set
        if return_id:
            return return_id
        else:
            print api_function.upper() + " with a value of '" + match_value + "' was not found."
            sys.exit(-1) 

    def get_compute(self,id):
        #Get json formated data
        api_function = "compute_profiles/"
        data = self.get_json(self.foreman_api + api_function + id  )
        #Return the compute attributes for the compute profile specified
        return data['compute_attributes'][0]['vm_attrs']
    
    def get_data(self,function,id):
        #Get json formated data
        api_function = function 
        data = self.get_json(self.foreman_api + api_function + id  )
        #Return the compute attributes for the compute profile specified
        return data

    def update_host(self,id,ip):
        #Simple method to update a host - currently just the IP Address...
        new_host_data = {'id': id, 'ip': ip }
        dump = json.dumps(new_host_data)
        print dump 
        new_host = self.put_json(self.foreman_api + "hosts/" + str(id) ,json.dumps(new_host_data) )
        print new_host


    def add_interface(self,id,ip,subnet_id,name):
        #WARNING THIS IS BROKEN UNTILE WE CAN GET A VALID MAC ADDRESS!!!!!
        #This is also pretty useless as kickstart does not generate the secondary interface.
        #I will perhaps need to get clever with kickstart and modify the eth1 if I find it.
        #We'll have to wait and see.
        #Perhaps create a new fact about the server?
        #Simple method to update a host - currently just the IP Address...
        new_interface_data = {'interface' : {} }
        new_interface_data['interface']['ip'] = ip
        new_interface_data['interface']['type'] = 'interface' 
        new_interface_data['interface']['subnet_id'] = subnet_id
        new_interface_data['interface']['name'] = name 
        #BROKEN AND DANDEROUS!!!!!!
        new_interface_data['interface']['mac'] = "AA:AA:AA:AA:AA:AA" 
        dump = json.dumps(new_interface_data)
        print dump
        new_interface = self.post_json(self.foreman_api + "hosts/" + str(id) + "/interfaces" ,json.dumps(new_interface_data) )
        print new_interface
        if 'error' in new_interface.keys():
          print "ERROR additional interface not configured!"
          print  new_interface["error"]["message"]

    def add_host_fact(self,name,fact,value):
      fact_data = { 'name' : name, 'facts' : { fact : value } }   
      dump = json.dumps(fact_data)
      print dump
      new_fact = self.post_json(self.foreman_api + "hosts/" +  "/facts" ,json.dumps(fact_data) )
      print new_fact

    def get_subnet(self,ip):
        #Return the subnet name ( should be the VMnetwork name )
        #that the IP Address provided belongs to.
        data = self.get_data("subnets","")
        for subnet in data["results"]:
          try:
            #Convert ip string to IP Address 
            addr4 = ipaddress.ip_address( unicode(ip) )
            #Check to see if the IP Address exists in the subnet
            network = unicode(subnet['network_address'])
            if addr4 in ipaddress.ip_network(network):
              return subnet
          except Exception, e:
            print repr(e)
            print "WARNING: Validate all subnets are configured properly in Foreman."
            print "Make sure they have the proper network address as this is required."
            print "Continuing to search through subnets for IP's Network..."

    def get_disk_size(self,hostgroup):
        hostgroup_id = self.get_id(hostgroup,"hostgroups")
        #Pull back the dictionary for the hostgroup
        hostgroup_data = self.get_data("hostgroups/",str(hostgroup_id))
        #Get the partition table 
        ptable_id =  hostgroup_data["ptable_id"]
        ptable_data = self.get_data("ptables/",str(ptable_id))
        #Parse the partition table
        rows = ptable_data["layout"].split("\n")
        #Dictionary that will contain the physical disks and their sizes - disk: size 
        disks = {} 
        #Dictionary for VG sizes ( total of LVs ) - vg: size
        vgs = {}
        #VG to PV mapping - vg: pv 
        vg_pv = {}        
        #Map PV to Disk - pv: disk 
        pv_d = {}
        #Loop through the partition table
	for row in rows:
            #print row
            cells = row.split()
            if len(cells):
            #Map the VG to the PV
                if cells[0] == "volgroup":
                    vg_pv[cells[1]] = cells[2]
            #Total Logical Volumes and populate dictionary for Volume Groups
                if cells[0] == "logvol":
                    #Gather VG Name and size of LV
                    for cell in cells:
                        if "--vgname=" in cell:
                            #not sure why but I need to strip the = separately
                            vg = cell.lstrip("--vgname")
                            vg = vg.lstrip("=")
                        if "--size=" in cell:
                            lv_size = int( cell.lstrip("--size=") )
                    #Update or set the vgs dictionary with vg name and size
                    if vg in vgs: #Set 
                        vgs[vg] += lv_size
                    else: #Update
                        vgs[vg] = lv_size
            #Populate the dictionary for the disk devices
            if any("--ondisk=" in c for c in cells):
                #Map PVs to Disk Devices
                if "--fstype" not in cells: #Is disk and no FS = pv partition
                   for cell in cells:
                       if "--ondisk=" in cell:
                          disk = cell.lstrip("--ondisk")
                          disk = disk.lstrip('=')
                          pv_d[cells[1] ] = disk 
                #Get initial disk sizes
                for cell in cells:
                   if "--size=" in cell:    
                       #Get the size of the partition
                       psize = int( cell.lstrip("--size=") )
                   if "--ondisk=" in cell:
                       #not sure why but I need to strip the = separately
                       disk = cell.lstrip("--ondisk")
                       disk = disk.lstrip('=')
                       #Update or set the disk size
                       if disk in disks: #Update
                           disks[disk] += psize
                       else: #Set
                           disks[disk] = psize 
        #Roll the volume group size up to the disk devices by matching the VG to the PV                
        #Add it up son
        for vg,pv in vg_pv.iteritems():
            #If the PV exists in the PV per disk dictionary,
            #retrieve the REAL disk the VG is attached to. 
	    if pv in pv_d:
                vg_d = pv_d[pv]
            #Add the total size of LVs of the VG to the proper disk
            disks[vg_d] += vgs[vg]
        #Return disks dict sorted as a paranoid check
        sorted_disks = {}
        for key in sorted(disks.iterkeys() ):
            sorted_disks[key] = disks[key]
        return sorted_disks
 

    def add_host(self,name,ip,ip2,org,loc,hostgroup,compute_profile,compute_resource,cluster,cpu,memory_mb,hd0_size,hd0_ds,hd1_size,hd1_ds,power,network_label,network_label2):
        #Gather the numeric ids that represent the parameters requested to configure the server.
        loc_id = self.get_id(loc,"locations")
        hostgroup_id = self.get_id(hostgroup,"hostgroups")
        #Pull back the dictionary for the hostgroup
        hostgroup_data = self.get_data("hostgroups/",str(hostgroup_id))
        #Get the default compute profile id for the hostgroup if one is set 
        #If this is set, then the system is virtual
        compute_profile_id =  hostgroup_data["compute_profile_id"]
        new_host_data = {} 
        new_host = {}
        new_host_dump = {}
        #Setup the dictionary we are using to configure our new host 
        new_host_data = {'host':{
          'managed': True,
          'provision_method': 'build',
          'build': True,
          'name': name,
          'enabled': True,
          'hostgroup_id': hostgroup_id,
          'location_id': loc_id,
        }}

        #Get the subnet based on the IP address requested 
        subnet_data = self.get_subnet(ip)            
        if subnet_data:
          print "Assigning subnet: " + subnet_data['name'] + " to IP address: "  + ip
        else:
          print "No matching subnet was found for IP Address " + ip
          print "Cannot continue build.  Validate subnet for IP provided exists in provisioning tool."
          sys.exit()
      
        #Assign the ip address for the first interface
        new_host_data['host']['ip'] = ip
        #Set the subnet id for the host.
        new_host_data['host']['subnet_id'] = subnet_data['id']
 
        #NOTE: We need to consider creating a create or update function for this dict:
	#['host']['host_parameters_attributes']
        #If we ever want to set more than one parameter we will be up poop creek.
 
        #Create the second interface if it is requested
        if ip2:
          #Gte the appropriate subnet based on the IP requested.
          subnet_data2 = self.get_subnet(ip2)
          #Set the global parameter for the IP Address as we will need this to configure the interface in kickstart
          #Tje reference_id is currently the id of the main Foreman box in JC.  That is wiggy.
          #Move to the update post server build if you want this to be awesome.
          hpas  = {}
	  hpas['mst_nic2_ip'] = {  'name' : 'mst_nic2_ip' , 'value' : ip2 , "reference_id": 20 }   
	  hpas['mst_nic2_subnet'] = {  'name' : 'mst_nic2_subnet' , 'value' : subnet_data2['mask'] , "reference_id": 20 }   
          new_host_data['host']['host_parameters_attributes'] = hpas 
          if subnet_data2:
            print "Assigning subnet: " + subnet_data2['name'] + " to IP address: "  + ip2
          else:
            print "No matching subnet was found for IP Address " + ip2
            print "Cannot continue build.  Validate subnet for IP provided exists in provisioning tool."
            sys.exit()

        #Calulate the disk sizes based on the ptables
        ptable_disk_sizes = self.get_disk_size(hostgroup)
        print ptable_disk_sizes
        #If no hd size is set but a datastore is selected then use the sizes from the PTABLE 
        #Extra in GB to add per disk to allow for growing.
        extra_hd = 10
        if hd0_size == "" and hd0_ds:      
            hd0_size = int( math.ceil(float(ptable_disk_sizes["sda"])/1024) ) + extra_hd
        if hd1_size == "" and hd1_ds:
            hd1_size = int( math.ceil(float(ptable_disk_sizes["sdb"])/1024) ) + extra_hd
        #Assign compute resource if it requested     
        if compute_resource:
            new_host_data['host']['compute_resource_id'] = self.get_id(compute_resource,"compute_resources")

        #If we are specifying a compute profile then overwrite the default for the hostgroup
        if compute_profile:
            compute_profile_id = self.get_id(compute_profile,"compute_profiles")
            new_host_data['host']['compute_profile_id'] = compute_profile_id  

        #IF we have a compute profile set then configure any specific compute attributes   
        if compute_profile_id: 
            #Pull the compute attributes defined for the specified compute profile
            compute_attributes = self.get_compute( str( compute_profile_id ) )
            #Modify the compute attributes after the profile sets this data...
            if cpu: 
              compute_attributes['cpus'] = cpu
            if memory_mb:
              compute_attributes['memory_mb'] = memory_mb
            if cluster:
              compute_attributes['cluster'] = cluster

            #Configure the Virtual NIC(s).
            #The following attributes are reqiured to configure the VMware network:


            #If a network label is provided use it vs the subnet name.
            if network_label:
              compute_attributes['interfaces_attributes']['0']['network'] = network_label 
              compute_attributes['interfaces_attributes']['new_interfaces']['network'] = network_label 
            else:
              compute_attributes['interfaces_attributes']['0']['network'] = subnet_data['name']
              compute_attributes['interfaces_attributes']['new_interfaces']['network'] = subnet_data['name']


            #Create the second interface if it is requested
            if ip2:
              #Create the second interface 
              compute_attributes['interfaces_attributes']['1'] = {}
              #If a network label is provided use it vs the subnet name.
              if network_label2:
                compute_attributes['interfaces_attributes']['1']['network'] = network_label2 
                compute_attributes['interfaces_attributes']['1']['type'] = 'VirtualVmxnet3' 
              else:
                compute_attributes['interfaces_attributes']['1']['network'] = subnet_data2['name']
                compute_attributes['interfaces_attributes']['1']['type'] = 'VirtualVmxnet3'

            #Set first hard driver parametes
            compute_attributes['volumes_attributes']['0']['name'] = 'Hard Disk 0' 
            compute_attributes['volumes_attributes']['0']['size_gb'] = hd0_size
            compute_attributes['volumes_attributes']['0']['datastore'] = hd0_ds
            #Set the second hard drive if requested.
            if hd1_size and hd1_ds:
              #Create the dictionary for the second hard drive
              new_disk =  { 'size_gb': hd1_size,
                  'name': 'Hard disk 1',
                  '_delete': '',
                  'thin': 'true',
                  'eager_zero': 'false',
                  'datastore': hd1_ds}
              compute_attributes['volumes_attributes']['1'] = new_disk
            new_host_data['host']['compute_attributes'] = compute_attributes
       
        #Trap for missing compute_attributes dictionary. 
        try:
          compute_attributes
        except NameError:
          print "Error: Compute attributes not set."  
          print "You may need to manually override the Compute Profile if the Host Group is a child VS inheriting it..."
          sys.exit()
        #Convert dict to json object
        new_host_dump = json.dumps(new_host_data) 
        #Attempt to post the new host request:w
        new_host = self.post_json(self.foreman_api + "hosts" ,new_host_dump )
        #Perform post host creation processes.
        if "id" in new_host:
            #Attempt to add a second interface if it is requested
        #    if ip2:
        #      print subnet_data2
        #      self.add_host_fact(new_host['name'],'secondary_ip',ip2)              
              #Currently this requires the mac address of the secondary interface.
              #I have not found a sane way to retrieve this yet, thus it is commented out.
              #self.add_interface(new_host['id'],ip2,subnet_data2['id'],'eth1') 
            #Attempt to power on the host
            if power == 'on':
              new_host_id = str(new_host["id"])
              host_power_on = { "id": new_host_id,"power_action": True }
              new_host_power_state = self.put_json(self.foreman_api + "hosts/"  + new_host_id + "/power" ,json.dumps( { "id": new_host_id,"power_action": "start" } ) )
        return new_host
