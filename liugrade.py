import httplib2
import operator
import json
from bs4 import BeautifulSoup
from urllib import urlencode
from config import * # pass & pwd variables and so on
import smtplib
import string

def strip_content(elem):
	stripped = elem.renderContents().strip()
	stripped = stripped.replace('*', '')
	stripped = stripped.replace('\xc2\xa0', '')
	return stripped

def format_course(code, info):
	output_string = code + ": " + info['course'] + " grade: " + info['grade'] + " points: " + info['points'] + " date: " + info['date'] + "\n"
	if 'course_moments' in info:
		for key in info['course_moments']:
			output_string += "\t" + key + " grade: " + info['course_moments'][key]['grade'] + " points: " + info['course_moments'][key]['points'] + " date: " + info['course_moments'][key]['date'] + "\n"
	return output_string

old_dict = {}
try:
	f = open(config_dump_filename, 'r')
	content = f.read()
	old_dict = json.loads(content)
	f.close()
except:
	# we will simply compare with an empty dictionary of the "old" courses
	pass


# Bad practice, should add the certificate to use validation
http = httplib2.Http(disable_ssl_certificate_validation=True)
url = 'https://www3.student.liu.se/portal/login'
resp, content = http.request(url)
post_data = {}
for field in BeautifulSoup(content).findAll('input'):
	if field.has_key('name'):
		post_data[field['name']] = field['value']


post_data['user'] = config_username
post_data['pass'] = config_password

post_data['redirect_url'] = '/portal/sv/portal/studieresultat/'
post_data['redirect'] = '1'

resp, content =  http.request(url, "POST", body=urlencode(post_data))

soup = BeautifulSoup(content).findAll('table')[4] # fifth table
course_data = []
for row in soup.findAll("tr"):
	col = row.findAll("td")
	if (len(col) == 5):
		if col[0].findAll('b'): # a course is bold
			data = { 'key' : strip_content(col[0].findAll('b')[0]), 'data' : {} }
			data['data'] = {'course' : strip_content(col[1]), 'points' : strip_content(col[2]), 'grade' : strip_content(col[3]), 'date' : strip_content(col[4])}
			course_data.append(data)
		else: # otherwise its a course moment
			key = strip_content(col[0]) 
			if ('course_moments' not in course_data[-1]['data']):
				course_data[-1]['data'].update({'course_moments' : { } })
			data = {'points' : strip_content(col[2]), 'grade' : strip_content(col[3]), 'date' : strip_content(col[4])}
			course_data[-1]['data']['course_moments'][key] = data

# convert to dict
course_dict = { }
for x in course_data:
	course_dict.update({x['key'] : x['data']})

# list of new courses added
new_course = [course for course in course_dict if course not in old_dict]
# we will format a mail string
mail_str = ""
if (len(new_course) != 0):
	mail_str = "New courses added:\n"
	# done alphabetically
	for x in sorted(new_course):
		mail_str += format_course(x, course_dict[x])
		# copy the new courses to the old dict to compare individually
		old_dict.update({x : course_dict[x]})
	mail_str += "\n"

# check for changes in the existing courses (for instance added course moments), output shall also be sorted
for x in sorted(course_dict.keys()):
	if 'course_moments' not in course_dict[x] and 'course_moments' in old_dict[x]:
		mail_str += "Course " + x + " has been finished...\n"
		mail_str += format_course(x, course_dict[x])
	elif 'course_moments' in course_dict[x] and 'course_moments' in old_dict[x]:
		if len(course_dict[x]['course_moments']) > len(old_dict[x]['course_moments']):
			mail_str += "Course " + x + " has been updated...\n"
			mail_str += format_course(x, course_dict[x])

# we have produced output, thus we shall mail the user and update our dump file
if (mail_str != ""):
	f = open(config_dump_filename, 'w')
	f.write(json.dumps(course_dict))
	f.close()
	body = string.join((
			"From: %s" % config_email_from,
			"To: %s" % config_email_to,
			"Subject: %s" % config_email_subject ,
			"",
			mail_str
			), "\r\n")
	server = smtplib.SMTP(config_email_host)
	server.sendmail(config_email_from, [config_email_to], body)
	server.quit()
