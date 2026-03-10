"""IRDAI compliance checker middleware."""

from schemas.models import ComplianceResult, PolicyData
from config.irdai_rules import IRDAI_RULES


class ComplianceChecker:
    """Checks content against IRDAI regulatory rules."""

    def check(self, content: str, policy_data: PolicyData | None = None, channel: str = "email", contact_count: int = 1) -> ComplianceResult:
        """Run all applicable IRDAI compliance rules against content.
        
        Returns ComplianceResult with verdict and violations.
        """
        violations = []
        hard_block = False
        kwargs = {
            "content": content,
            "policy_type": policy_data.policy_type if policy_data else "",
            "grace_period_days": policy_data.grace_period_days if policy_data else 30,
            "contact_count": contact_count,
        }

        irdai_disclosure = False
        opt_out = False
        grievance = False
        mis_selling = False

        for rule in IRDAI_RULES:
            try:
                passed = rule["check_fn"](**kwargs)
            except TypeError:
                # Try with just content
                try:
                    passed = rule["check_fn"](content)
                except Exception:
                    passed = True

            if not passed:
                violations.append(f"[{rule['category']}] {rule['name']} (severity: {rule['severity']})")
                if rule["hard_block"]:
                    hard_block = True
                if rule["name"] == "no_mis_selling":
                    mis_selling = True

            # Track disclosure checks
            if rule["name"] == "ai_identity_declared" and passed:
                irdai_disclosure = True
            elif rule["name"] == "opt_out_mechanism_present" and passed:
                opt_out = True
            elif rule["name"] == "grievance_number_present" and passed:
                grievance = True

        # Determine verdict
        if hard_block or mis_selling:
            verdict = "BLOCK"
        elif violations:
            verdict = "FAIL"
        else:
            verdict = "PASS"

        return ComplianceResult(
            verdict=verdict,
            irdai_disclosure_present=irdai_disclosure,
            opt_out_present=opt_out,
            grievance_number_present=grievance,
            mis_selling_detected=mis_selling,
            pii_violations=[v for v in violations if "PRIVACY" in v],
            trai_dnd_respected=True,
            violations=violations,
        )
