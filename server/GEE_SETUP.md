# Google Earth Engine Setup Guide

This project integrates with Google Earth Engine (GEE) to provide multi-decadal historical analysis (Landsat) and cloud-masked Sentinel-2 composites. 

## 1. Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (or select an existing one).

## 2. Enable the Earth Engine API

1. In the Google Cloud Console, navigate to **APIs & Services > Library**.
2. Search for "Earth Engine API".
3. Click **Enable**.

## 3. Create a Service Account

1. Navigate to **IAM & Admin > Service Accounts**.
2. Click **Create Service Account**.
3. Provide a name and description, then click **Create and Continue**.
4. (Optional) Grant the service account the "Earth Engine Resource Viewer" role.
5. Click **Done**.

## 4. Generate a JSON Key

1. Find the newly created Service Account in the list and click on it.
2. Go to the **Keys** tab.
3. Click **Add Key > Create new key**.
4. Select **JSON** and click **Create**.
5. The JSON key file will be downloaded to your computer.

## 5. Register the Service Account with Earth Engine

1. Go to the [Earth Engine Sign Up](https://earthengine.google.com/signup/) page (you must have an active Earth Engine account).
2. Register your Google Cloud Project for Earth Engine access [here](https://code.earthengine.google.com/register).
3. Ensure the service account email is added to a registered project or is granted access via IAM.

## 6. Configure the Backend

1. Rename the downloaded JSON file to `gee_key.json`.
2. Move it to the `server/` directory or update `.env` to point to it:
   ```env
   GEE_CREDENTIALS_PATH=/path/to/your/gee_key.json
   GEE_SERVICE_ACCOUNT_EMAIL=your-service-account@your-project.iam.gserviceaccount.com
   GEE_PROJECT_ID=your-project-id
   ```
3. Restart the backend container/server.
