#!/usr/bin/python
"""
Purpose: Configure Attributes of VM and modify it's power state.
         The original intent was to make per VM settings more granular when 
		 provisioning systems using the Foreman API. 
Written by: Robert Lupinek
Sources:
"""
import atexit
from pyVim import connect
from  pyVmomi import vim
from pyVmomi import vmodl
import sys
#Disable SSL warnings
import requests
requests.packages.urllib3.disable_warnings()

class vmware_helper:
    def __init__(self,host,user,pwd,port):
        self.si = None
        try:
            self.si = connect.SmartConnect(host=host,user=user,pwd=pwd,port=port)
            atexit.register(connect.Disconnect, self.si)
        except Exception as e:
            print str(e)
            pass
        if not self.si:
            raise SystemExit("Unable to connect to host with supplied info.")
    
    def wait_for_tasks(self,service_instance, tasks):
        """Given the service instance si and tasks, it returns after all the
       tasks are complete
       Happily borrowed from the pyvmomi samples project helper module for tasks:
            https://github.com/vmware/pyvmomi-community-samples/blob/master/samples/tools/tasks.py
       """
        property_collector = service_instance.content.propertyCollector
        task_list = [str(task) for task in tasks]
        # Create filter
        obj_specs = [vmodl.query.PropertyCollector.ObjectSpec(obj=task)
                     for task in tasks]
        property_spec = vmodl.query.PropertyCollector.PropertySpec(type=vim.Task,
                                                                   pathSet=[],
                                                                   all=True)
        filter_spec = vmodl.query.PropertyCollector.FilterSpec()
        filter_spec.objectSet = obj_specs
        filter_spec.propSet = [property_spec]
        pcfilter = property_collector.CreateFilter(filter_spec, True)
        try:
            version, state = None, None
            # Loop looking for updates till the state moves to a completed state.
            while len(task_list):
                update = property_collector.WaitForUpdates(version)
                for filter_set in update.filterSet:
                    for obj_set in filter_set.objectSet:
                        task = obj_set.obj
                        for change in obj_set.changeSet:
                            if change.name == 'info':
                                state = change.val.state
                            elif change.name == 'info.state':
                                state = change.val
                            else:
                                continue
    
                            if not str(task) in task_list:
                                continue
    
                            if state == vim.TaskInfo.State.success:
                                # Remove task from taskList
                                task_list.remove(str(task))
                            elif state == vim.TaskInfo.State.error:
                                raise task.info.error
                # Move to next version
                version = update.version
        finally:
            if pcfilter:
                pcfilter.Destroy()
    
    
    def get_obj(self, content,vimtype, name):
        """
         Get the vsphere object associated with a given text name
        """    
        obj = None
        #Retrieve the content of the smart connect object
        content = self.si.RetrieveContent()
        #Return the container for the content view
        container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
        for c in container.view:
            if c.name == name:
                obj = c
                break
        return obj
    
    def power_state(self,vm,state):
        task = None
	try:
            if state == 'off':
                task = vm.PowerOffVM_Task()
            if state == 'on':
                task = vm.PowerOnVM_Task()    
            if task:
                self.wait_for_tasks(self.si,[task])
        #If the exception due to the power state is already set to desired state then pass...
	except vim.fault.InvalidPowerState:
            print "Could not change power state to " + state + " due to state already being " + state + "."          
            pass
        #Everything else should BOMB baby bomb.
        except Exception, e:
            raise SystemExit("power state: " + str(e) )
        print "Power state configuration complete."
    
    def configure_vm(self,vm,cpu_count,memory_mb,annotation):
        try:
            #Create a new ConfigSpec with the specific attributes we desire
            spec = vim.vm.ConfigSpec( annotation = annotation,numCPUs = cpu_count, memoryMB = memory_mb )
            #Trigger the reconfiguraion task
            task = vm.ReconfigVM_Task(spec=spec)    
            self.wait_for_tasks(self.si,[task])
        except Exception, e:
            raise SystemExit("Failed to reconfigure VM: " + str(e) )
        print "VM configuration a success."

    def annotate_vm(self,vm,annotation):
        try:
            #Create a new ConfigSpec with the specific attributes we desire
            spec = vim.vm.ConfigSpec( annotation = annotation )
            #Trigger the reconfiguraion task
            task = vm.ReconfigVM_Task(spec=spec)
            self.wait_for_tasks(self.si,[task])
        except Exception, e:
            raise SystemExit("Failed to reconfigure VM: " + str(e) )
        print "VM configuration a success."
            
    def get_vm(self,search_string,search_type):
        #Specify search string (VM name or UUID ) and if you are seaching by 'uuid' or 'name'
        #If searching by name 
        if search_type == 'name':
            #Retrieve the content of the smart connect object
            content = self.si.RetrieveContent()
            print content 
            vm = self.get_obj(content, [vim.VirtualMachine], search_string )
        #If searching by VM uuid
        if search_type == 'uuid':
            search_index = self.si.content.searchIndex
            vm = search_index.FindByUuid(None, uuid = search_string, instanceUuid = True, vmSearch = True)
        #Calling the config operation returns an instance of vim.vm.ConfigInfo
        config = vm.config
        #You can use the attributes available to the object for printing or otherwise
        #print config.uuid #UUID of VM
        print "Found vm with the following UUID: " + config.instanceUuid #Unique UUID maintained by vCenter called instance UUID
        return vm
