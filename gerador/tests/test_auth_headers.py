import urllib.request
import json
import base64

USERNAME = 'Lucas'
PASSWORD = 'Ji99 n7Dz o9mf Evan F93w cYL3'

auth_plain = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode('utf-8')).decode('utf-8')
auth_nospace = base64.b64encode(f"{USERNAME}:{PASSWORD.replace(' ', '')}".encode('utf-8')).decode('utf-8')

test_headers = [
    {'Authorization': f'Basic {auth_plain}'},
    {'Authorization': f'Basic {auth_nospace}'},
    {'X-HTTP-Authorization': f'Basic {auth_plain}'},
    {'X-HTTP-Authorization': f'Basic {auth_nospace}'}
]

url = 'https://DemoStore.com.br/wp-json/wp/v2/users/me'

for i, h in enumerate(test_headers):
    h['User-Agent'] = 'Mozilla/5.0'
    print(f"Testing header option {i+1}...")
    try:
        req = urllib.request.Request(url, headers=h)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            print(f"  ===> SUCCESS! Logged in as: {data.get('name')}")
            break
    except urllib.error.HTTPError as e:
        print(f"  -> Failed ({e.code}) - {e.read().decode()}")
    except Exception as e:
        print(f"  -> Error: {e}")
