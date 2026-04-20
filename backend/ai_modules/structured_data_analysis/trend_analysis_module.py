"""
Trend Analysis Module for PE Due Diligence AI Agent

Analyzes historical financial trends to detect potential risks.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller

class TrendAnalysisModule:
    def __init__(self):
        pass

    def _check_stationarity(self, timeseries):
        """Check if a time series is stationary using Augmented Dickey-Fuller test."""
        if len(timeseries) < 4: # ADF test requires minimum observations
            return False, "Insufficient data for stationarity test"
        try:
            result = adfuller(timeseries)
            p_value = result[1]
            # If p-value <= 0.05, we reject the null hypothesis (series is stationary)
            return p_value <= 0.05, f"ADF p-value: {p_value:.3f}"
        except Exception as e:
            print(f"Error during stationarity check: {e}")
            return False, f"Error: {e}"

    def analyze_trends(self, financial_data):
        """Analyze key financial trends for potential risk indicators."""
        findings = []
        bs = financial_data["balance_sheet"]
        is_data = financial_data["income_statement"]
        cf = financial_data["cash_flow_statement"]
        years = is_data.columns.tolist()
        
        if len(years) < 3: # Need at least 3 years for meaningful trend analysis
            print("Warning: Insufficient historical data for trend analysis (need >= 3 years).")
            return findings

        # 1. Revenue Growth Trend
        revenue = is_data.loc["Revenue"].values
        revenue_growth = np.diff(revenue) / revenue[:-1] * 100
        if np.any(revenue_growth < -10): # Significant decline
            year_index = np.where(revenue_growth < -10)[0][0]
            findings.append({
                "description": f"Significant revenue decline detected in year {years[year_index]} ({revenue_growth[year_index]:.1f}%).",
                "risk_category": "Revenue Risk",
                "risk_score": 70,
                "evidence": f"Revenue growth rates: {revenue_growth}"
            })
        elif np.mean(revenue_growth) < 5 and np.std(revenue_growth) < 3: # Stagnant growth
             findings.append({
                "description": "Stagnant revenue growth observed over the period.",
                "risk_category": "Revenue Risk",
                "risk_score": 50,
                "evidence": f"Average revenue growth: {np.mean(revenue_growth):.1f}%"
            })

        # 2. Profitability Trends (Net Income vs Revenue)
        net_income = is_data.loc["Net Income"].values
        net_income_growth = np.diff(net_income) / net_income[:-1] * 100
        
        # Check if net income growth lags significantly behind revenue growth
        if len(net_income_growth) == len(revenue_growth):
            growth_diff = revenue_growth - net_income_growth
            if np.mean(growth_diff) > 15: # If revenue grows >15% faster than net income on average
                findings.append({
                    "description": "Net income growth consistently lagging behind revenue growth.",
                    "risk_category": "Revenue Risk",
                    "risk_score": 65,
                    "evidence": f"Avg Revenue Growth: {np.mean(revenue_growth):.1f}%, Avg NI Growth: {np.mean(net_income_growth):.1f}%"
                })

        # 3. Cash Flow Trends (Operating Cash Flow vs Net Income)
        op_cash_flow = cf.loc["Net Cash Provided by Operating Activities"].values
        cf_ni_ratio = op_cash_flow / net_income
        if np.mean(cf_ni_ratio) < 0.9:
            findings.append({
                "description": f"Operating cash flow consistently lower than net income (Avg Ratio: {np.mean(cf_ni_ratio):.2f}).",
                "risk_category": "Fraud Risk",
                "risk_score": 70,
                "evidence": f"CF/NI Ratios: {cf_ni_ratio}"
            })
        # Check for declining trend in CF/NI ratio
        if len(cf_ni_ratio) > 1 and cf_ni_ratio[0] < cf_ni_ratio[-1]: # If latest ratio is lower than earliest
             findings.append({
                "description": "Declining trend in Cash Flow to Net Income ratio.",
                "risk_category": "Fraud Risk",
                "risk_score": 60,
                "evidence": f"CF/NI Ratios: {cf_ni_ratio}"
            })

        # 4. Asset Growth vs Revenue Growth
        total_assets = bs.loc["Total Assets"].values
        asset_growth = np.diff(total_assets) / total_assets[:-1] * 100
        if len(asset_growth) == len(revenue_growth):
             growth_diff_assets = asset_growth - revenue_growth
             if np.mean(growth_diff_assets) > 20: # If assets grow >20% faster than revenue
                 findings.append({
                    "description": "Total assets growing significantly faster than revenue.",
                    "risk_category": "Fraud Risk", # Could indicate capitalized expenses or poor asset utilization
                    "risk_score": 65,
                    "evidence": f"Avg Asset Growth: {np.mean(asset_growth):.1f}%, Avg Revenue Growth: {np.mean(revenue_growth):.1f}%"
                })

        # 5. Seasonal Decomposition (Example on Revenue - requires monthly/quarterly data ideally)
        # This is illustrative; annual data has limited seasonality.
        # if len(revenue) >= 4: # Need enough data points
        #     try:
        #         # Assuming annual data, period=1 makes little sense, but for demonstration:
        #         decomposition = seasonal_decompose(revenue, model=\"additive\", period=max(1, min(len(revenue)//2, 1)))
        #         trend = decomposition.trend
        #         seasonal = decomposition.seasonal
        #         residual = decomposition.resid
        #         # Analyze residuals for anomalies or trend changes
        #         if np.std(residual[~np.isnan(residual)]) > np.std(revenue) * 0.2: # High residual variance
        #              findings.append({
        #                 "description": "High volatility in revenue after accounting for trend/seasonality.",
        #                 "risk_category": "Revenue Risk",
        #                 "risk_score": 55,
        #                 "evidence": "High residual variance in seasonal decomposition."
        #             })
        #     except Exception as e:
        #         print(f"Warning: Seasonal decomposition failed: {e}")

        # 6. Stationarity Check (Example on Net Income)
        is_stationary, stationarity_evidence = self._check_stationarity(net_income)
        if not is_stationary and "Error" not in stationarity_evidence:
            findings.append({
                "description": "Net Income trend appears non-stationary, suggesting potential instability or strong trend.",
                "risk_category": "Revenue Risk",
                "risk_score": 50,
                "evidence": stationarity_evidence
            })

        return findings

    def plot_trends(self, financial_data, output_dir):
        """Generate plots for key financial trends."""
        try:
            bs = financial_data["balance_sheet"]
            is_data = financial_data["income_statement"]
            cf = financial_data["cash_flow_statement"]
            years = is_data.columns.tolist()

            if len(years) < 2:
                print("Insufficient data to plot trends.")
                return

            plt.figure(figsize=(12, 8))
            
            # Plot Revenue, Net Income, Operating Cash Flow
            plt.plot(years, is_data.loc["Revenue"].values, marker=\"o\", label="Revenue")
            plt.plot(years, is_data.loc["Net Income"].values, marker=\"s\", label="Net Income")
            plt.plot(years, cf.loc["Net Cash Provided by Operating Activities"].values, marker=\"^", label="Operating Cash Flow")
            
            plt.title("Key Financial Trends")
            plt.xlabel("Year")
            plt.ylabel("Amount ($)")
            plt.legend()
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(f"{output_dir}/key_financial_trends.png")
            plt.close()
            print(f"Saved plot: {output_dir}/key_financial_trends.png")

        except Exception as e:
            print(f"Error generating trend plot: {e}")

# Example Usage
if __name__ == "__main__":
    # Assumes financial_ratio_analyzer.py is available for process_financial_dataframe
    from financial_ratio_analyzer import process_financial_dataframe
    
    test_data_dir = "/home/ubuntu/pe_due_diligence_agent/test_data"
    output_dir_trends = "/home/ubuntu/pe_agent_package/test_results/trends"
    os.makedirs(output_dir_trends, exist_ok=True)

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

            trend_analyzer = TrendAnalysisModule()
            trend_findings = trend_analyzer.analyze_trends(financial_data_dict)
            trend_analyzer.plot_trends(financial_data_dict, output_dir_trends)

            print("\n--- Trend Analysis Findings ---")
            if trend_findings:
                for finding in trend_findings:
                    print(f"- {finding["description"]} (Risk: {finding["risk_category"]}, Score: {finding["risk_score"]})")
            else:
                print("No significant trend anomalies detected.")
        else:
            print("Could not process financial dataframes.")

    except FileNotFoundError:
        print(f"Error: Test data files not found in {test_data_dir}")
    except ImportError:
         print("Error: Ensure statsmodels and seaborn are installed (`pip install statsmodels seaborn`)")
    except Exception as e:
        print(f"An error occurred during example execution: {e}")

