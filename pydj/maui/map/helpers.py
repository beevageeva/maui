from settings import MAPHOSTS,TEMPLATE_DIRS
import re,logging
from django.template import Context, Template
import libssh2
import os
import scp_upload
import ssh_exec
import sftp_listdir

logger=logging.getLogger(__name__)



def listjobsSlurm(session):
	listres = parseoutput(session,"squeue",2,-1,["id","queue","name" , "user", "state", "timeUse" , "nodes" ,  "nodeList"])
	return listres

def listjobsTorque(session):
	listres = parseoutput(session,"qstat",3,0,["id","name", "user", "timeUse", "state", "queue"])
	return listres

def listresSlurm(session):
	listres = parseoutput(session, "sinfo -N -l", 1, -1, ["NODELIST", "NODES", "PARTITION" ,  "STATE", "CPUS"  ,  "SCT", "MEMORY", "TMP_DISK", "WEIGHT", "FEATURES", "REASON"])
	return listres

def regexpf(key,field):
	return  (key , re.compile("^" + field + "=(\S+)") )
	

def listnodesSlurm(session):
#NodeName=drago0 Arch=x86_64 CoresPerSocket=10 CPUAlloc=0 CPUErr=0 CPUTot=40 Features=(null) Gres=(null) NodeAddr=drago0 NodeHostName=drago0 OS=Linux RealMemory=1 Sockets=4 State=IDLE ThreadsPerCore=1 TmpDisk=0 Weight=1 BootTime=2012-02-09T10:21:15 SlurmdStartTime=2012-02-09T12:02:43 Reason=(null)
	listres = parseoutput(session, "scontrol show nodes -o", -1, -1, [ 
		regexpf('id', 'NodeName'),  
		regexpf('Arch', 'Arch'),  
		regexpf('CoresPerSocket', 'CoresPerSocket'),  
		regexpf('CPUAlloc', 'CPUAlloc'),  
		regexpf('CPUErr', 'CPUErr'),  
		regexpf('CPUTot', 'CPUTot'),  
		regexpf('Features', 'Features'),  
		regexpf('Gres', 'Gres'),  
		regexpf('NodeAddr', 'NodeAddr'),  
		regexpf('NodeHostName', 'NodeHostName'),  
		regexpf('OS', 'OS'),  
		regexpf('RealMemory', 'RealMemory'),  
		regexpf('Sockets', 'Sockets'),  
		regexpf('State', 'State'),  
		regexpf('ThreadsPerCore', 'ThreadsPerCore'),  
		regexpf('TmpDisk', 'TmpDisk'),  
		regexpf('Weight', 'Weight'),  
		regexpf('BootTime', 'BootTime'),  
		regexpf('SlurmdStartTime', 'SlurmdStartTime'),  
		regexpf('Reason', 'Reason') 
	])
	return listres


def listnodes(session):
	listres =  sorted(parseoutput(session, "diagnose -n", 4, 4,["id","state","procs","memory","disk", "Swap" ,     "Speed" , "Opsys",   "Arch", "Par" ,  "load", "Res" ,"classes"," Network"," features"]), key=lambda node: node['id'] )
	return listres

def getgangliaurl(sessionhost):
	if(MAPHOSTS[sessionhost]['enable_ganglia']):
		if MAPHOSTS[sessionhost].has_key("ganglia_cluster_name"):
			cn = MAPHOSTS[sessionhost]["ganglia_cluster_name"]
		else:
			cn = sessionhost
		return MAPHOSTS[sessionhost]['ganglia_url'] + 'graph.php?m=load_one&z=small&c=' + cn + '&x=0&g=load_report&n=0&r=hour&h='
	return None

def listres(session):
	return parseoutput(session,"showres -n",5,1,["nodeid", "type" , "resid" ,  "jobState", "task"    ,   "start" ,   "duration"     ,  "startTimeDayOfWeek" , "startTimeMonth" , "startTimeDayOfMonth", "startTime" ])


def liststats(session):
	return parseoutput(session,"showstats -u",5,2,[ "user"  ,"jobs",  "procs" , "procHours" , "jobs"   , "jobsprc",    "phReq"  ,  "phReqPrc" ,   "phDed"  ,  "phDedPrc" ,  "fsTgt" , "avgXF" , "maxXF" , "avgQH" , "effic" , "wCAcc" ])

def getqueuesfromcfg(sessionhost):
	queues = MAPHOSTS[sessionhost]['queues']
	if isinstance(queues,tuple):	
		return map(lambda x: (x,x), MAPHOSTS[sessionhost]['queues'])
	else:
		return [(queues, queues)]


def getjoboutSlurm(session,jobid):
	return re.split("\n",execcommand(session,"scontrol show job  "+ jobid))	

def getjobout(session,jobid):
	return re.split("\n",execcommand(session,"checkjob -v "+ jobid))

def getjoboutTorque(session,jobid):
	return re.split("\n",execcommand(session,"qstat -f "+ jobid))

def getnodeoutSlurm(session,nodeid):
	return re.split("\n",execcommand(session,"scontrol show  node  "+ nodeid))	

def getnodeout(session,nodeid):
	return re.split("\n",execcommand(session,"checknode -v "+ nodeid))


def getScriptContent(h, rmtype):
	f = open (TEMPLATE_DIRS + "/script_" + rmtype +".sh", "r") 
	t = Template(f.read())
	f.close()
	c = Context(h)
	return t.render(c)



def submitJob(session, scriptFilename):
	rmtype = MAPHOSTS[session["host"]]['rmtype']
	if rmtype == "slurm":
		submitcommand = "sbatch"
		resregexp = re.compile("^Submitted batch job (\S+)$")
	else:
		submitcommand = "qsub"
		resregexp = re.compile("^\s*(\S+).+")
	res = execcommand(session, submitcommand + "  "+scriptFilename )
	m = resregexp.match(res)
	if m:
		jobid = m.group(1)
		return jobid
	return None



def parseoutput(session,cmd,tailplus,headminus,fields):
	cmdstr = cmd
	if tailplus!=-1:
		cmdstr += " | tail -n +"+ str(tailplus)
	if headminus!=-1:
		cmdstr += " | head -n -" + str(headminus) 

	#logger.debug("cmdstr:" +cmdstr )
	out =  execcommand(session,cmdstr)
	lines = re.split("\n", out)
	res = []
	for line in lines:
		m = re.split("\s+",line)
		o = {}
		#if string starts with \s+ split will put "" in the first elem
		if m[0]=="":
			m.pop(0)
		i=0
		while i<len(fields) and i<len(m):

			f = fields[i]
			# como en scontrol show nodes -o
			#output  NodeName=drago0 ...
			# ('nodeName' , re.compile('^NodeName=(\S+)'))  
			if isinstance(f,tuple):
				regexp = f[1]
				field = f[0]
				rematch = regexp.match(m[i])
				if rematch:
					value = rematch.group(1) 
				else:
					value=""
			else:
				field = f	
				value = m[i]
			o[field] = value
			#logger.debug(field + "=" + value )

#			o[fields[i]] = m[i]


			i+=1
		if i==len(fields):
			res.append(o)
		else:
			logger.debug("LINE " + str(i) +":" +line + "END")
	return res

	
def remoteListdir(session, dirname="."):
	host = session['host']
	listdirdata = sftp_listdir.MySFTPClient(hostname=MAPHOSTS[host]['host'], username=session['username'], password=session['password'], port=MAPHOSTS[host]['port'] ).listdir(dirname)
	filenames = []
	for data in listdirdata:
		if len(data)>=2 and data[1]:
			if data[0]!='.' and data[0]!="..":	filenames.append( (data[0], data[1][0] == 4096) )
	filenames = sorted(filenames, key=lambda fn: fn[0])
	if dirname!=".": filenames.insert(0,("..",True))
	return filenames




def authenticate(host,username,password):
	src = ssh_exec.SSHRemoteClient(MAPHOSTS[host]['host'], username, password, MAPHOSTS[host]['port'])
	out = src.execute()
	return out

def execcommand(session,cmd):
	host = session['host']
	src = ssh_exec.SSHRemoteClient(MAPHOSTS[host]['host'], session['username'], session['password'], MAPHOSTS[host]['port'])
	res =  src.execute(cmd)
#	print "command:"
#	print cmd
#	print "res:"
#	print res
#	print "res-end:"
	return res

def uploadfile(session,filename,remotefilename):
	host = session['host']
	myscp = scp_upload.MySCPClient(hostname=MAPHOSTS[host]['host'], username=session['username'], password=session['password'], port=MAPHOSTS[host]['port'])
	myscp.send(filename,remotefilename)

def downloadfile(session,remotefilename):
	host = session['host']
	myscp = scp_upload.MySCPClient(hostname=MAPHOSTS[host]['host'], username=session['username'], password=session['password'], port=MAPHOSTS[host]['port'])
	return myscp.recv(remotefilename)


	
