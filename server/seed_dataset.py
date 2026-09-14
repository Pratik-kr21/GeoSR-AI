import httpx
import asyncio

async def seed_data():
    base_url = "http://localhost:8000/api/v1"
    
    print("1. Creating a new GeoSR-AI Project...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        project_data = {
            "name": "Sentinel-2 Validation",
            "location": "Chandigarh Area",
            "description": "Seeded project using test_input.tif"
        }
        res = await client.post(f"{base_url}/projects/", json=project_data)
        if res.status_code != 200:
            print(f"Failed to create project: {res.text}")
            return
        
        project = res.json()
        project_id = project['id']
        print(f"✅ Created Project ID: {project_id}")
        
        print("\n2. Uploading test_input.tif to MinIO and Database...")
        file_path = "data/test_input.tif"
        
        # We need a longer timeout because the file is 964MB
        async with httpx.AsyncClient(timeout=300.0) as upload_client:
            with open(file_path, "rb") as f:
                files = {"file": ("test_input.tif", f, "image/tiff")}
                upload_res = await upload_client.post(f"{base_url}/projects/{project_id}/upload", files=files)
                
                if upload_res.status_code != 200:
                    print(f"Failed to upload file: {upload_res.text}")
                    return
                
                file_metadata = upload_res.json()
                file_id = file_metadata['file_id']
                object_name = file_metadata['object_name']
                print(f"✅ Upload successful. File ID: {file_id}")
                print(f"   Rasterio extracted CRS: {file_metadata['crs']}")
                print(f"   Rasterio extracted Bands: {file_metadata['bands']}")
                
        print("\n3. Triggering Super-Resolution Celery Background Task...")
        sr_res = await client.post(f"{base_url}/projects/{project_id}/super-resolution?object_name={object_name}")
        if sr_res.status_code != 200:
            print(f"Failed to trigger SR: {sr_res.text}")
            return
            
        job_data = sr_res.json()
        job_id = job_data['job_id']
        print(f"✅ SR Job Queued. Job ID: {job_id}")
        
        print("\n4. Polling Job Status...")
        for _ in range(20):
            status_res = await client.get(f"{base_url}/projects/jobs/{job_id}")
            if status_res.status_code == 200:
                status_data = status_res.json()
                print(f"   Current Status: {status_data['status']}")
                if status_data['status'] == 'completed':
                    print("🎉 Background processing finished successfully!")
                    break
                elif status_data['status'] == 'failed':
                    print("❌ Background processing failed.")
                    break
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(seed_data())
