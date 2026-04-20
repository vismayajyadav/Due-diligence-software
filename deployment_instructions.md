# Deployment Instructions for PE Due Diligence AI Agent Backend

This guide provides instructions for deploying the Flask backend API to cloud platforms like Render and Hugging Face Spaces.

**Prerequisites:**

*   A Git repository (e.g., GitHub, GitLab) containing the project code (`pe_agent_package` content).
*   Accounts on the chosen deployment platform (Render or Hugging Face).

## Option 1: Deploying on Render

Render is a platform that makes it easy to deploy web services, including Dockerized applications.

1.  **Push Code:** Ensure your project code (including the `Dockerfile`, `requirements.txt`, and the `backend` directory) is pushed to your Git repository.
2.  **Create a New Web Service on Render:**
    *   Go to the Render Dashboard and click "New +" > "Web Service".
    *   Connect your Git repository (GitHub/GitLab).
    *   Select the repository containing your project.
3.  **Configure the Service:**
    *   **Name:** Give your service a name (e.g., `pe-agent-backend`).
    *   **Region:** Choose a region close to you or your users.
    *   **Branch:** Select the branch to deploy from (e.g., `main`).
    *   **Runtime:** Select "Docker". Render will automatically detect your `Dockerfile`.
    *   **Root Directory:** Leave blank if `Dockerfile` is in the root, or specify the path if it's nested (e.g., if your repo root contains `pe_agent_package`, and `Dockerfile` is inside that, you might not need to set this if Render detects it correctly relative to the repo root).
    *   **Health Check Path (Optional but Recommended):** Set this to `/` (the index route in `app.py`).
    *   **Port:** Render typically detects the `EXPOSE` instruction in the Dockerfile (5000 in this case). Ensure this matches.
4.  **Environment Variables:**
    *   Click on "Environment".
    *   Add any necessary environment variables from your `.env.sample` (e.g., `FLASK_ENV=production`, `SECRET_KEY=your_generated_secret_key`). **Do not commit your actual secret key to Git.**
5.  **Build and Deploy:**
    *   Click "Create Web Service".
    *   Render will clone your repository, build the Docker image using your `Dockerfile`, and deploy the service.
    *   Monitor the build and deploy logs for any errors.
6.  **Access:** Once deployed, Render will provide you with a public URL (e.g., `https://your-service-name.onrender.com`) where your API will be accessible.

## Option 2: Deploying on Hugging Face Spaces

Hugging Face Spaces can host Docker containers, making it suitable for deploying APIs.

1.  **Push Code:** Ensure your project code is pushed to a Git repository (or you can upload directly to a Hugging Face Space repo).
2.  **Create a New Space on Hugging Face:**
    *   Go to Hugging Face and click "New" > "Space".
    *   Give your Space a name.
    *   Select a license (e.g., Apache 2.0).
    *   Choose "Docker" as the Space SDK.
    *   Select "Blank" template.
    *   Choose hardware (CPU basic should be sufficient initially).
    *   Click "Create Space".
3.  **Add Code to the Space Repository:**
    *   You can clone the Space repository locally, add your project files (including `Dockerfile`, `requirements.txt`, `backend` directory), commit, and push.
    *   Alternatively, use the "Files and versions" tab on the Space page to upload files directly.
    *   **Important:** Ensure your `Dockerfile` and the `backend` directory are in the root of the Space repository.
4.  **Configure Dockerfile (if needed):**
    *   The provided `Dockerfile` should work. Ensure the `EXPOSE 5000` and `CMD` lines are correct. Hugging Face Spaces typically expect the application to run on port 7860 by default for Gradio/Streamlit, but for Docker, it respects the `EXPOSE` instruction. You might need to configure the port mapping if issues arise.
5.  **Secrets (Environment Variables):**
    *   Go to the "Settings" tab of your Space.
    *   Scroll down to "Repository secrets".
    *   Add any necessary secrets (like `SECRET_KEY`). These will be available as environment variables.
6.  **Build and Deploy:**
    *   Hugging Face automatically builds and deploys the Docker container when you push changes or upload files.
    *   Monitor the build logs (accessible via the "Logs" button or link on the Space page) for errors.
7.  **Access:** Your API will be accessible via the Space's URL. Since it's an API, you'll interact with specific endpoints (e.g., `https://your-username-your-space-name.hf.space/api/upload`).

## Important Notes for Production:

*   **Use Gunicorn:** For production deployments on both platforms, modify the `Dockerfile`'s `CMD` to use `gunicorn` instead of the Flask development server for better performance and stability. Add `gunicorn` to `requirements.txt`.
    ```dockerfile
    # Add gunicorn to requirements.txt
    # ... (rest of Dockerfile)
    CMD ["gunicorn", "--bind", "0.0.0.0:5000", "backend.api.app:app"]
    ```
*   **Secret Management:** Use the platform's secret management features (Environment Variables on Render, Repository secrets on Hugging Face) for sensitive information like API keys or `SECRET_KEY`. Do not hardcode them.
*   **Database:** The current API uses in-memory storage for job status. For production, replace this with a persistent database (e.g., PostgreSQL, Redis) and configure the connection via environment variables.
*   **CORS:** If your HTML frontend is hosted on a different domain than the API, you'll need to configure Cross-Origin Resource Sharing (CORS) in your Flask app (e.g., using the `Flask-CORS` extension).
*   **File Storage:** Uploaded files and results are currently stored on the container's filesystem, which is ephemeral. For production, use external storage like AWS S3, Azure Blob Storage, or Render Disks.

These instructions provide a starting point. Refer to the specific documentation of Render and Hugging Face Spaces for more advanced configurations and troubleshooting.
