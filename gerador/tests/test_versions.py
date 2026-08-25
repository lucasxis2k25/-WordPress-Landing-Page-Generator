import urllib.request
import json

CK = 'ck_784c7e773683c8a0ffc5cdf6d27cd3c1f1ea2485'
CS = 'cs_659c08187c016bd05fbb7cff64139db7e850af05'

urls = [
    f"https://DemoStore.com.br/wp-json/wc/v3/products?consumer_key={CK}&consumer_secret={CS}",
    f"https://DemoStore.com.br/wp-json/wc/v2/products?consumer_key={CK}&consumer_secret={CS}",
    f"https://DemoStore.com.br/wp-json/wc/v1/products?consumer_key={CK}&consumer_secret={CS}"
]

for url in urls:
    print(f"Testing {url[:65]}...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            print(f"  ===> SUCCESS! Returned {len(data)} items")
            break
    except urllib.error.HTTPError as e:
        print(f"  -> Error {e.code}: {e.read().decode()}")
    except Exception as e:
        print(f"  -> Exception: {e}")
