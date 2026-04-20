"""
Interview Analysis Module for Unstructured Data

Placeholder module for analyzing interview transcripts. Focuses on keyword spotting
and potentially identifying sentiment or inconsistencies (basic implementation).
"""

import re
from .text_processing_module import TextProcessingModule
# Optional: Import sentiment analysis library if needed

class InterviewAnalysisModule:
    def __init__(self):
        self.text_processor = TextProcessingModule()
        # Keywords related to potential deception, uncertainty, or negativity
        self.risk_keywords = [
            "uncertain", "maybe", "perhaps", "difficult", "challenging", "concern", 
            "risk", "issue", "problem", "delay", "overstated", "understated", 
            "if", "but", "however", "actually", "frankly", "to be honest"
        ]
        self.positive_keywords = ["confident", "strong", "growth", "opportunity", "positive", "certain", "definitely", "robust"]

    def _find_keywords(self, tokens, keywords):
        """Find occurrences of keywords in tokenized text."""
        found = []
        for token in tokens:
            for keyword in keywords:
                # Use boundary matching to avoid partial matches within words
                if re.search(r"\b" + re.escape(keyword) + r"\b", token):
                    found.append(keyword)
        return found # Return all occurrences for frequency analysis

    def analyze_transcript(self, transcript_text):
        """Analyze a single interview transcript for risk keywords and sentiment."""
        if not isinstance(transcript_text, str) or not transcript_text.strip():
            return {"findings": [], "risk_keyword_freq": 0, "positive_keyword_freq": 0}

        cleaned_text = self.text_processor.clean_text(transcript_text)
        tokens = self.text_processor.tokenize(cleaned_text)
        
        findings = []
        
        # Keyword Frequency Analysis
        found_risk_keywords = self._find_keywords(tokens, self.risk_keywords)
        found_positive_keywords = self._find_keywords(tokens, self.positive_keywords)
        
        risk_freq = len(found_risk_keywords)
        positive_freq = len(found_positive_keywords)
        total_words = len(tokens)
        
        # Calculate relative frequency
        relative_risk_freq = (risk_freq / total_words) * 100 if total_words > 0 else 0

        if relative_risk_freq > 1.5: # Threshold for high frequency of risk/uncertainty words (e.g., > 1.5%)
            findings.append({
                "description": f"High frequency of risk/uncertainty keywords ({relative_risk_freq:.1f}%) detected in interview transcript.",
                "risk_category": "Management Risk", # Interviews often reveal management quality/candor
                "risk_score": 50 + min(50, int(relative_risk_freq * 10)),
                "evidence": f"Risk keywords found: {risk_freq} times (e.g., {list(set(found_risk_keywords))[:5]})"
            })
        elif risk_freq > positive_freq * 1.5: # If risk words significantly outweigh positive words
             findings.append({
                "description": "Risk/uncertainty keywords significantly outweigh positive keywords in interview transcript.",
                "risk_category": "Management Risk",
                "risk_score": 45,
                "evidence": f"Risk keywords: {risk_freq}, Positive keywords: {positive_freq}"
            })

        # Placeholder for more advanced analysis (e.g., inconsistency detection, sentiment shifts)

        return {
            "findings": findings,
            "risk_keyword_freq": risk_freq,
            "positive_keyword_freq": positive_freq
        }

# Example Usage
if __name__ == "__main__":
    interview_analyzer = InterviewAnalysisModule()
    sample_transcript = """
    Interviewer: How confident are you about the revenue projections?
    CEO: Well, frankly, it's challenging. We are confident, but there are risks. 
    The market is perhaps uncertain. However, we see strong growth opportunities. 
    It might be difficult, but we have a robust plan. To be honest, there could be a delay.
    """
    
    results = interview_analyzer.analyze_transcript(sample_transcript)
    print("--- Interview Analysis Results ---")
    print(f"Risk Keyword Frequency: {results["risk_keyword_freq"]}")
    print(f"Positive Keyword Frequency: {results["positive_keyword_freq"]}")
    print("Findings:")
    if results["findings"]:
        for finding in results["findings"]:
            print(f"- {finding["description"]} (Risk: {finding["risk_category"]}, Score: {finding["risk_score"]})\n  Evidence: {finding["evidence"]}")
    else:
        print("No significant risks identified based on keyword frequency.")

