import requests
from app.services.realtime_service import _get_cdse_token

token = _get_cdse_token()
id = "89e9f4d2-d902-49b9-b05c-226f7917d7f0"

url_cat = f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products({id})/$value"
url_zip = f"https://zipper.dataspace.copernicus.eu/odata/v1/Products({id})/$value"

h = {"Authorization": f"Bearer {token}"}

try:
    with requests.get(url_cat, headers=h, stream=True) as r:
        print("Catalogue GET:", r.status_code)
except Exception as e:
    print("Cat err:", e)

try:
    with requests.get(url_zip, headers=h, stream=True) as r:
        print("Zipper GET:", r.status_code)
except Exception as e:
    print("Zip err:", e)
