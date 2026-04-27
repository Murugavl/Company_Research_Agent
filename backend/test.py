import urllib.request, json
from urllib.error import HTTPError
req = urllib.request.Request('http://localhost:8000/api/research/stream', data=json.dumps({'user_message': 'OpenAI', 'company_name': '', 'session_id': 'test1', 'chat_history': [{'role': 'user', 'content': 'OpenAI'}], 'current_plan': None}).encode('utf-8'), headers={'Content-Type': 'application/json'})
try:
    print(urllib.request.urlopen(req).read().decode('utf-8'))
except HTTPError as e:
    print(e.read().decode('utf-8'))
