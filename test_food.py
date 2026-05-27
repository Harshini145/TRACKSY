import requests
r = requests.get('http://127.0.0.1:8000/food-spots/nearby?lat=28.6139&lon=77.2090&radius=1000')
print('Status', r.status_code)
try:
    print(r.json())
except Exception:
    print(r.text)
