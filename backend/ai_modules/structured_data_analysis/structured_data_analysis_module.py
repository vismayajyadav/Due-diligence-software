"""
Structured Data Analysis Module for PE Due Diligence AI Agent

Integrates ratio analysis, anomaly detection, and trend analysis for
structured financial data.
"""

import pandas as pd
import numpy as np

# Assuming the modules are in the same directory or accessible via sys.path
from .financial_ratio_analyzer import FinancialRatioAnalyzer, process_financial_dataframe
from .anomaly_detection_engine import AnomalyDetectionEngine
from .trend_analysis_module import TrendAnalysisModule

class StructuredDataAnalysisModule:
    def __init__(self):
        self.ratio_analyzer = FinancialRatioAnalyzer()
        self.anomaly_engine = AnomalyDetectionEngine()
        self.trend_analyzer = TrendAnalysisModule()

    def analyze_financial_data(self, financial_data):
        """Performs comprehensive analysis on structured financial data.

        Args:
            financial_data (dict): Dictionary containing pandas DataFrames for 
                                   balance_sheet, income_statement, cash_flow_statement.
                                   DataFrames should have years as columns and accounts as index.

        Returns:
            dict: A dictionary containing analysis results, including risk scores,
                  findings, and calculated ratios.
        """
        if not all(k in financial_data for k in ["balance_sheet", "income_statement", "cash_flow_statement"]):
            raise ValueError("Financial data dictionary must contain balance_sheet, income_statement, and cash_flow_statement.")

        # 1. Calculate Financial Ratios
        try:
            ratios = self.ratio_analyzer.calculate_ratios(financial_data)
        except Exception as e:
            print(f"Error during ratio calculation: {e}")
            ratios = {} # Continue analysis even if ratios fail partially

        # 2. Analyze Ratios for Risks
        try:
            ratio_findings = self.ratio_analyzer.analyze_ratios(ratios)
        except Exception as e:
            print(f"Error during ratio analysis: {e}")
            ratio_findings = []

        # 3. Detect Anomalies (Statistical & ML)
        try:
            anomaly_findings = self.anomaly_engine.run_detection(financial_data, ratios)
        except Exception as e:
            print(f"Error during anomaly detection: {e}")
            anomaly_findings = []

        # 4. Analyze Trends
        try:
            trend_findings = self.trend_analyzer.analyze_trends(financial_data)
        except Exception as e:
            print(f"Error during trend analysis: {e}")
            trend_findings = []

        # 5. Combine and Score Findings
        all_findings = ratio_findings + anomaly_findings + trend_findings
        
        # Simple de-duplication based on description
        unique_findings = []
        seen_descriptions = set()
        for finding in all_findings:
            # Ensure finding is a dict and has 'description'
            if isinstance(finding, dict) and "description" in finding:
                 if finding["description"] not in seen_descriptions:
                    unique_findings.append(finding)
                    seen_descriptions.add(finding["description"])
            else:
                print(f"Warning: Skipping invalid finding format: {finding}")

        # Categorize findings by risk level
        high_priority_findings = [f for f in unique_findings if f.get("risk_score", 0) >= 75]
        medium_priority_findings = [f for f in unique_findings if 50 <= f.get("risk_score", 0) < 75]
        low_priority_findings = [f for f in unique_findings if f.get("risk_score", 0) < 50]

        # Calculate risk scores by category (taking the max score in each category)
        fraud_risk_score = 0
        legal_risk_score = 0
        revenue_risk_score = 0
        
        for finding in unique_findings:
            score = finding.get("risk_score", 0)
            category = finding.get("risk_category", "Other")
            if category == "Fraud Risk":
                fraud_risk_score = max(fraud_risk_score, score)
            elif category == "Legal Risk":
                legal_risk_score = max(legal_risk_score, score)
            elif category == "Revenue Risk":
                revenue_risk_score = max(revenue_risk_score, score)
            # Add handling for 'Other' if needed

        # Calculate overall risk score (e.g., max of categories or weighted average)
        overall_risk_score = max(fraud_risk_score, legal_risk_score, revenue_risk_score)

        # Prepare final results dictionary
        results = {
            "overall_risk_score": int(overall_risk_score),
            "risk_categories": {
                "Fraud Risk": int(fraud_risk_score),
                "Legal Risk": int(legal_risk_score),
                "Revenue Risk": int(revenue_risk_score)
            },
            "high_priority_findings": sorted(high_priority_findings, key=lambda x: x.get("risk_score", 0), reverse=True),
            "medium_priority_findings": sorted(medium_priority_findings, key=lambda x: x.get("risk_score", 0), reverse=True),
            "low_priority_findings": sorted(low_priority_findings, key=lambda x: x.get("risk_score", 0), reverse=True),
            "all_findings_count": len(unique_findings),
            "financial_ratios": ratios # Include calculated ratios for reference
        }

        return results

# Example Usage
if __name__ == "__main__":
    test_data_dir = "/home/ubuntu/pe_due_diligence_agent/test_data"
    output_dir_main = "/home/ubuntu/pe_agent_package/test_results/structured_analysis"
    os.makedirs(output_dir_main, exist_ok=True)
    
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

            structured_module = StructuredDataAnalysisModule()
            analysis_results = structured_module.analyze_financial_data(financial_data_dict)

            print("\n--- Structured Analysis Results ---")
            print(f"Overall Risk Score: {analysis_results["overall_risk_score"]}")
            print("Risk Categories:", analysis_results["risk_categories"])
            print("\nHigh Priority Findings:")
            for finding in analysis_results["high_priority_findings"]:
                 print(f"- {finding["description"]} (Score: {finding["risk_score"]})")
            print("\nMedium Priority Findings:")
            for finding in analysis_results["medium_priority_findings"]:
                 print(f"- {finding["description"]} (Score: {finding["risk_score"]})")
                 
            # Save results to file
            import json
import os
            with open(f"{output_dir_main}/structured_analysis_summary.json", "w") as f:
                # Convert numpy types for JSON serialization if necessary
                json.dump(analysis_results, f, indent=4, default=lambda x: int(x) if isinstance(x, np.integer) else float(x) if isinstance(x, np.floating) else None if pd.isna(x) else x)
            print(f"\nSaved detailed results to {output_dir_main}/structured_analysis_summary.json")

            # Optionally, generate trend plots via the trend module instance
            structured_module.trend_analyzer.plot_trends(financial_data_dict, output_dir_main)

        else:
            print("Could not process financial dataframes.")

    except FileNotFoundError:
        print(f"Error: Test data files not found in {test_data_dir}")
    except ImportError as e:
         print(f"Error: Missing dependency - {e}. Ensure all required packages are installed.")
    except Exception as e:
        print(f"An error occurred during example execution: {e}")

