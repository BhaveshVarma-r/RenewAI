"""Safety gate middleware — sequential blocking pipeline."""

import asyncio
from schemas.models import SafetyGateResult, ComplianceResult, CritiqueResult, PolicyData
from mock_services.cloud_dlp import MockCloudDLP
from mock_services.pagerduty import MockPagerDuty
from mock_services.cloud_sql_audit import MockAuditDB
from middleware.distress_detector import DistressDetector
from middleware.compliance_checker import ComplianceChecker


class SafetyGate:
    """Combined safety pipeline: PII masking → distress detection → compliance → quality → mis-selling."""

    def __init__(self):
        self.dlp = MockCloudDLP()
        self.distress_detector = DistressDetector()
        self.compliance_checker = ComplianceChecker()
        self.pagerduty = MockPagerDuty()
        self.audit_db = MockAuditDB()

    async def process(
        self,
        content: str,
        language: str = "english",
        policy_data: PolicyData | None = None,
        critique_result: CritiqueResult | None = None,
        channel: str = "email",
    ) -> SafetyGateResult:
        """Run the full safety pipeline. Target latency ~800ms."""
        violations = []
        escalate_human = False

        # Step 1: PII Masking
        masked_content, pii_findings = self.dlp.mask_pii(content)
        if pii_findings:
            for f in pii_findings:
                violations.append(f"PII detected: {f['type']}")

        # Step 2: Distress Detection
        distress = self.distress_detector.check(masked_content, language)
        if distress["distress_detected"]:
            escalate_human = True
            violations.append(f"Distress detected (severity: {distress['severity']})")
            if distress["severity"] == "high":
                await self.pagerduty.trigger_alert(
                    title=f"DISTRESS_DETECTED - {distress['keywords_found']}",
                    severity="critical",
                    details={"language": language, "keywords": distress["keywords_found"]},
                    source_agent="safety_gate",
                )

        # Step 3: Compliance Check
        compliance = self.compliance_checker.check(
            masked_content, policy_data, channel
        )
        if compliance.violations:
            violations.extend(compliance.violations)
        if compliance.mis_selling_detected:
            await self.pagerduty.trigger_alert(
                title="MIS_SELLING detected in content",
                severity="critical",
                details={"content_preview": masked_content[:200]},
                source_agent="safety_gate",
            )

        # Step 4: Content Quality Check (from critique)
        if critique_result:
            if critique_result.tone_score < 5:
                violations.append(f"Low tone score: {critique_result.tone_score}")
            if critique_result.hallucination_detected:
                violations.append("Hallucination detected by critique agent")
                escalate_human = True

        # Step 5: Determine pass/fail
        passed = compliance.verdict != "BLOCK" and not (
            distress.get("severity") == "high"
        )

        # Simulate ~800ms latency
        await asyncio.sleep(0.1)

        return SafetyGateResult(
            passed=passed,
            masked_content=masked_content,
            compliance=compliance,
            violations=violations,
            escalate_human=escalate_human,
            pii_findings=[{"type": f["type"], "masked": f["masked"]} for f in pii_findings],
        )
