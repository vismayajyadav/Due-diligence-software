"""
Integrated Analysis Module for PE Due Diligence AI Agent

Combines findings from structured and unstructured data analysis modules
to provide a holistic risk assessment.
"""

import numpy as np

# Assuming modules are importable
from .structured_data_analysis.structured_data_analysis_module import StructuredDataAnalysisModule, process_financial_dataframe
from .unstructured_data_analysis.news_analysis_module import NewsAnalysisModule
from .unstructured_data_analysis.interview_analysis_module import InterviewAnalysisModule

class IntegratedAnalysisModule:
    def __init__(self):
        self.structured_analyzer = StructuredDataAnalysisModule()
        self.news_analyzer = NewsAnalysisModule()
        self.interview_analyzer = InterviewAnalysisModule()

    def run_full_analysis(self, financial_data_dict, news_articles=None, interview_transcripts=None):
        """Runs analysis on all available data types and integrates results.

        Args:
            financial_data_dict (dict): Dictionary containing pandas DataFrames for 
                                       balance_sheet, income_statement, cash_flow_statement.
            news_articles (list[str], optional): List of news article texts.
            interview_transcripts (list[str], optional): List of interview transcript texts.

        Returns:
            dict: A comprehensive dictionary containing integrated risk scores,
                  findings from all sources, and supporting evidence.
        """
        all_findings = []
        structured_results = {}
        news_results_list = []
        interview_results_list = []

        # 1. Analyze Structured Data
        if financial_data_dict:
            try:
                structured_results = self.structured_analyzer.analyze_financial_data(financial_data_dict)
                # Add structured findings to the main list
                all_findings.extend(structured_results.get("high_priority_findings", []))
                all_findings.extend(structured_results.get("medium_priority_findings", []))
                all_findings.extend(structured_results.get("low_priority_findings", []))
                print("Structured data analysis completed.")
            except Exception as e:
                print(f"Error during structured data analysis: {e}")
                # Add an error finding
                all_findings.append({
                    "description": "Structured data analysis failed.",
                    "risk_category": "System Error",
                    "risk_score": 0,
                    "evidence": str(e)
                })
        else:
            print("No structured financial data provided.")

        # 2. Analyze Unstructured Data - News Articles
        if news_articles:
            print(f"Analyzing {len(news_articles)} news articles...")
            for i, article in enumerate(news_articles):
                try:
                    news_result = self.news_analyzer.analyze_article(article)
                    news_results_list.append(news_result)
                    # Add findings, marking the source
                    for finding in news_result.get("findings", []):
                        finding["source"] = f"News Article {i+1}"
                        all_findings.append(finding)
                except Exception as e:
                    print(f"Error analyzing news article {i+1}: {e}")
                    all_findings.append({
                        "description": f"News article {i+1} analysis failed.",
                        "risk_category": "System Error",
                        "risk_score": 0,
                        "source": f"News Article {i+1}",
                        "evidence": str(e)
                    })
            print("News article analysis completed.")
        else:
            print("No news articles provided.")

        # 3. Analyze Unstructured Data - Interview Transcripts
        if interview_transcripts:
            print(f"Analyzing {len(interview_transcripts)} interview transcripts...")
            for i, transcript in enumerate(interview_transcripts):
                try:
                    interview_result = self.interview_analyzer.analyze_transcript(transcript)
                    interview_results_list.append(interview_result)
                    # Add findings, marking the source
                    for finding in interview_result.get("findings", []):
                        finding["source"] = f"Interview {i+1}"
                        all_findings.append(finding)
                except Exception as e:
                    print(f"Error analyzing interview transcript {i+1}: {e}")
                    all_findings.append({
                        "description": f"Interview transcript {i+1} analysis failed.",
                        "risk_category": "System Error",
                        "risk_score": 0,
                        "source": f"Interview {i+1}",
                        "evidence": str(e)
                    })
            print("Interview transcript analysis completed.")
        else:
            print("No interview transcripts provided.")

        # 4. Integrate Findings and Calculate Final Scores
        
        # Consolidate findings by category and calculate final scores (e.g., max score per category)
        final_scores = {"Fraud Risk": 0, "Legal Risk": 0, "Revenue Risk": 0, "Management Risk": 0, "System Error": 0}
        categorized_findings = {"Fraud Risk": [], "Legal Risk": [], "Revenue Risk": [], "Management Risk": [], "System Error": []}
        
        for finding in all_findings:
            category = finding.get("risk_category", "Other")
            if category not in final_scores:
                 category = "Other" # Handle unexpected categories
                 if category not in final_scores: final_scores[category] = 0; categorized_findings[category] = []
                 
            score = finding.get("risk_score", 0)
            final_scores[category] = max(final_scores[category], score)
            categorized_findings[category].append(finding)

        # Calculate overall score (e.g., max of primary risk categories)
        overall_score = max(final_scores["Fraud Risk"], final_scores["Legal Risk"], final_scores["Revenue Risk"], final_scores["Management Risk"])

        # Sort findings within categories by score
        for category in categorized_findings:
            categorized_findings[category].sort(key=lambda x: x.get("risk_score", 0), reverse=True)

        # Prepare the final integrated result package
        integrated_results = {
            "overall_risk_score": int(overall_score),
            "risk_scores_by_category": {k: int(v) for k, v in final_scores.items()},
            "findings_by_category": categorized_findings,
            "total_findings_count": len(all_findings),
            "analysis_summary": {
                "structured_data_analyzed": bool(financial_data_dict),
                "news_articles_analyzed": len(news_articles) if news_articles else 0,
                "interviews_analyzed": len(interview_transcripts) if interview_transcripts else 0,
            },
            # Optionally include raw results from sub-modules
            # "raw_structured_results": structured_results,
            # "raw_news_results": news_results_list,
            # "raw_interview_results": interview_results_list
        }

        return integrated_results

# Example Usage
if __name__ == "__main__":
    import pandas as pd
    import os
    import json

    test_data_dir = "/home/ubuntu/pe_due_diligence_agent/test_data"
    output_dir_integrated = "/home/ubuntu/pe_agent_package/test_results/integrated_analysis"
    os.makedirs(output_dir_integrated, exist_ok=True)

    # Load sample structured data
    financial_data_dict_example = None
    try:
        bs_raw = pd.read_csv(f"{test_data_dir}/company_xyz_balance_sheet.csv")
        is_raw = pd.read_csv(f"{test_data_dir}/company_xyz_income_statement.csv")
        cf_raw = pd.read_csv(f"{test_data_dir}/company_xyz_cash_flow_statement.csv")
        bs_proc = process_financial_dataframe(bs_raw)
        is_proc = process_financial_dataframe(is_raw)
        cf_proc = process_financial_dataframe(cf_raw)
        if bs_proc is not None and is_proc is not None and cf_proc is not None:
            financial_data_dict_example = {
                "balance_sheet": bs_proc,
                "income_statement": is_proc,
                "cash_flow_statement": cf_proc
            }
    except FileNotFoundError:
        print(f"Warning: Structured test data not found in {test_data_dir}")
    except Exception as e:
        print(f"Warning: Error loading structured test data: {e}")

    # Sample unstructured data
    sample_news = ["""
    COMPANY XYZ FACES LAWSUIT OVER ACCOUNTING IRREGULARITIES
    Shares plummeted after news broke of a significant lawsuit alleging fraudulent accounting practices and misstatement of earnings. 
    The investigation by regulatory bodies is ongoing. Analysts worry about market share loss due to the scandal and potential fines.
    """]
    sample_interview = ["""
    Interviewer: How confident are you about the revenue projections?
    CEO: Well, frankly, it's challenging. We are confident, but there are risks. The market is perhaps uncertain. However, we see strong growth opportunities. It might be difficult, but we have a robust plan. To be honest, there could be a delay.
    """]

    # Run integrated analysis
    integrator = IntegratedAnalysisModule()
    full_results = integrator.run_full_analysis(financial_data_dict_example, sample_news, sample_interview)

    print("\n--- Integrated Analysis Results ---")
    print(f"Overall Risk Score: {full_results["overall_risk_score"]}")
    print("Risk Scores by Category:", full_results["risk_scores_by_category"])
    print("Total Findings:", full_results["total_findings_count"])
    print("\nFindings Summary:")
    for category, findings in full_results["findings_by_category"].items():
        if findings:
            print(f"\n  {category}:")
            for finding in findings[:3]: # Show top 3 per category
                source = f" (Source: {finding.get(\"source\", \"Structured\")})" if "source" in finding else ""
                print(f"    - {finding["description"]}{source} (Score: {finding["risk_score"]})")

    # Save results
    try:
        with open(f"{output_dir_integrated}/integrated_analysis_summary.json", "w") as f:
             json.dump(full_results, f, indent=4, default=lambda x: int(x) if isinstance(x, np.integer) else float(x) if isinstance(x, np.floating) else None if pd.isna(x) else str(x)) # Added str() for broader compatibility
        print(f"\nSaved integrated results to {output_dir_integrated}/integrated_analysis_summary.json")
    except Exception as e:
        print(f"Error saving integrated results: {e}")

