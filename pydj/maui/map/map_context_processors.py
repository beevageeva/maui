from settings import MAPHOSTS, MAPLAYOUTS

def auth(request):
	if request.session.has_key('username') and request.session['username']:
		otherhosts = []	
		for h in MAPHOSTS.keys():
			if h!=request.session['host']:
				otherhosts.append(h)
		if request.session.has_key('layout') and request.session['layout']:
			layout = request.session['layout']
		else:
			layout = MAPLAYOUTS[0]
		otherlayouts = []	
		for l in MAPLAYOUTS:
			if l!=layout:
				otherlayouts.append(l)
		return {'username' : request.session['username'], 'host' : request.session['host'] , 'otherhosts' : otherhosts ,'layout': layout + '.html', 'otherlayouts' : otherlayouts}
	return {}
	
