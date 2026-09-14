import httpx
import asyncio

async def test():
    url = "http://localhost:8000/api/v1/projects/1/upload"
    file_path = "data/test_input.tif"

    with open(file_path, "rb") as f:
        files = {"file": ("test_input.tif", f, "image/tiff")}
        async with httpx.AsyncClient(timeout=None) as client:
            response = await client.post(url, files=files)
            print(response.status_code)
            print(response.json())

if __name__ == "__main__":
    asyncio.run(test())
