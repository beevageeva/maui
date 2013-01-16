from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.core.servers.basehttp import FileWrapper
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import requires_csrf_token
import os
import simplejson
import logging,random,string

from forms import LoginForm,SubmitJobForm
import helpers
from models import JobDef
from maui.settings import TEMP_DOC_ROOT,MAPLAYOUTS, MAPHOSTS


logger=logging.getLogger(__name__)



def login_required(viewfunc):
	def wrappedviewfunc(request,*args,**kvargs):
		if(not request.session.has_key('username') or not request.session['username']):
			return render_to_response('login.html', {'form':LoginForm(),'error_message': 'Login required'},context_instance=RequestContext(request) )
		else:
			return viewfunc(request,*args,**kvargs)
	return wrappedviewfunc



def login(request):
	if request.method == 'POST': # If the form has been submitted...
		form = LoginForm(request.POST) # A form bound to the POST data
		if form.is_valid(): # All validation rules pass
			username = form.cleaned_data['username']
			password = form.cleaned_data['password']
			host = form.cleaned_data['host']
			if helpers.authenticate(host,username, password):
				request.session['username'] = username
				request.session['host'] = host
				request.session['password'] = password
				return HttpResponseRedirect('listjobsTorque') # Redirect after POST
			else:
				return render_to_response('login.html', {'form':form,'error_message': 'Invalid authentication'},context_instance=RequestContext(request) )
	else:
		return render_to_response('login.html', {'form':LoginForm()},context_instance=RequestContext(request) )


@login_required
def logout(request):
	request.session['username'] = None	
	request.session['password'] = None	
	request.session['host'] = None	
	return render_to_response('login.html', {'form':LoginForm()},context_instance=RequestContext(request) )


@login_required
def changeHost(request,host):
	request.session['host'] = host
	return HttpResponseRedirect(reverse('map.views.listjobsTorque'))


@login_required
def changeLayout(request,layout):
	if layout in MAPLAYOUTS:
		request.session['layout'] = layout
	return HttpResponseRedirect(reverse('map.views.listjobsTorque'))


@login_required
def listdirsAjax(request,dirname):
	dirname = dirname.replace("__POINT__",".").replace("__SLASH__","/").replace("__SPACE__"," ")
	logger.debug("in lisDirAjax: before normpath " + dirname)
	dirname = os.path.normpath(dirname)
	logger.debug("in lisDirAjax: " + dirname)
	listdir = helpers.remoteListdir(request.session,dirname)	
	json = simplejson.dumps(listdir)
	return HttpResponse(json, mimetype='application/json')


@login_required
def submitscript(request):
	if request.method == 'POST': # If the form has been submitted...
		scriptname = request.POST['scriptname']	
		cleanscriptname = scriptname.replace("%",".").replace("|","/")
		jobid = helpers.submitJob(request.session,cleanscriptname )
		message = "SUBMIT " + cleanscriptname+ ": "
		if jobid:
			message+=jobid
		else:
			message+="job not queued"	
	else:
		message = "GET method not allowed"	
	return listjobs(request,message)	



@login_required
def liststats(request):
	if isSlurm(request.session):
		return render_to_response('liststatsSlurm.html', {},context_instance=RequestContext(request)) 
	else:
		listres =  helpers.liststats(request.session)
		return render_to_response('liststats.html', {'list': listres, 'listlen':len(listres) },context_instance=RequestContext(request)) 
	

@login_required
def listnodes(request):
	slurm = isSlurm(request.session)
	if slurm:
		listnodes = helpers.listnodesSlurm(request.session)
	else:
		listnodes = helpers.listnodes(request.session)
	return render_to_response('listnodes.html', {'list': listnodes, 'isSlurm' : slurm ,   'gangliaurl':helpers.getgangliaurl(request.session['host']) },context_instance=RequestContext(request))



@login_required
def submitjob(request):
	if request.method == 'POST': # If the form has been submitted...
		form = SubmitJobForm(request.POST) # A form bound to the POST data
		if form.is_valid():
				if isSlurm(request.session):
					rmtype = "slurm"
				else:
					rmtype = "torque" 
				out = helpers.getScriptContent(form.cleaned_data, rmtype)
				#print "SUBMIT JOb"
				#print out
				helpers.uploadfile(request.session,out, form.cleaned_data['scriptFilename'])
				message="SUMBIT "+form.cleaned_data["scriptFilename"] + ": "
				jobid = helpers.submitJob(request.session,form.cleaned_data["scriptFilename"] )
				if jobid:
					message+=jobid
				else:
					message+="job not queued"		
				jobdef = form.save()
				if jobdef:
					jobdef.username = request.session['username']
					jobdef.host = request.session['host']
					jobdef.jobid = jobid	
					if jobdef.save():
						message+=", Job saved"
				return listjobs(request,message)	
	form = SubmitJobForm()
	form.fields['queue'].widget.choices= helpers.getqueuesfromcfg(request.session['host'])
	return render_to_response('submitjob.html', {'form':form},context_instance=RequestContext(request) )


def downloadfile(session,remotefilename,downloadname):
	ret = helpers.downloadfile(session,remotefilename)
	filename =  TEMP_DOC_ROOT +  ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(10))
	localfile = open(filename,'w')		
	if ret: localfile.write(ret)
	localfile.close()
	localfile = open(filename, 'rb')		
	wrapper = FileWrapper(localfile)
	#no close on file
	response = HttpResponse(wrapper, content_type='text/plain')
	response['Content-Disposition'] = 'attachment; filename='+downloadname
	return response




@login_required
def downloaderror(request,jobdefid):
	job=JobDef.objects.get(id=jobdefid)
	return downloadfile(request.session,job.errorfile,"errorfile")


@login_required
def downloadout(request,jobdefid):
	job=JobDef.objects.get(id=jobdefid)
	return downloadfile(request.session,job.outfile,"outfile")

@login_required
def downloadscript(request,jobdefid):
	job=JobDef.objects.get(id=jobdefid)
	return downloadfile(request.session,job.scriptFilename,"script.sh")


@login_required
def deleteMyjob(request,jobdefid):
	job = JobDef.objects.get(id=jobdefid)
	if(job and job.username == request.session['username']):
		job.delete()
	return HttpResponseRedirect(reverse('map.views.listMyjobs'))


@login_required
def deletejobTorque(request,jobid):
	if isSlurm(request.session):
		deletecommand = "scancel"
	else:	
		deletecommand = "qdel"
	message="cancel "+jobid + ": "
	message += helpers.execcommand(request.session, deletecommand + " "+jobid )
	return listjobs(request,message)	

@login_required
def viewjob(request,jobid):
	if isSlurm(request.session):
		outlines = helpers.getjoboutSlurm(request.session,jobid)
		outlinesTorque = None
	else:
		outlines = helpers.getjobout(request.session,jobid)
		outlinesTorque = helpers.getjoboutTorque(request.session,jobid)	
	return render_to_response('viewjob.html', {'outlines': outlines, 'outlinesTorque': outlinesTorque},context_instance=RequestContext(request)) 

@login_required
def viewMyjob(request,jobdefid):
	return render_to_response('viewMyjob.html', {'job': JobDef.objects.get(id = jobdefid) } ,context_instance=RequestContext(request)) 


@login_required
def viewnode(request,nodeid):
	if isSlurm(request.session):
		outlines = helpers.getnodeoutSlurm(request.session,nodeid)
	else:
		outlines = helpers.getnodeout(request.session,nodeid)
	return render_to_response('viewnode.html', {'outlines': outlines },context_instance=RequestContext(request)) 
	
@login_required
def listres(request):
	if isSlurm(request.session):
		return render_to_response('listresSlurm.html', {},context_instance=RequestContext(request)) 
	else:
		return render_to_response('listres.html', {'list': helpers.listres(request.session)},context_instance=RequestContext(request) )

def isSlurm(session):
	hostmap =  MAPHOSTS[session['host']]
	return hostmap.has_key('rmtype') and hostmap['rmtype'] == 'slurm'


@login_required
def listjobsTorque(request):
	return listjobs(request)

def listjobs(request,message=None):
	slurm = isSlurm(request.session)
	if slurm:
		listjobs = helpers.listjobsSlurm(request.session)
	else:
		listjobs = helpers.listjobsTorque(request.session)
	c = {'isSlurm': slurm , 'list': listjobs}
	if message:
		c['message'] = message
	return render_to_response('listjobsTorque.html', c,context_instance=RequestContext(request) ) 



@login_required
def listMyjobs(request):
	session = request.session
	return render_to_response('listMyjobs.html', {'list': JobDef.objects.filter(username__exact=session['username'],host__exact=session['host']) },context_instance=RequestContext(request)) 
