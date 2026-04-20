"""
Financial Ratio Analyzer for PE Due Diligence AI Agent

Calculates various financial ratios to identify potential risks.
"""

import pandas as pd
import numpy as np

class FinancialRatioAnalyzer:
    def __init__(self):
        pass

    def calculate_ratios(self, financial_data):
        """Calculate key financial ratios from processed financial data."""
        bs = financial_data["balance_sheet"]
        is_data = financial_data["income_statement"]
        cf = financial_data["cash_flow_statement"]
        
        years = bs.columns.tolist()
        ratios = {}

        # Initialize ratio dictionaries
        ratio_names = [
            "gross_margin", "net_profit_margin", "return_on_assets", "return_on_equity",
            "current_ratio", "quick_ratio", "cash_ratio",
            "asset_turnover", "inventory_turnover", "receivables_turnover", "days_sales_outstanding",
            "debt_to_equity", "interest_coverage",
            "cash_flow_to_net_income", "free_cash_flow_margin",
            "days_sales_in_receivables_index", "gross_margin_index", "asset_quality_index",
            "sales_growth_index", "depreciation_index", "sga_index", "leverage_index"
        ]
        for name in ratio_names:
            ratios[name] = {}

        for year in years:
            try:
                # Profitability ratios
                ratios["gross_margin"][year] = is_data.loc["Gross Profit", year] / is_data.loc["Revenue", year]
                ratios["net_profit_margin"][year] = is_data.loc["Net Income", year] / is_data.loc["Revenue", year]
                ratios["return_on_assets"][year] = is_data.loc["Net Income", year] / bs.loc["Total Assets", year]
                ratios["return_on_equity"][year] = is_data.loc["Net Income", year] / bs.loc["Total Stockholders\" Equity", year]

                # Liquidity ratios
                ratios["current_ratio"][year] = bs.loc["Total Current Assets", year] / bs.loc["Total Current Liabilities", year]
                ratios["quick_ratio"][year] = (bs.loc["Total Current Assets", year] - bs.loc["Inventory", year]) / bs.loc["Total Current Liabilities", year]
                ratios["cash_ratio"][year] = bs.loc["Cash and Cash Equivalents", year] / bs.loc["Total Current Liabilities", year]

                # Efficiency ratios
                ratios["asset_turnover"][year] = is_data.loc["Revenue", year] / bs.loc["Total Assets", year]
                ratios["inventory_turnover"][year] = is_data.loc["Cost of Goods Sold", year] / bs.loc["Inventory", year]
                ratios["receivables_turnover"][year] = is_data.loc["Revenue", year] / bs.loc["Accounts Receivable", year]
                ratios["days_sales_outstanding"][year] = 365 / ratios["receivables_turnover"][year]

                # Leverage ratios
                ratios["debt_to_equity"][year] = bs.loc["Total Liabilities", year] / bs.loc["Total Stockholders\" Equity", year]
                # Interest coverage needs EBIT (Operating Income)
                ratios["interest_coverage"][year] = is_data.loc["Operating Income", year] / abs(is_data.loc["Interest Expense", year])

                # Cash flow ratios
                ratios["cash_flow_to_net_income"][year] = cf.loc["Net Cash Provided by Operating Activities", year] / is_data.loc["Net Income", year]
                # Free Cash Flow = Operating Cash Flow - CapEx (Purchase of Property and Equipment)
                fcf = cf.loc["Net Cash Provided by Operating Activities", year] + cf.loc["Purchase of Property and Equipment", year] # CapEx is negative
                ratios["free_cash_flow_margin"][year] = fcf / is_data.loc["Revenue", year]

            except (KeyError, ZeroDivisionError, TypeError) as e:
                print(f"Warning: Could not calculate some ratios for year {year} due to missing data or zero division: {e}")
                # Assign NaN or handle appropriately
                for name in ratio_names:
                    if year not in ratios[name]:
                         ratios[name][year] = np.nan

        # Calculate year-over-year indices (Beneish M-Score components)
        for i in range(len(years) - 1):
            current_year = years[i]
            prev_year = years[i+1]
            try:
                # Days Sales in Receivables Index (DSRI)
                dsri_current = bs.loc["Accounts Receivable", current_year] / is_data.loc["Revenue", current_year]
                dsri_prev = bs.loc["Accounts Receivable", prev_year] / is_data.loc["Revenue", prev_year]
                ratios["days_sales_in_receivables_index"][current_year] = dsri_current / dsri_prev

                # Gross Margin Index (GMI)
                gm_current = ratios["gross_margin"][current_year]
                gm_prev = ratios["gross_margin"][prev_year]
                ratios["gross_margin_index"][current_year] = gm_prev / gm_current

                # Asset Quality Index (AQI)
                # AQI = [1 - (Current Assets + PP&E) / Total Assets] current / [1 - (Current Assets + PP&E) / Total Assets] previous
                aqi_numerator_current = bs.loc["Total Current Assets", current_year] + bs.loc["Property Plant and Equipment", current_year]
                aqi_numerator_prev = bs.loc["Total Current Assets", prev_year] + bs.loc["Property Plant and Equipment", prev_year]
                aqi_current = (1 - (aqi_numerator_current / bs.loc["Total Assets", current_year]))
                aqi_prev = (1 - (aqi_numerator_prev / bs.loc["Total Assets", prev_year]))
                ratios["asset_quality_index"][current_year] = aqi_current / aqi_prev

                # Sales Growth Index (SGI)
                ratios["sales_growth_index"][current_year] = is_data.loc["Revenue", current_year] / is_data.loc["Revenue", prev_year]

                # Depreciation Index (DEPI)
                dep_current = abs(bs.loc["Accumulated Depreciation", current_year] - bs.loc["Accumulated Depreciation", prev_year])
                dep_prev = abs(bs.loc["Accumulated Depreciation", prev_year] - bs.loc["Accumulated Depreciation", years[i+2] if i+2 < len(years) else prev_year]) # Need one more year back
                ppe_current = bs.loc["Property Plant and Equipment", current_year]
                ppe_prev = bs.loc["Property Plant and Equipment", prev_year]
                dep_rate_current = dep_current / (ppe_current + dep_current)
                dep_rate_prev = dep_prev / (ppe_prev + dep_prev)
                ratios["depreciation_index"][current_year] = dep_rate_prev / dep_rate_current

                # Sales, General & Administrative Index (SGAI)
                sgai_current = is_data.loc["General and Administrative", current_year] / is_data.loc["Revenue", current_year]
                sgai_prev = is_data.loc["General and Administrative", prev_year] / is_data.loc["Revenue", prev_year]
                ratios["sga_index"][current_year] = sgai_current / sgai_prev

                # Leverage Index (LVGI)
                lvgi_current = ratios["debt_to_equity"][current_year]
                lvgi_prev = ratios["debt_to_equity"][prev_year]
                ratios["leverage_index"][current_year] = lvgi_current / lvgi_prev

            except (KeyError, ZeroDivisionError, TypeError, IndexError) as e:
                 print(f"Warning: Could not calculate some index ratios for year {current_year} due to missing data, zero division, or insufficient history: {e}")
                 # Assign NaN or handle appropriately
                 index_ratios = ["days_sales_in_receivables_index", "gross_margin_index", "asset_quality_index", "sales_growth_index", "depreciation_index", "sga_index", "leverage_index"]
                 for name in index_ratios:
                     if current_year not in ratios[name]:
                         ratios[name][current_year] = np.nan

        return ratios

    def calculate_beneish_m_score(self, ratios, year):
        """Calculate the Beneish M-Score for a specific year."""
        try:
            dsri = ratios["days_sales_in_receivables_index"][year]
            gmi = ratios["gross_margin_index"][year]
            aqi = ratios["asset_quality_index"][year]
            sgi = ratios["sales_growth_index"][year]
            depi = ratios["depreciation_index"][year]
            sgai = ratios["sga_index"][year]
            lvgi = ratios["leverage_index"][year]
            # TATA = Total Accruals / Total Assets (Requires calculation from CF and BS)
            # Placeholder for TATA - requires more complex calculation
            tata = 0.05 # Placeholder value, needs proper calculation

            # Beneish M-Score formula
            m_score = -4.84 + 0.920 * dsri + 0.528 * gmi + 0.404 * aqi + 0.892 * sgi + 0.115 * depi - 0.172 * sgai + 4.679 * tata - 0.327 * lvgi
            return m_score
        except (KeyError, TypeError) as e:
            print(f"Warning: Could not calculate Beneish M-Score for {year} due to missing ratios: {e}")
            return np.nan

    def analyze_ratios(self, ratios):
        """Analyze calculated ratios to identify potential risk indicators."""
        findings = []
        years = list(ratios["gross_margin"].keys()) # Get available years
        if not years:
            return findings
        
        latest_year = years[0]
        prev_year = years[1] if len(years) > 1 else None

        # --- Fraud Risk Indicators --- 
        # Beneish M-Score
        if prev_year: # M-Score requires indices from the latest year
            m_score = self.calculate_beneish_m_score(ratios, latest_year)
            if not np.isnan(m_score) and m_score > -1.78: # Threshold for potential manipulation
                findings.append({
                    "description": f"High Beneish M-Score ({m_score:.2f}), indicating potential earnings manipulation.",
                    "risk_category": "Fraud Risk",
                    "risk_score": 80 + min(20, (m_score + 1.78) * 10), # Scale score based on how much it exceeds threshold
                    "evidence": f"M-Score: {m_score:.2f} (Threshold: -1.78)"
                })
            elif not np.isnan(m_score):
                 findings.append({
                    "description": f"Beneish M-Score ({m_score:.2f}) is below the manipulation threshold.",
                    "risk_category": "Fraud Risk",
                    "risk_score": max(0, 20 + m_score * 5), # Lower score if below threshold
                    "evidence": f"M-Score: {m_score:.2f} (Threshold: -1.78)"
                })

        # DSRI
        if prev_year and latest_year in ratios["days_sales_in_receivables_index"] and not np.isnan(ratios["days_sales_in_receivables_index"][latest_year]):
            dsri = ratios["days_sales_in_receivables_index"][latest_year]
            if dsri > 1.3:
                findings.append({
                    "description": f"High Days Sales in Receivables Index (DSRI) ({dsri:.2f}), suggesting potential revenue inflation.",
                    "risk_category": "Fraud Risk",
                    "risk_score": 75 + min(25, (dsri - 1.3) * 50),
                    "evidence": f"DSRI: {dsri:.2f} (Normal < 1.3)"
                })

        # Cash Flow vs Net Income
        if latest_year in ratios["cash_flow_to_net_income"] and not np.isnan(ratios["cash_flow_to_net_income"][latest_year]):
            cf_ni_ratio = ratios["cash_flow_to_net_income"][latest_year]
            if cf_ni_ratio < 0.8:
                findings.append({
                    "description": f"Low Cash Flow to Net Income ratio ({cf_ni_ratio:.2f}), indicating earnings quality concerns.",
                    "risk_category": "Fraud Risk",
                    "risk_score": 70 + max(0, (0.8 - cf_ni_ratio) * 50),
                    "evidence": f"CF/NI Ratio: {cf_ni_ratio:.2f} (Healthy > 1.0)"
                })

        # --- Revenue Risk Indicators --- 
        # Gross Margin Trend
        if prev_year and not np.isnan(ratios["gross_margin"][latest_year]) and not np.isnan(ratios["gross_margin"][prev_year]):
            if ratios["gross_margin"][latest_year] < ratios["gross_margin"][prev_year]:
                findings.append({
                    "description": f"Declining Gross Margin from {ratios['gross_margin'][prev_year]:.1%} to {ratios['gross_margin'][latest_year]:.1%}.",
                    "risk_category": "Revenue Risk",
                    "risk_score": 60,
                    "evidence": f"GM {latest_year}: {ratios['gross_margin'][latest_year]:.1%}, GM {prev_year}: {ratios['gross_margin'][prev_year]:.1%}"
                })
        
        # Sales Growth Index
        if prev_year and latest_year in ratios["sales_growth_index"] and not np.isnan(ratios["sales_growth_index"][latest_year]):
            sgi = ratios["sales_growth_index"][latest_year]
            if sgi < 1.0:
                 findings.append({
                    "description": f"Negative or stagnant sales growth (SGI: {sgi:.2f}).",
                    "risk_category": "Revenue Risk",
                    "risk_score": 50 + max(0, (1.0 - sgi) * 50),
                    "evidence": f"SGI: {sgi:.2f}"
                })

        # --- Legal/Financial Health Risk Indicators ---
        # Current Ratio
        if latest_year in ratios["current_ratio"] and not np.isnan(ratios["current_ratio"][latest_year]):
            cr = ratios["current_ratio"][latest_year]
            if cr < 1.0:
                findings.append({
                    "description": f"Low Current Ratio ({cr:.2f}), indicating potential short-term liquidity issues.",
                    "risk_category": "Legal Risk", # Liquidity issues can lead to legal problems
                    "risk_score": 65,
                    "evidence": f"Current Ratio: {cr:.2f} (Healthy > 1.5-2.0)"
                })

        # Debt-to-Equity Ratio
        if latest_year in ratios["debt_to_equity"] and not np.isnan(ratios["debt_to_equity"][latest_year]):
            dte = ratios["debt_to_equity"][latest_year]
            if dte > 2.0: # Threshold can vary by industry
                findings.append({
                    "description": f"High Debt-to-Equity ratio ({dte:.2f}), indicating high financial leverage.",
                    "risk_category": "Legal Risk", # High debt increases bankruptcy risk
                    "risk_score": 60 + min(40, (dte - 2.0) * 20),
                    "evidence": f"D/E Ratio: {dte:.2f} (High > 2.0)"
                })

        return findings

# Helper function (can be moved to a utils file later)
def process_financial_dataframe(df):
    """Processes a single financial dataframe (from CSV)."""
    try:
        df_processed = df.set_index("Account")
        for col in df_processed.columns:
            df_processed[col] = pd.to_numeric(df_processed[col], errors="coerce")
        return df_processed
    except KeyError:
        print("Error: 'Account' column not found. Ensure CSVs have an 'Account' column.")
        return None

if __name__ == "__main__":
    # Example Usage (using the test data created earlier)
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

            analyzer = FinancialRatioAnalyzer()
            calculated_ratios = analyzer.calculate_ratios(financial_data_dict)
            analysis_findings = analyzer.analyze_ratios(calculated_ratios)

            print("\n--- Calculated Ratios (Latest Year) ---")
            latest_year_main = list(calculated_ratios["gross_margin"].keys())[0]
            for name, values in calculated_ratios.items():
                 if latest_year_main in values:
                     print(f"{name}: {values[latest_year_main]:.3f}")
            
            print("\n--- Analysis Findings ---")
            if analysis_findings:
                for finding in analysis_findings:
                    print(f"- {finding['description']} (Risk: {finding['risk_category']}, Score: {finding['risk_score']})")
            else:
                print("No significant risk indicators found based on ratio analysis.")
        else:
            print("Could not process financial dataframes.")

    except FileNotFoundError:
        print(f"Error: Test data files not found in {test_data_dir}")
    except Exception as e:
        print(f"An error occurred during example execution: {e}")

