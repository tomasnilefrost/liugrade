import httplib2
from bs4 import BeautifulSoup
from urllib import urlencode

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
		if col[0].findAll('b'): # a completed course is bold
			data = {'course_code' : col[0].findAll('b')[0].renderContents().strip().replace('*', ''), 'course' : col[1].renderContents().strip(), 'points' : col[2].renderContents().strip(), 'grade' : col[3].renderContents().strip(), 'date' : col[4].renderContents().strip(), 'course_moments' : {}}
			courseData.append(data)
		else:
			key = col[0].renderContents().strip().replace('\xc2\xa0', '') # a course moment starts with two white spaces
			data = {'points' : col[2].renderContents().strip(), 'grade' : col[3].renderContents().strip(), 'date' : col[4].renderContents().strip()}
			courseData[-1]['course_moments'][key] = data

print courseData



