$vmhost="192.168.0.56"
$vcenter="vc.rkc.local"
$vcuser="administrator@rkc.local"
$vcpass="Nicira123$"
$vm_count="2" 
$numcpu="4"
$diskspace="40960"
$memory="12288"
$ds="nsx_lab"
$guestid="vmkernel65Guest"
#$guestid="vmkernel6Guest"

$network1="64-0"
$network2="65-0"

# environment parameter setup 
Get-Module -ListAvailable PowerCLI* | Import-Module
# the notes for Set-PowerCLIConfiguration. the multi-server mode is default and prompt warning to accept (change to single) and add -Confirm:$false to avoid 
Set-PowerCLIConfiguration -DefaultVIServerMode 'Single' -InvalidCertificateAction Ignore -Confirm:$false

# conecting to vCenter 
write-host "Connecting to vCenter Server $vcenter" -foreground green 
Connect-VIServer $vcenter -user $vcuser -password $vcpass

# create nested vsphere by the while loop
$i=1
while($i -le $vm_count) {
	New-VM -VMHost $vmhost -Name pvc-esxi$i -Datastore $ds -DiskMB $diskspace -MemoryMB $memory -NumCpu $numcpu -GuestID $guestid -NetworkName $network1,$network2
	$vm=Get-VM | ? {$_.name -match "pvc-esxi$i"}
	$nicnum=Get-NetworkAdapter $vm |  ?{$_.name -match "Network adapter 1"}
    	$mac_addr="00:50:56:00:00:0$i"
	Set-NetworkAdapter $nicnum -Confirm:$false -MacAddress $mac_addr
	$i ++
}

# setup the cpu hardware virtualization functions 
$vm=Get-VM pvc-esx**
$spec=New-Object VMware.Vim.VirtualMachineConfigSpec
$spec.nestedHVEnabled = $true
$vm.ExtensionData.ReconfigVM($spec)

# poweron VMs
Start-VM -VM $vm 
