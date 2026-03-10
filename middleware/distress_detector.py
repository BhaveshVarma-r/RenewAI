"""Distress detection middleware for customer messages."""

from config.distress_keywords import distress_keywords


class DistressDetector:
    """Detects distress signals in customer communications across 9 languages."""

    def check(self, text: str, language: str = "english") -> dict:
        """Check text for distress indicators.
        
        Returns:
            dict with distress_detected, keywords_found, severity
        """
        if not text:
            return {"distress_detected": False, "keywords_found": [], "severity": "none"}

        text_lower = text.lower()
        lang_keywords = distress_keywords.get(language, distress_keywords.get("english", {}))
        
        found_keywords = []
        max_severity = "none"
        severity_order = {"none": 0, "low": 1, "medium": 2, "high": 3}

        for severity in ["high", "medium", "low"]:
            keywords = lang_keywords.get(severity, [])
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    found_keywords.append(keyword)
                    if severity_order.get(severity, 0) > severity_order.get(max_severity, 0):
                        max_severity = severity

        return {
            "distress_detected": len(found_keywords) > 0,
            "keywords_found": found_keywords,
            "severity": max_severity,
        }
