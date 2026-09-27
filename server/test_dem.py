import requests, json

client_id = "sh-30017d61-4f73-4e64-a064-499ceaa3d0a7"
client_secret = "ZD30wEkSuogt7EBl2nScvBiTEDvrZfWA"

# get token
resp = requests.post(
    "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
    data={"grant_type": "client_credentials", "client_id": client_id, "client_secret": client_secret}
)
token = resp.json()["access_token"]

def test_dem(instance):
    payload = {
        "input": {
            "bounds": {"bbox": [76,30,77,31], "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"}},
            "data": [{"type": "dem", "dataFilter": {"demInstance": instance}}] if instance else [{"type": "dem"}]
        },
        "output": {"width": 10, "height": 10, "responses": [{"identifier": "default", "format": {"type": "image/tiff"}}]},
        "evalscript": "//VERSION=3\nfunction setup(){return {input:['DEM'],output:{bands:1,sampleType:'FLOAT32'}};}function evaluatePixel(sample){return [sample.DEM];}"
    }
    r = requests.post("https://sh.dataspace.copernicus.eu/api/v1/process", headers={"Authorization": f"Bearer {token}"}, json=payload)
    print(f"{instance or 'DEFAULT'}: {r.status_code}")
    if r.status_code != 200:
        print(r.text)

test_dem("COPERNICUS_30")
test_dem("COPERNICUS_90")
test_dem("MAPZEN")
