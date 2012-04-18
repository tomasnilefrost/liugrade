import httplib2
from bs4 import BeautifulSoup
from urllib import urlencode

def strip_content(elem):
	stripped = elem.renderContents().strip()
	stripped = stripped.replace('*', '')
	stripped = stripped.replace('\xc2\xa0', '')
	return stripped

http = httplib2.Http()
url = 'https://www3.student.liu.se/portal/login'
resp, content = http.request(url)
post_data = {}
for field in BeautifulSoup(content).findAll('input'):
	if field.has_key('name'):
		post_data[field['name']] = field['value']


post_data['user'] = ''
post_data['pass'] = ''

post_data['redirect_url'] = '/portal/sv/portal/studieresultat/'
post_data['redirect'] = '1'

resp, content =  http.request(url, "POST", body=urlencode(post_data))

soup = BeautifulSoup(content).findAll('table')[4] # fifth table
courseData = []
for row in soup.findAll("tr"):
	col = row.findAll("td")
	if (len(col) == 5):
		if col[0].findAll('b'): # a course is bold
			data = {'course_code' : strip_content(col[0].findAll('b')[0]), 'course' : strip_content(col[1]), 'points' : strip_content(col[2]), 'grade' : strip_content(col[3]), 'date' : strip_content(col[4])}#, 'course_moments' : {}}
			courseData.append(data)
		else: # otherwise its a course moment
			key = strip_content(col[0]) 
			if ('course_moments' not in courseData[-1]):
				courseData[-1].update({'course_moments' : { } })
			data = {'points' : strip_content(col[2]), 'grade' : strip_content(col[3]), 'date' : strip_content(col[4])}
			courseData[-1]['course_moments'][key] = data

print courseData




