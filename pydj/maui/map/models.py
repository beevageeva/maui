from django.db import models
from django.core.validators import RegexValidator

class JobDef(models.Model):
	username = models.CharField(max_length=100,blank=True)
	jobid = models.CharField(max_length=20,null=True,blank=True)
	host = models.CharField(max_length=20,blank=True)
	scriptFilename = models.CharField(max_length=100,validators=[RegexValidator(regex="\S+")])
	jobName = models.CharField(max_length=20,validators=[RegexValidator(regex="\S+")])
	numNodes = models.CharField(max_length=20,validators=[RegexValidator(regex="\d+", message="Numero")])
	procsNode = models.CharField(max_length=20,validators=[RegexValidator(regex="\d+")])
	queue = models.CharField(max_length=20,validators=[RegexValidator(regex="\S+")])
	mem = models.CharField(max_length=20,null=True,blank=True,validators=[RegexValidator(regex="\d+")])
	walltime = models.CharField(max_length=20,null=True,blank=True,validators=[RegexValidator(regex="\d{2}:\d{2}:\d{2}", message="Formato dd:hh:mm" )])
	outfile = models.CharField(max_length=20,validators=[RegexValidator(regex="[\S]+")])
	errorfile = models.CharField(max_length=20,validators=[RegexValidator(regex="\S+")])
	resid = models.CharField(max_length=20,null=True,blank=True,validators=[RegexValidator(regex="[.\w]+")])
	execcode = models.TextField(max_length=4000)
