"""
Anomaly Detection Engine for PE Due Diligence AI Agent

Uses statistical methods and machine learning to identify unusual patterns
in financial data that might indicate risks.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

class AnomalyDetectionEngine:
    def __init__(self, contamination=\"auto\"):
        """Initialize the anomaly detection engine.

        Args:
            contamination (float or \"auto\"): The expected proportion of outliers
                                               in the data set. Used by Isolation Forest.
        """
        self.contamination = contamination
        self.scaler = StandardScaler()

    def _prepare_data_for_ml(self, financial_data):
        """Prepares and scales financial data for machine learning models."""
        # Example: Combine key metrics from different statements into a single DataFrame
        # This needs careful feature engineering based on available data
        bs = financial_data["balance_sheet"]
        is_data = financial_data["income_statement"]
        cf = financial_data["cash_flow_statement"]
        years = bs.columns.tolist()

        # Select key metrics
        metrics = {
            "Revenue": is_data.loc["Revenue"],
            "Net Income": is_data.loc["Net Income"],
            "Operating Cash Flow": cf.loc["Net Cash Provided by Operating Activities"],
            "Total Assets": bs.loc["Total Assets"],
            "Total Liabilities": bs.loc["Total Liabilities"],
            "Accounts Receivable": bs.loc["Accounts Receivable"],
            "Inventory": bs.loc["Inventory"]
        }
        
        df = pd.DataFrame(metrics).T # Transpose to have years as rows
        df.columns = years
        df = df.T # Transpose back to have metrics as columns

        # Handle potential NaN values (e.g., fill with mean or median)
        df = df.fillna(df.median())

        # Scale the data
        scaled_data = self.scaler.fit_transform(df)
        return pd.DataFrame(scaled_data, index=df.index, columns=df.columns)

    def detect_anomalies_statistical(self, financial_data, ratios):
        """Detect anomalies using statistical methods (e.g., Z-score on ratios)."""
        findings = []
        years = list(ratios["gross_margin"].keys()) # Get available years
        if not years:
            return findings
        
        latest_year = years[0]

        # Example: Z-score for Days Sales Outstanding (DSO)
        dso_values = [ratios["days_sales_outstanding"][y] for y in years if y in ratios["days_sales_outstanding"] and not np.isnan(ratios["days_sales_outstanding"][y])]
        if len(dso_values) > 1:
            mean_dso = np.mean(dso_values)
            std_dso = np.std(dso_values)
            if std_dso > 0:
                latest_dso = ratios["days_sales_outstanding"][latest_year]
                z_score_dso = (latest_dso - mean_dso) / std_dso
                if abs(z_score_dso) > 2.0: # Threshold for anomaly (e.g., 2 standard deviations)
                    findings.append({
                        "description": f"Anomalous Days Sales Outstanding (DSO) detected ({latest_dso:.1f} days).",
                        "risk_category": "Fraud Risk",
                        "risk_score": 60 + min(40, abs(z_score_dso) * 10),
                        "evidence": f"DSO Z-Score: {z_score_dso:.2f} (Mean: {mean_dso:.1f}, StdDev: {std_dso:.1f})"
                    })

        # Example: Check for large year-over-year changes in key ratios
        if len(years) > 1:
            prev_year = years[1]
            for ratio_name in ["gross_margin", "net_profit_margin", "current_ratio"]:
                 if latest_year in ratios[ratio_name] and prev_year in ratios[ratio_name] and not np.isnan(ratios[ratio_name][latest_year]) and not np.isnan(ratios[ratio_name][prev_year]):
                    change = (ratios[ratio_name][latest_year] - ratios[ratio_name][prev_year]) / ratios[ratio_name][prev_year]
                    if abs(change) > 0.3: # Threshold for significant change (e.g., 30%)
                        findings.append({
                            "description": f"Significant year-over-year change in {ratio_name.replace(\"_\", \" \").title()} ({change:.1%}).",
                            "risk_category": "Revenue Risk" if "margin" in ratio_name else "Legal Risk",
                            "risk_score": 50 + min(50, abs(change) * 100),
                            "evidence": f"{ratio_name.replace(\"_\", \" \").title()} changed from {ratios[ratio_name][prev_year]:.3f} to {ratios[ratio_name][latest_year]:.3f}"
                        })

        return findings

    def detect_anomalies_ml(self, financial_data):
        """Detect anomalies using machine learning (Isolation Forest)."""
        findings = []
        try:
            scaled_data = self._prepare_data_for_ml(financial_data)
            if scaled_data.empty or scaled_data.shape[0] < 2:
                 print("Warning: Insufficient data for ML anomaly detection.")
                 return findings

            model = IsolationForest(contamination=self.contamination, random_state=42)
            predictions = model.fit_predict(scaled_data)
            
            # Anomalies are marked as -1
            anomaly_indices = np.where(predictions == -1)[0]
            anomaly_scores = model.decision_function(scaled_data)

            for idx in anomaly_indices:
                year = scaled_data.index[idx]
                score = anomaly_scores[idx]
                # Map score to 0-100 range (approximate)
                risk_score = max(0, min(100, 50 + (-score * 100)))
                findings.append({
                    "description": f"Potential anomaly detected in financial metrics for year {year} using Isolation Forest.",
                    "risk_category": "Fraud Risk", # ML anomalies often point to complex fraud
                    "risk_score": int(risk_score),
                    "evidence": f"Isolation Forest anomaly score: {score:.3f} for year {year}"
                })
                
        except Exception as e:
            print(f"Error during ML anomaly detection: {e}")
            # Optionally add a finding indicating the error
            # findings.append({"description": "ML anomaly detection failed.", ...})

        return findings

    def run_detection(self, financial_data, ratios):
        """Run both statistical and ML anomaly detection methods."""
        statistical_findings = self.detect_anomalies_statistical(financial_data, ratios)
        ml_findings = self.detect_anomalies_ml(financial_data)
        
        # Combine and potentially de-duplicate findings
        all_findings = statistical_findings + ml_findings
        # Simple de-duplication based on description (can be improved)
        unique_findings = []
        seen_descriptions = set()
        for finding in all_findings:
            if finding["description"] not in seen_descriptions:
                unique_findings.append(finding)
                seen_descriptions.add(finding["description"])
                
        return unique_findings

# Example Usage (similar structure to financial_ratio_analyzer.py)
if __name__ == "__main__":
    # Assumes financial_ratio_analyzer.py is in the same directory or path
    from financial_ratio_analyzer import FinancialRatioAnalyzer, process_financial_dataframe
    
    test_data_dir = "/home/ubuntu/pe_due_diligence_agent/test_data"
    try:
        balance_sheet_raw = pd.read_csv(f"{test_data_dir}/company_xyz_balance_sheet.csv")
        income_statement_raw = pd.read_csv(f"{test_data_dir}/company_xyz_income_statement.csv")
        cash_flow_statement_raw = pd.read_csv(f"{test_data_dir}/company_xyz_cash_flow_statement.csv")

        bs_processed = process_financial_dataframe(balance_sheet_raw)
        is_processed = process_financial_dataframe(income_statement_raw)
        cf_processed = process_financial_dataframe(cash_flow_statement_raw)

        if bs_processed is not None and is_processed is not None and cf_processed is not None:
            financial_data_dict = {
                "balance_sheet": bs_processed,
                "income_statement": is_processed,
                "cash_flow_statement": cf_processed
            }

            # Calculate ratios first
            ratio_analyzer = FinancialRatioAnalyzer()
            calculated_ratios = ratio_analyzer.calculate_ratios(financial_data_dict)

            # Run anomaly detection
            anomaly_engine = AnomalyDetectionEngine()
            anomaly_findings = anomaly_engine.run_detection(financial_data_dict, calculated_ratios)

            print("\n--- Anomaly Detection Findings ---")
            if anomaly_findings:
                for finding in anomaly_findings:
                    print(f"- {finding["description"]} (Risk: {finding["risk_category"]}, Score: {finding["risk_score"]})")
            else:
                print("No significant anomalies detected.")
        else:
             print("Could not process financial dataframes.")

    except FileNotFoundError:
        print(f"Error: Test data files not found in {test_data_dir}")
    except ImportError:
         print("Error: Ensure scikit-learn is installed (`pip install scikit-learn`)")
    except Exception as e:
        print(f"An error occurred during example execution: {e}")

