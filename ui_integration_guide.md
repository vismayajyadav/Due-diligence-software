# UI Integration Guide for PE Due Diligence AI Agent Backend

This guide explains how a frontend web interface (e.g., built with HTML, CSS, and JavaScript) can interact with the Flask backend API for the PE Due Diligence AI Agent.

**API Base URL:** Assume your backend API is deployed and accessible at `YOUR_API_BASE_URL` (e.g., `https://your-service-name.onrender.com` or `https://your-username-your-space-name.hf.space`).

## Core Interaction Flow

1.  **File Upload:** The user selects financial statements (CSV), news articles (TXT), and interview transcripts (TXT) via an HTML form.
2.  **Initiate Analysis:** The frontend JavaScript collects these files and sends them as `multipart/form-data` to the backend API endpoint: `POST YOUR_API_BASE_URL/api/upload`.
3.  **Receive Job ID:** The backend accepts the files, starts the analysis process in the background, and immediately responds with a unique `job_id`.
4.  **Poll for Status:** The frontend uses the `job_id` to periodically check the analysis status by sending requests to: `GET YOUR_API_BASE_URL/api/status/<job_id>`.
5.  **Fetch Results:** Once the status endpoint indicates `"status": "completed"`, the frontend retrieves the analysis results by sending a request to: `GET YOUR_API_BASE_URL/api/results/<job_id>`.
6.  **Display Results:** The frontend parses the JSON results and displays the risk scores, findings, and other relevant information to the user.

## JavaScript Examples (using Fetch API)

These examples assume you have HTML input elements for file selection (e.g., `<input type="file" id="balanceSheetFile">`, `<input type="file" id="newsFile">`, etc.) and elements to display status and results.

### 1. Uploading Files and Starting Analysis

```javascript
async function startAnalysis() {
    const balanceSheetInput = document.getElementById("balanceSheetFile");
    const incomeStatementInput = document.getElementById("incomeStatementFile");
    const cashFlowInput = document.getElementById("cashFlowFile");
    const newsInput = document.getElementById("newsFile");
    const interviewInput = document.getElementById("interviewFile");

    const formData = new FormData();

    // Append files if they exist
    if (balanceSheetInput.files.length > 0) {
        formData.append("balance_sheet", balanceSheetInput.files[0]);
    }
    if (incomeStatementInput.files.length > 0) {
        formData.append("income_statement", incomeStatementInput.files[0]);
    }
    if (cashFlowInput.files.length > 0) {
        formData.append("cash_flow", cashFlowInput.files[0]);
    }
    if (newsInput.files.length > 0) {
        formData.append("news", newsInput.files[0]);
    }
    if (interviewInput.files.length > 0) {
        formData.append("interview", interviewInput.files[0]);
    }

    // Check if any files were added
    if ([...formData.entries()].length === 0) {
        alert("Please select at least one file to analyze.");
        return;
    }

    const apiUrl = "YOUR_API_BASE_URL/api/upload"; // Replace with your actual API URL
    const statusElement = document.getElementById("statusDisplay"); // Element to show status

    statusElement.textContent = "Uploading files and starting analysis...";

    try {
        const response = await fetch(apiUrl, {
            method: "POST",
            body: formData, // FormData handles multipart/form-data encoding
        });

        if (response.status === 202) { // 202 Accepted indicates background processing started
            const data = await response.json();
            const jobId = data.job_id;
            statusElement.textContent = `Analysis started. Job ID: ${jobId}. Checking status...`;
            // Start polling for status
            pollStatus(jobId);
        } else {
            const errorData = await response.json();
            statusElement.textContent = `Error starting analysis: ${errorData.error || response.statusText}`;
            console.error("Upload failed:", errorData);
        }
    } catch (error) {
        statusElement.textContent = "Network error or API unreachable.";
        console.error("Error uploading files:", error);
    }
}
```

### 2. Polling for Analysis Status

```javascript
function pollStatus(jobId) {
    const apiUrl = `YOUR_API_BASE_URL/api/status/${jobId}`; // Replace with your actual API URL
    const statusElement = document.getElementById("statusDisplay");
    const resultsElement = document.getElementById("resultsDisplay"); // Element to show results

    const intervalId = setInterval(async () => {
        try {
            const response = await fetch(apiUrl);
            if (!response.ok) {
                console.error("Status check failed:", response.statusText);
                statusElement.textContent = `Error checking status (Job ID: ${jobId}).`;
                clearInterval(intervalId); // Stop polling on error
                return;
            }

            const data = await response.json();
            statusElement.textContent = `Job ${jobId}: ${data.status}`;

            if (data.status === "completed") {
                clearInterval(intervalId); // Stop polling
                statusElement.textContent = `Job ${jobId}: Completed. Fetching results...`;
                // Fetch the results
                fetchResults(jobId);
            } else if (data.status === "failed") {
                clearInterval(intervalId); // Stop polling
                statusElement.textContent = `Job ${jobId}: Failed. Error: ${data.error}`;
                console.error("Analysis failed:", data.error);
            } else {
                // Status is still "pending" or "processing", continue polling
                statusElement.textContent = `Job ${jobId}: ${data.status}...`;
            }
        } catch (error) {
            console.error("Error polling status:", error);
            statusElement.textContent = `Error polling status (Job ID: ${jobId}). Check network/API.`;
            clearInterval(intervalId); // Stop polling on network error
        }
    }, 5000); // Poll every 5 seconds (adjust as needed)
}
```

### 3. Fetching and Displaying Results

```javascript
async function fetchResults(jobId) {
    const apiUrl = `YOUR_API_BASE_URL/api/results/${jobId}`; // Replace with your actual API URL
    const statusElement = document.getElementById("statusDisplay");
    const resultsElement = document.getElementById("resultsDisplay"); // Assumes an element (e.g., a <pre> or <div>) to display results

    try {
        const response = await fetch(apiUrl);
        if (!response.ok) {
            const errorData = await response.json();
            statusElement.textContent = `Error fetching results: ${errorData.error || response.statusText}`;
            console.error("Failed to fetch results:", errorData);
            return;
        }

        const results = await response.json();
        statusElement.textContent = `Job ${jobId}: Results received.`;

        // Display the results (example: showing raw JSON in a <pre> tag)
        resultsElement.textContent = JSON.stringify(results, null, 2);

        // --- OR --- 

        // Process and display results in a more user-friendly format
        // Example: Display overall score and high-priority findings
        /*
        let displayHtml = `<h2>Analysis Results (Job ID: ${jobId})</h2>`;
        displayHtml += `<p><strong>Overall Risk Score: ${results.overall_risk_score}</strong></p>`;
        displayHtml += `<h3>Risk Scores by Category:</h3><ul>`;
        for (const [category, score] of Object.entries(results.risk_scores_by_category)) {
            displayHtml += `<li>${category}: ${score}</li>`;
        }
        displayHtml += `</ul>`;

        displayHtml += `<h3>High Priority Findings:</h3>`;
        const highFindings = results.findings_by_category["Fraud Risk"].concat(
                             results.findings_by_category["Legal Risk"],
                             results.findings_by_category["Revenue Risk"],
                             results.findings_by_category["Management Risk"]
                           ).filter(f => f.risk_score >= 75).sort((a, b) => b.risk_score - a.risk_score);

        if (highFindings.length > 0) {
            displayHtml += `<ul>`;
            highFindings.forEach(finding => {
                displayHtml += `<li><strong>${finding.risk_category} (Score: ${finding.risk_score}):</strong> ${finding.description} <br> <small>Evidence: ${finding.evidence || 'N/A'} ${finding.source ? '(Source: ' + finding.source + ')' : ''}</small></li>`;
            });
            displayHtml += `</ul>`;
        } else {
            displayHtml += `<p>No high-priority findings.</p>`;
        }
        resultsElement.innerHTML = displayHtml;
        */

    } catch (error) {
        statusElement.textContent = "Error processing or displaying results.";
        console.error("Error fetching/displaying results:", error);
    }
}
```

## CORS (Cross-Origin Resource Sharing)

If your frontend HTML/JS files are served from a different domain than your backend API (which is common), you **must** configure CORS on the Flask backend. Otherwise, the browser will block requests from the frontend to the API for security reasons.

Install the `Flask-CORS` extension:

```bash
pip install Flask-CORS
```

Add it to your `requirements.txt`.

Then, initialize it in your `app.py`:

```python
# In backend/api/app.py

from flask import Flask # ... other imports
from flask_cors import CORS # Import CORS

# ... (rest of imports)

app = Flask(__name__)
CORS(app) # Enable CORS for all routes and origins (adjust for production)

# ... (rest of app configuration and routes)
```

For production, you should configure `CORS` more restrictively, allowing only the specific domain(s) where your frontend is hosted.

Example: `CORS(app, resources={r"/api/*": {"origins": "https://your-frontend-domain.com"}})`

This guide provides the basic steps for integrating a frontend with the provided Flask API. You will need to adapt the JavaScript code to match your specific HTML structure and desired user experience.
