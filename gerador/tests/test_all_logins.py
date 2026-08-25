import urllib.request
import json
import base64

PASSWORD = 'Ji99 n7Dz o9mf Evan F93w cYL3'
LOGINS = [
    'Lucas',
    'lucas',
    'LUCAS',
    'lucas.dev@DemoStore.com.br',
    'lucas@DemoStore.com.br',
    'comercial@DemoStore.com.br',
    'lucas.dev',
    'lucas_DemoStore',
    'lucas.DemoStore'
]

url = 'https://DemoStore.com.br/wp-json/wp/v2/users/me'

for login in LOGINS:
    auth = base64.b64encode(f"{login}:{PASSWORD}".encode('utf-8')).decode('utf-8')
    headers = {'Authorization': f'Basic {auth}', 'User-Agent': 'Mozilla/5.0'}
    print(f"Testing login '{login}'...")
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            print(f"\n============================================================")
            print(f"[===> SUCESSO TOTAL!] Logado como: '{data.get('name')}' (ID: {data.get('id')}) com login '{login}'")
            print(f"============================================================\n")
            break
    except urllib.error.HTTPError as e:
        print(f"  -> {e.code}: {e.read().decode()}")
    except Exception as e:
        print(f"  -> Error: {e}")
