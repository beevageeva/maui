from django import forms
from settings import MAPHOSTS
import models


class LoginForm(forms.Form):
	username = forms.CharField(max_length=100)
	password = forms.CharField(widget=forms.PasswordInput(render_value=False))
	host = forms.ChoiceField(choices=map(lambda x: (x,x), MAPHOSTS.keys()))

class SubmitJobForm(forms.ModelForm):
	class Meta:
		model = models.JobDef
		widgets = {'queue': forms.Select} 
