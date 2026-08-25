import urllib.request
import json
import base64

PASSWORD = 'Ji99 n7Dz o9mf Evan F93w cYL3'

# 1. Tenta listar autores publicos do site para descobrir o slug de usuario
print("[*] Consultando usuários públicos do site...")
try:
    req = urllib.request.Request('https://DemoStore.com.br/wp-json/wp/v2/users', headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        users = json.loads(resp.read().decode())
        print("Usuários públicos encontrados:")
        for u in users:
            print(f"  - ID: {u.get('id')}, Name: {u.get('name')}, Slug: {u.get('slug')}")
            
            # Testa autenticação com esse slug
            auth = base64.b64encode(f"{u.get('slug')}:{PASSWORD}".encode('utf-8')).decode('utf-8')
            req_auth = urllib.request.Request('https://DemoStore.com.br/wp-json/wp/v2/users/me', headers={'Authorization': f'Basic {auth}', 'User-Agent': 'Mozilla/5.0'})
            try:
                with urllib.request.urlopen(req_auth, timeout=5) as r_auth:
                    d_auth = json.loads(r_auth.read().decode())
                    print(f"    ===> SUCESSO TOTAL! O login exato é: '{u.get('slug')}'")
                    break
            except Exception as e:
                print(f"    -> Falhou para slug '{u.get('slug')}': {e}")
except Exception as e:
    print(f"[!] Erro ao listar usuários públicos: {e}")
