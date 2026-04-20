# Main Flask application file for PE Due Diligence AI Agent API

import os
import sys
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import uuid
import json
import pandas as pd
import threading

# Add project root to Python path to allow importing modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

# Import AI modules (adjust path if necessary)
try:
    from ai_modules.integrated_analysis_module import IntegratedAnalysisModule, process_financial_dataframe
except ImportError as e:
    print(f"Error importing AI modules: {e}. Ensure modules are in the correct path and dependencies are installed.")
    # Define dummy classes/functions if import fails, so app can still start
    class IntegratedAnalysisModule:
        def run_full_analysis(self, *args, **kwargs):
            return {"error": "AI Module not loaded", "details": str(e)}
    def process_financial_dataframe(df):
        return df # Dummy function

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = os.path.join(project_root, "uploads")
RESULTS_FOLDER = os.path.join(project_root, "results")
ALLOWED_EXTENSIONS = {"txt", "pdf", "csv", "xlsx", "xls"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["RESULTS_FOLDER"] = RESULTS_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024 # 32 MB limit

# Ensure upload and results directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# In-memory storage for job status and results (Replace with DB in production)
analysis_jobs = {}

# Initialize the analysis module
analysis_integrator = IntegratedAnalysisModule()

def allowed_file(filename):
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Helper Function for Background Analysis ---
def run_analysis_background(job_id, file_paths):
    """Runs the analysis in a separate thread."""
    print(f"Starting analysis for job {job_id}...")
    analysis_jobs[job_id]["status"] = "processing"
    
    financial_data_dict = {}
    news_articles = []
    interview_transcripts = []
    
    try:
        # Process uploaded files
        bs_df, is_df, cf_df = None, None, None
        for file_type, filepath in file_paths.items():
            if not filepath:
                continue
            print(f"Processing {file_type}: {filepath}")
            if file_type == "balance_sheet" and filepath.endswith(".csv"):
                bs_df = process_financial_dataframe(pd.read_csv(filepath))
            elif file_type == "income_statement" and filepath.endswith(".csv"):
                is_df = process_financial_dataframe(pd.read_csv(filepath))
            elif file_type == "cash_flow" and filepath.endswith(".csv"):
                cf_df = process_financial_dataframe(pd.read_csv(filepath))
            # TODO: Add processing for XLSX/XLS using pandas/openpyxl/xlrd
            # TODO: Add processing for PDF/TXT (requires text extraction logic)
            elif file_type == "news" and filepath.endswith(".txt"):
                 with open(filepath, "r", encoding="utf-8") as f:
                     news_articles.append(f.read())
            elif file_type == "interview" and filepath.endswith(".txt"):
                 with open(filepath, "r", encoding="utf-8") as f:
                     interview_transcripts.append(f.read())

        # Prepare financial data dict if all statements are present
        if bs_df is not None and is_df is not None and cf_df is not None:
            financial_data_dict = {
                "balance_sheet": bs_df,
                "income_statement": is_df,
                "cash_flow_statement": cf_df
            }
        elif bs_df is not None or is_df is not None or cf_df is not None:
             print("Warning: Not all financial statements (BS, IS, CF) provided in CSV format. Structured analysis may be incomplete.")
             # Allow analysis even with partial data, module should handle it
             financial_data_dict = {
                "balance_sheet": bs_df,
                "income_statement": is_df,
                "cash_flow_statement": cf_df
            }

        # Run the integrated analysis
        results = analysis_integrator.run_full_analysis(
            financial_data_dict if financial_data_dict else None, 
            news_articles if news_articles else None, 
            interview_transcripts if interview_transcripts else None
        )
        
        # Save results to a file
        result_filepath = os.path.join(app.config["RESULTS_FOLDER"], f"{job_id}_results.json")
        with open(result_filepath, "w") as f:
            # Convert numpy types for JSON serialization
            json.dump(results, f, indent=4, default=lambda x: int(x) if isinstance(x, np.integer) else float(x) if isinstance(x, np.floating) else None if pd.isna(x) else str(x))
        
        analysis_jobs[job_id]["status"] = "completed"
        analysis_jobs[job_id]["result_file"] = result_filepath
        print(f"Analysis completed for job {job_id}. Results saved to {result_filepath}")

    except Exception as e:
        print(f"Error during analysis for job {job_id}: {e}")
        analysis_jobs[job_id]["status"] = "failed"
        analysis_jobs[job_id]["error"] = str(e)

# --- API Routes ---

@app.route("/")
def index():
    # Simple index route, maybe serve a static file or API info later
    return jsonify({"message": "PE Due Diligence AI Agent API is running."}) 

@app.route("/api/upload", methods=["POST"])
def upload_files():
    """Handles file uploads for analysis."""
    if not request.files:
        return jsonify({"error": "No files part in the request"}), 400

    job_id = str(uuid.uuid4())
    job_folder = os.path.join(app.config["UPLOAD_FOLDER"], job_id)
    os.makedirs(job_folder, exist_ok=True)
    
    uploaded_files = {
        "balance_sheet": None,
        "income_statement": None,
        "cash_flow": None,
        "news": [],
        "interview": []
    }
    file_paths = {
        "balance_sheet": None,
        "income_statement": None,
        "cash_flow": None,
        "news": None, # For simplicity, handle one news/interview file for now via API
        "interview": None
    }

    # Process known file types from form fields
    file_keys = ["balance_sheet", "income_statement", "cash_flow", "news", "interview"]
    for key in file_keys:
        if key in request.files:
            file = request.files[key]
            if file and file.filename != "" and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(job_folder, filename)
                file.save(filepath)
                uploaded_files[key] = filename
                file_paths[key] = filepath # Store path for analysis
            elif file and file.filename != "":
                 print(f"File type not allowed: {file.filename}")
                 # Optionally return error or just ignore

    # TODO: Handle multiple news/interview files if needed (e.g., request.files.getlist(\"news_files\"))

    if not any(uploaded_files.values()):
        return jsonify({"error": "No valid files uploaded or file types not allowed"}), 400

    # Store job info (in memory)
    analysis_jobs[job_id] = {
        "status": "pending",
        "uploaded_files": uploaded_files,
        "result_file": None,
        "error": None
    }

    # Start analysis in background thread
    analysis_thread = threading.Thread(target=run_analysis_background, args=(job_id, file_paths))
    analysis_thread.start()

    return jsonify({"message": "Files uploaded successfully. Analysis started.", "job_id": job_id}), 202

@app.route("/api/status/<job_id>", methods=["GET"])
def get_status(job_id):
    """Checks the status of an analysis job."""
    job = analysis_jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job ID not found"}), 404
    
    response = {"job_id": job_id, "status": job["status"]}
    if job["status"] == "failed":
        response["error"] = job["error"]
    elif job["status"] == "completed":
        response["result_url"] = f"/api/results/{job_id}" # Provide URL to get results
        
    return jsonify(response), 200

@app.route("/api/results/<job_id>", methods=["GET"])
def get_results(job_id):
    """Retrieves the analysis results for a completed job."""
    job = analysis_jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job ID not found"}), 404
    
    if job["status"] != "completed":
        return jsonify({"error": "Analysis not completed or failed", "status": job["status"]}), 400
        
    result_file = job.get("result_file")
    if not result_file or not os.path.exists(result_file):
        return jsonify({"error": "Result file not found"}), 500
        
    try:
        # Send the JSON file content
        return send_from_directory(app.config["RESULTS_FOLDER"], os.path.basename(result_file), as_attachment=False)
    except Exception as e:
        print(f"Error sending result file for job {job_id}: {e}")
        return jsonify({"error": "Could not retrieve results"}), 500

if __name__ == "__main__":
    # Run in debug mode for development (change for production)
    app.run(host="0.0.0.0", port=5000, debug=True)

