"""Mock Cloud DLP with real regex-based PII detection and masking."""

import re
from typing import Tuple


class MockCloudDLP:
    """Real regex-based PII detection and masking for Indian identifiers."""

    # PII patterns
    PATTERNS = {
        "aadhaar": {
            "regex": re.compile(r'\b(\d{4}[\s-]?\d{4}[\s-]?\d{4})\b'),
            "mask_fn": lambda m: f"XXXX-XXXX-{m.group(1)[-4:]}",
            "description": "Aadhaar Number (12-digit)",
        },
        "pan": {
            "regex": re.compile(r'\b([A-Z]{5}[0-9]{4}[A-Z])\b'),
            "mask_fn": lambda m: f"XXXXX{m.group(1)[-5:]}",
            "description": "PAN Card Number",
        },
        "phone": {
            "regex": re.compile(r'\b(?:\+91[\s-]?)?([6-9]\d{9})\b'),
            "mask_fn": lambda m: f"+91-XXXXX-{m.group(1)[-5:]}",
            "description": "Indian Phone Number",
        },
        "email": {
            "regex": re.compile(r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'),
            "mask_fn": lambda m: f"{m.group(1)[:2]}***@{m.group(1).split('@')[1]}",
            "description": "Email Address",
        },
        "bank_account": {
            "regex": re.compile(r'\b(\d{9,18})\b'),
            "mask_fn": lambda m: f"XXXX-XXXX-{m.group(1)[-4:]}",
            "description": "Bank Account Number",
            "min_length": 9,
        },
        "credit_card": {
            "regex": re.compile(r'\b(\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4})\b'),
            "mask_fn": lambda m: f"XXXX-XXXX-XXXX-{m.group(1)[-4:]}",
            "description": "Credit Card Number",
        },
    }

    def mask_pii(self, text: str) -> Tuple[str, list[dict]]:
        """Detect and mask PII in text.
        
        Returns:
            Tuple of (masked_text, list of findings)
        """
        findings = []
        masked_text = text

        # Process patterns in priority order (credit card before bank account due to overlap)
        priority_order = ["credit_card", "aadhaar", "pan", "phone", "email", "bank_account"]

        for pii_type in priority_order:
            pattern_info = self.PATTERNS[pii_type]
            regex = pattern_info["regex"]
            mask_fn = pattern_info["mask_fn"]

            matches = list(regex.finditer(masked_text))
            # Process in reverse to maintain positions
            for match in reversed(matches):
                original = match.group(0)

                # Skip bank_account if it's likely an aadhaar or credit card
                if pii_type == "bank_account":
                    digits_only = re.sub(r'[\s-]', '', original)
                    if len(digits_only) == 12 or len(digits_only) == 16:
                        continue
                    if len(digits_only) < 9:
                        continue

                masked = mask_fn(match)
                findings.append({
                    "type": pii_type,
                    "original": original,
                    "masked": masked,
                })
                masked_text = masked_text[:match.start()] + masked + masked_text[match.end():]

        return masked_text, findings
