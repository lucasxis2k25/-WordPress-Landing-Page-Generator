import urllib.request
import json
import base64

PASSWORD = 'Jp3w sZQC wJOy HsGp KUO0 yOr6'
USERNAMES = ['lucas', 'lucas.dev', 'lucasdev', 'admin', 'DemoStore', 'comercial', 'desenvolvimento', 'sell-parts']

for username in USERNAMES:
    auth = base64.b64encode(f"{username}:{PASSWORD}".encode('utf-8')).decode('utf-8')
    headers = {'Authorization': f'Basic {auth}', 'User-Agent': 'Mozilla/5.0'}
    url = 'https://DemoStore.com.br/wp-json/wp/v2/users/me'
    print(f"Testing username '{username}'...")
    try:
        req = urllib.request.Request(url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=5)
        data = json.loads(resp.read().decode())
        print(f"  ===> SUCCESS! Authenticated as: {data.get('name')} (username: {username})")
        break
    except urllib.error.HTTPError as e:
        print(f"  -> Failed ({e.code})")
    except Exception as e:
        print(f"  -> Error: {e}")
