#!/usr/bin/python
import vmware_helper
#To use command line ags
#Results in an object example to use: args.password
#args = get_args()

host = 'vcenterhost'
user = 'username'
pwd = 'password'
port = 443
vm_name = 'vmname'
uuid = '501b6f99-3dc7-fda3-9741-1fa115d56ea1' #Instance UUID

vm_helper = vmware_helper.vmware_helper(host,user,pwd,port)
#Searching by uuid is SOOO Much faster, but it requires knowing how to get it.
#vm = vm_helper.get_vm(uuid,'uuid')
vm = vm_helper.get_vm(vm_name,'name')
#Power the vm down in case you would like to modify the config 
vm_helper.power_state(vm,'off')
vm = vm_helper.annotate_vm(vm,'THIS IS SO AWESOME!')
#If you want to modify the vm's configuration beyond annotation.
vm_helper.configure_vm(vm,2,4096,"You rule bro!")
#Power the VM down
vm_helper.power_state(vm,'on')
