import datetime
import requests
import execjs
import json
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

USER = {
    'username': '',
    'password': ''
}

FOLDER = {
    'root_id': '',
    'path': ''
}

NAME_LIST = [

]

BARK_CONFIG = {
    'server': '',
    'key': '',
    'icon': ''
}

PAN_CAS_URL= 'http://pan.dlut.edu.cn/cas'
PAN_AUTH_URL = 'http://pan.dlut.edu.cn/v1/auth/md5_sso'
PAN_FOLDER_LIST_URL = 'http://pan.dlut.edu.cn/v1/fileops/list_folder'
DLUT_CAS_URL = 'https://sso.dlut.edu.cn/cas/login?service=http://pan.dlut.edu.cn/cas'
BARK_URL = 'https://{0}/{1}/weekly-report-stats/{2}/?group=weekly-report-stats&icon={3}'


session = requests.session()

response = session.get(PAN_CAS_URL, allow_redirects=True)
login_html = response.text
soup = BeautifulSoup(login_html, 'html.parser')

with open('des.js', 'r', encoding='utf-8') as f:
    js = f.read()

context = execjs.compile(js)

lt = soup.find(id="lt")['value']
execution = soup.find("input", {"name": "execution"})['value']
_eventId = soup.find("input", {"name": "_eventId"})['value']
rsa = context.call('strEnc', USER['username'] + USER['password'] + lt, '1', '2', '3')

form = {
    'rsa': rsa,
    'ul': len(USER['username']),
    'pl': len(USER['password']),
    'sl': 0,
    'lt': lt,
    'execution': execution,
    '_eventId': _eventId
}

response = session.post(url=DLUT_CAS_URL, data=form)

parsed_url = urlparse(response.url)
query_params = parse_qs(parsed_url.query)
query_params = {key: values[0] for key, values in query_params.items()}
query_string = urlencode(query_params)
unparsed_url = urlunparse(urlparse(PAN_AUTH_URL)._replace(query=query_string))

response = session.post(unparsed_url)
token = json.loads(response.text)['token']

FOLDER['token'] = token

query_string = urlencode(FOLDER)
unparsed_url = urlunparse(urlparse(PAN_FOLDER_LIST_URL)._replace(query=query_string))

response = requests.post(unparsed_url)
j = json.loads(response.text)
file_list = [item['name'] for item in j]

to_remove = []
not_submitted = []
match_failed = []

for file_name in file_list:
    hit = False
    for name_pattern in NAME_LIST:
        if re.search(name_pattern, file_name):
            to_remove.append(name_pattern)
            hit = True
            break
    if not hit:
        match_failed.append(file_name)

for name in NAME_LIST:
    if name not in to_remove:
        not_submitted.append(name)

not_submitted = [f"{i + 1}.{name.replace('.+', '%')}" for i, name in enumerate(not_submitted)]
match_failed = [f"{i + 1}.{name.replace('.+', '%')}" for i, name in enumerate(match_failed)]

result = ''

if not_submitted:
    result = 'Unsubmitted:\n' + '\n'.join(not_submitted)
if match_failed:
    result += '\n' + 'Match failed:\n' + '\n'.join(match_failed)

push_url = BARK_URL.format(BARK_CONFIG['server'], BARK_CONFIG['key'], result, BARK_CONFIG['icon'])
requests.get(push_url)