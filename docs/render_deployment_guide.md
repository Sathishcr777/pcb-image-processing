# Cloud Deployment Guide: Deploying to Render

This guide outlines how to deploy the **PCB AI Inspection & Photometric AOI Suite** to [Render](https://render.com) using the included Docker configuration.

---

## 📋 Overview of Deployment Assets

The following files are configured for Render deployment:

1. **`Dockerfile`**:
   - Uses `python:3.11-slim` with system OpenCV dependencies (`libgl1`, `libglib2.0-0`, `curl`).
   - Pre-installs lightweight **PyTorch CPU wheels** to prevent CUDA bloat and avoid memory limits on cloud builders.
   - Binds dynamically to Render's injected `$PORT` (`sh -c 'uvicorn server.main:app --host 0.0.0.0 --port ${PORT:-8000}'`).
2. **`.dockerignore`**:
   - Excludes large files (e.g. `PCB-Photometric-AOI-Suite-v4.0-Complete.zip` ~317MB, virtual environments, caches) for fast build uploads.
3. **`render.yaml`**:
   - Blueprint configuration defining the Docker Web Service, free/starter plan, and health check on `/health`.

---

## 🚀 Step-by-Step Deployment Instructions

### Step 1: Commit and Push Changes to GitHub

Ensure all deployment files are committed and pushed to your remote GitHub repository (`main` branch):

```bash
git add .dockerignore Dockerfile render.yaml
git commit -m "Configure Render cloud deployment"
git push origin main
```

---

### Step 2: Deploy on Render

There are two easy methods to deploy on Render:

#### Method A: Blueprint Deployment (Recommended — 1 Click)

1. Log in to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** in the top navigation bar and select **Blueprint**.
3. Connect your GitHub repository (`Sathishcr777/pcb-image-processing` or your fork).
4. Render will automatically read `render.yaml` and configure:
   - **Service Name**: `pcb-photometric-aoi-suite`
   - **Runtime**: `Docker`
   - **Health Check**: `/health`
5. Click **Apply**. Render will trigger the build and deploy automatically.

#### Method B: Manual Web Service Deployment

1. In [Render Dashboard](https://dashboard.render.com), click **New +** &rarr; **Web Service**.
2. Select your GitHub repository.
3. Fill in the following settings:
   - **Name**: `pcb-photometric-aoi-suite` (or your choice)
   - **Region**: Choose the closest region (e.g. `Oregon (US West)` or `Frankfurt (EU Central)`)
   - **Language / Runtime**: **Docker**
   - **Dockerfile Path**: `./Dockerfile`
   - **Docker Context**: `.`
   - **Instance Type**: **Free** (or Starter)
4. Under **Advanced**:
   - **Health Check Path**: `/health`
   - Add Environment Variables:
     - `PCB_AOI_ENV` = `production`
     - `PCB_AOI_REQUIRE_API_KEY` = `0`
     - `PCB_AOI_USE_DEPTH_MODEL` = `0`
5. Click **Create Web Service**.

---

### Step 3: Monitor Build & Verify

During the build process:
- Render pulls the base image and system dependencies.
- PyTorch CPU wheels install quickly (~180MB vs 2.5GB CUDA).
- Uvicorn launches on `0.0.0.0:$PORT`.
- Render pings `/health` and marks the service **Live**.

Your deployment URL will look like:
```text
https://pcb-photometric-aoi-suite.onrender.com
```

---

### 🌐 Live Public Endpoints

Once deployed, you can access all suite tools directly via your public Render URL:

- **Live Inspection Dashboard**: `https://<YOUR-RENDER-APP>.onrender.com/`
- **Photometric 3D Studio**: `https://<YOUR-RENDER-APP>.onrender.com/photometric-studio`
- **Photometric Stereo Analysis**: `https://<YOUR-RENDER-APP>.onrender.com/photometric`
- **X-Ray Inspection Studio**: `https://<YOUR-RENDER-APP>.onrender.com/xray-studio`
- **3D Point Cloud View**: `https://<YOUR-RENDER-APP>.onrender.com/3d-view`
- **Audit History**: `https://<YOUR-RENDER-APP>.onrender.com/audit-history`
- **API Health Check**: `https://<YOUR-RENDER-APP>.onrender.com/health`

---

### 💾 Note on Persistent Storage (Optional)

- On Render Free Tier, the container filesystem is ephemeral (resets on restart).
- If you upgrade to a Render paid instance (Starter $7/mo), you can attach a **Persistent Disk** mounted at `/app/server/audit` and `/app/server/reference` to retain custom golden boards and ISO audit logs permanently.
