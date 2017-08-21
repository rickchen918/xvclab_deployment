$vcenter="pvc.rkc.local"
$vcuser="administrator@rkc.local"
$vcpass="Nicira123$"
$remotepath="/volume1/nsx_lab"
$esx1="192.168.64.50"
$esx2="192.168.64.51"


# environment parameter setup 
Get-Module -ListAvailable PowerCLI* | Import-Module
# the notes for Set-PowerCLIConfiguration. the multi-server mode is default and prompt warning to accept (change to single) and add -Confirm:$false to avoid 
Set-PowerCLIConfiguration -DefaultVIServerMode 'Single' -InvalidCertificateAction Ignore -Confirm:$false

# conecting to vCenter License Maanger 
write-host "Connecting to vCenter Server $vcenter" -foreground green 
Connect-VIServer $vcenter -user $vcuser -password $vcpass 

#create VC datacenter 
new-datacenter -location datacenters -name pvc-dc

# create infra clusetrs
new-cluster -location pvc-dc -name pvc-cluster 

# register hosts to vc
add-vmhost $esx1 -Location pvc-dc -User root -Password nicira123 -Force
add-vmhost $esx2 -Location pvc-dc -User root -Password nicira123 -Force

# move host into cluster
move-vmhost $esx1 -destination pvc-cluster
move-vmhost $esx2 -destination pvc-cluster

# mount nfs storage to hosts
new-datastore -nfs -vmhost $esx1 -name nsx_lab -path $remotepath -nfshost 192.168.0.96
new-datastore -nfs -vmhost $esx2 -name nsx_lab -path $remotepath -nfshost 192.168.0.96

# create new vds 
new-vdswitch -name pvc-nsx -location pvc-dc -NumUplinkPorts 2

# attach host into vds 
Add-VDSwitchVMHost -VDSwitch pvc-nsx -VMHost $esx1
Add-VDSwitchVMHost -VDSwitch pvc-nsx -VMHost $esx2

# attach vmnic1 to vds
$vmhostnetworkadpater=get-vmhost $esx1 |get-vmhostnetworkadapter -physical -name vmnic1
get-vdswitch pvc-nsx | add-vdswitchphysicalnetworkadapter -vmhostnetworkadapter $vmhostnetworkadpater -confirm:$false
$vmhostnetworkadpater=get-vmhost $esx2 |get-vmhostnetworkadapter -physical -name vmnic1
get-vdswitch pvc-nsx | add-vdswitchphysicalnetworkadapter -vmhostnetworkadapter $vmhostnetworkadpater -confirm:$false

