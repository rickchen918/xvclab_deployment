import json,os,subprocess,time,ssl,OpenSSL,requests,paramiko,pdb

psc_json="./psc.json"
pvc_json="./pvc.json"
svc_json="./svc.json"
pvsm_json="./pvsm.json"
svsm_json="./svsm.json"
vsphere_iso="/root/project/nsx-v/nsx_functions/VMware-VCSA-all-6.5.0-5178943.iso"
vsm_ova="../nsx_functions/VMware-NSX-Manager-6.3.3-6276725.ova"
vm_ds="nsx_lab"

class deployment(object):
    def __init__(self,file):
	self.file=file
	with open(self.file) as kv:
	    js=json.load(kv)
	    self.js=js

    def vc_deploy(self,iso,json):
	iso_path = iso
	script_path = "./iso/vcsa-cli-installer/lin64/vcsa-deploy"
	template_path = "%s"%json
	log_path = os.getcwd()
	log_dir = "--log-dir %s" %log_path

	#create mount point of iso
	subprocess.call(["mkdir","iso"])
	subprocess.call(["mount",iso_path,"iso"])

	print "\n"
	print "*" *100
	print "The VCSA appliance is starting to deploy"
        print "\n"
        print "*" *100

	#deploy vc appliance align with template configuration
	os.system("%s install --no-esx-ssl-verify --acknowledge-ceip --accept-eula %s --verbose %s" %(script_path,template_path,log_dir))

	time.sleep(10)

	#recovery env before deployment
	subprocess.call(["umount","./iso"])
	subprocess.call(["rm","-rf","./iso"])

	with open("vcsa-cli-installer.log") as file:
    	    key = file.read()
    	    if key.find("First time configuration succeeded") != -1:
       	        print "\n"
		print "=" * 100
        	print "The VCSA appliance has been sucessfully deployed"
       		print "\n"
        	print "=" *100
        	os.system("rm %s/vcsa-cli-installer*" %log_path)
    	    else:
                print "\n"
         	print "=" * 100
         	print "The deployment may not be sucessful, please review vcsa-cli-installer.log"
                print "\n"
                print "=" * 100
		exit()

    def vsm_deploy(self,ova):
	vsm=self.js['vsm']
	vc=self.js['vc']
	dst_net = vc['net']
	vc_user = vc['vc_user']
	vc_pass = vc['vc_passwd']
	vc_server = vc['vcenter']
	dc_name = vc['dc_name']
	cluster_name = vc['cluster_name']
	ova_name = ova

	cli_passwd=vsm["vsm_cli_passwd_0"]
	cli_en_passwd=vsm["vsm_cli_en_passwd_0"]
	hostname=vsm["vsm_hostname"]
	ip=vsm["vsm_ip_0"]
	netmask=vsm["vsm_netmask_0"]
	gateway=vsm["vsm_gateway_0"]
	dns1=vsm["vsm_dns1_0"]
	domain=vsm["vsm_domain_0"]
	ntp=vsm["vsm_ntp_0"]
	sshenable=vsm["vsm_isSSHEnabled"]

        print "\n"
        print "=" * 100
        print "The NSX Manager appliance is starting to deploy"
        print "\n"
        print "=" *100

	deploy ="""ovftool --X:logFile=log --X:injectOvfEnv --acceptAllEulas --powerOn --noSSLVerify --diskMode=thin \
	--allowExtraConfig --X:waitForIp --name=%s --datastore=%s --net:VSMgmt=%s \
	--prop:vsm_cli_passwd_0=%s \
	--prop:vsm_cli_en_passwd_0=%s \
	--prop:vsm_hostname=%s \
	--prop:vsm_ip_0=%s \
	--prop:vsm_netmask_0=%s \
	--prop:vsm_gateway_0=%s \
	--prop:vsm_dns1_0=%s \
	--prop:vsm_domain_0=%s \
	--prop:vsm_ntp_0=%s \
	--prop:vsm_isSSHEnabled=%s \
	%s \
	vi://"%s":"%s"@"%s"/%s/host/%s """ %(hostname,vm_ds,dst_net,cli_passwd,cli_en_passwd,hostname,ip,netmask,\
	gateway,dns1,domain,ntp,sshenable,ova_name,vc_user,vc_pass,vc_server,dc_name,cluster_name)

	#deploy cmd with above definition
	check=os.system(deploy)

	#verfiy deployment result from log keyword search
	with open('log') as file:
   	 extract = file.read()
    	 if extract.find("Ovf convertion finished") != -1:
       	     print "\n"
	     print "="*100
	     print " The ovf deployment has been done, the VSM is booting up "
             print "="*100
	     print "\n"
             os.system("rm log")
   	 else:
	    print "\n"
	    print "="*100
	    print "The deplpyment is not completed, check log "
	    print "="*100
	    print "\n"
	    exit()

    def registration(self,vcsajson):
	vsm = self.js['vsm']
	vsmip = vsm['vsm_ip_0']
	vsmuser = "admin"
	vsmpasswd = vsm['vsm_cli_passwd_0']
	
	with open(vcsajson) as vc:
	    js=json.load(vc)
	    vcip=js['new.vcsa']['network']['ip']
	    vcdomain=js['new.vcsa']['sso']['domain-name']
	    vcuser="administrator@"+str(vcdomain)
	    vcpasswd=js['new.vcsa']['os']['password']
	api_cert = ssl.get_server_certificate((vcip, 9443), ssl_version=2)
	x509_api = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, api_cert)
	api_cert_thumbp = x509_api.digest('sha1')

	url = "https://"+str(vsmip)+"/api/2.0/services/vcconfig"
	header={"Content-type":"application/xml"}
	body='''<vcInfo>
	<ipAddress>%s</ipAddress>
	<userName>%s</userName>
	<password>%s</password>
	<certificateThumbprint>%s</certificateThumbprint>
	<assignRoleToUser>true</assignRoleToUser>
	<pluginDownloadServer></pluginDownloadServer>
	<pluginDownloadPort></pluginDownloadPort>
	</vcInfo>''' %(vcip,vcuser,vcpasswd,api_cert_thumbp)

	conn=requests.put(url,auth=(vsmuser,vsmpasswd),verify=False,data=body,headers=header)
	if conn.status_code == 200:
	    print "\n"
	    print "=" * 100
	    print "the service has been registerred to vCenter" 
	    print "=" * 100
	    print "\n"
	else: 
	    print "\n"
	    print "=" * 100
	    print "the service is not registerred sucessfully" 	
	    print "=" * 100
    	    print "\n"
	    exit()

def autodeploy(vcsajson):
    with open(vcsajson) as vc:
        js=json.load(vc)
        vcip=js['target.vcsa']['network']['ip']
        vcpasswd=js['target.vcsa']['os']['password']
    ssh=paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # The init root password is same as administrator, just hardcode here to make simple 
    ssh_conn="ssh.connect('%s',username='root',password='%s')" %(vcip,vcpasswd)
    exec(ssh_conn)
    # the reg line is not tested yet 
    reg="autodeploy-register --register -R -a %s -u root -w %s -p 80 -s /etc/vmware-rbd/autodeploy-setup.xml" %(vcip,vcpasswd)
    stdin,stdout,stderr=ssh.exec_command(reg)
    exec(ssh_conn)    
    stdin,stdout,stderr=ssh.exec_command("/etc/init.d/vmware-rbd-watchdog start")
    ssh.close()

# create vcenter, cluster and vds for lab basic
def vclab_conf():
    os.system("powershell -Command ./labpvc-conf.ps1")
    os.system("powershell -Command ./labsvc-conf.ps1")

def nested_esx():
    os.system("powershell -Command ./pvchv-create.ps1")
    os.system("powershell -Command ./svchv-create.ps1")

print "deploying PSC "
deployment(psc_json).vc_deploy(vsphere_iso,psc_json)
print "deploying Primay vCenter"
deployment(pvc_json).vc_deploy(vsphere_iso,pvc_json)
print "deploying Secondary vCenter"
deployment(svc_json).vc_deploy(vsphere_iso,svc_json)
deployment(pvsm_json).vsm_deploy(vsm_ova)
deployment(svsm_json).vsm_deploy(vsm_ova)
time.sleep(600)
deployment(pvsm_json).registration(pvc_json)
deployment(svsm_json).registration(svc_json)
nested_esx()
time.sleep(900)
vclab_conf()




