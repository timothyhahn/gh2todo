import requests
import yaml
import sys

## Functions
def get_from(url):
    try:
        r = requests.get(url, auth=(github_username, github_password))
        return r.json()
    except Exception as e:
        print e
        print('Please check your credentials')
        sys.exit('Connection Failed')

def post_to(url, payload):
    try:
        r = requests.post(url, data=payload)
        return r.json()
    except Exception as e:
        print e
        print('Please check your credentials')
        sys.exit('Connection Failed')

## Get Credentials
with open ('credentials.yml', 'r') as credentials:
    credentials_string = credentials.read()

credentials_dict =  yaml.load(credentials_string)

github_username = credentials_dict['github_username']
github_password = credentials_dict['github_password']

todoist_username = credentials_dict['todoist_username']
todoist_password = credentials_dict['todoist_password']

todoist_project_name = 'githubissues'


## Get Open Issues
issues = get_from('https://api.github.com/issues')

for issue in issues:
    print '{0} - {1} - {2}'.format(issue['repository']['name'], issue['number'], issue['title'])

## Login to Todoist
payload = {'email': todoist_username, 'password': todoist_password}
token = post_to('https://todoist.com/API/login', payload)['token']

## Get Projects
payload = {'token': token}
projects = post_to('https://todoist.com/API/getProjects', payload)
project = filter(lambda p: p['name'] == todoist_project_name, projects)

## Create Project if it doesn't exist
project_id = 0
if project:
    project_id = project[0]['id']
else: 
    payload = {'token': token, 'name': todoist_project_name}
    project = post_to('https://todoist.com/API/addProject', payload)
    project_id = project['id']

## Get Uncompleted items from Todoist
payload = {'token': token, 'project_id': project_id}
uncompleted_tasks = post_to('https://todoist.com/API/getUncompletedItems', payload)

## If the issues on github isn't on todoist, add it
for issue in issues:
    issue_name = '{0} - {1} - {2}'.format(issue['repository']['name'], issue['number'], issue['title'])
    if next((task for task in uncompleted_tasks if task['content'] == issue_name), None):
        print '{0} already exists'.format(issue_name)
    else:
        print 'creating {0}'.format(issue_name)
        payload = {'project_id': project_id, 'token': token, 'content': issue_name}
        post_to('https://todoist.com/API/addItem', payload)

completed_issues = get_from('https://api.github.com/user/issues?state=closed')

## If the task is on todoist and complete on github, complete it
for task in uncompleted_tasks:
    task_name = task['content']
    if next((issue for issue in completed_issues if '{0} - {1} - {2}'.format(issue['repository']['name'], issue['number'], issue['title']) == task_name), None):
        print 'completing {0}'.format(task_name)
        payload = {'token': token, 'ids': str([task['id']])}
        post_to('https://todoist.com/API/completeItems', payload)

