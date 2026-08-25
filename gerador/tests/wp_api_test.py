import urllib.request
import json
import base64

def try_auth(username, password):
    auth = base64.b64encode(f"{username}:{password}".encode('utf-8')).decode('utf-8')
    headers = {'Authorization': f'Basic {auth}', 'User-Agent': 'Mozilla/5.0'}
    url = 'https://DemoStore.com.br/wp-json/wp/v2/users/me'
    print(f"Testing username '{username}'...")
    try:
        req = urllib.request.Request(url, headers=headers)
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read().decode())
        print(f"  -> SUCCESS! Logged in as: {data.get('name')}")
        return True
    except urllib.error.HTTPError as e:
        print(f"  -> Failed ({e.code}) - {e.read().decode()}")
        return False
    except Exception as e:
        print(f"  -> Error: {e}")
        return False

pass_spaces = 'Jp3w sZQC wJOy HsGp KUO0 yOr6'
try_auth('lucas.dev@DemoStore.com.br', pass_spaces)
