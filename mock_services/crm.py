"""Mock CRM Client with 25+ hardcoded sample policies."""

from datetime import datetime, timedelta
from typing import Optional
from schemas.models import PolicyData


class MockCRMClient:
    """Simulates a CRM system with realistic Indian insurance policy data."""

    def __init__(self):
        self._policies: dict[str, dict] = {}
        self._load_sample_policies()

    def _load_sample_policies(self):
        """Load 25+ sample policies covering all risk tiers, languages, channels, statuses."""
        today = datetime.now()
        samples = [
            # LOW RISK — active policies, good payment history
            {"policy_id": "POL001", "customer_id": "CUST001", "customer_name": "Rajesh Kumar",
             "premium_amount": 12000.0, "due_date": (today + timedelta(days=45)).strftime("%Y-%m-%d"),
             "grace_period_days": 30, "status": "active", "risk_tier": "low",
             "language_preference": "hindi", "channel_preference": "email",
             "contact_phone": "9876543210", "contact_email": "rajesh.kumar@email.com",
             "preferred_contact_time": "morning", "payment_history": ["on_time", "on_time", "on_time", "on_time"],
             "agent_id": "AG001", "policy_type": "term_life", "sum_assured": 1000000.0,
             "emi_eligible": False, "nominee_name": "Priya Kumar"},

            {"policy_id": "POL002", "customer_id": "CUST002", "customer_name": "Ananya Sharma",
             "premium_amount": 8500.0, "due_date": (today + timedelta(days=50)).strftime("%Y-%m-%d"),
             "grace_period_days": 30, "status": "active", "risk_tier": "low",
             "language_preference": "english", "channel_preference": "email",
             "contact_phone": "9876543211", "contact_email": "ananya.sharma@email.com",
             "preferred_contact_time": "afternoon", "payment_history": ["on_time", "on_time", "on_time"],
             "agent_id": "AG002", "policy_type": "endowment", "sum_assured": 500000.0,
             "emi_eligible": False, "nominee_name": "Vikram Sharma"},

            {"policy_id": "POL003", "customer_id": "CUST003", "customer_name": "Suresh Iyer",
             "premium_amount": 15000.0, "due_date": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
             "grace_period_days": 30, "status": "active", "risk_tier": "low",
             "language_preference": "tamil", "channel_preference": "whatsapp",
             "contact_phone": "9876543212", "contact_email": "suresh.iyer@email.com",
             "preferred_contact_time": "evening", "payment_history": ["on_time", "on_time", "on_time", "on_time", "on_time"],
             "agent_id": "AG001", "policy_type": "term_life", "sum_assured": 2000000.0,
             "emi_eligible": False, "nominee_name": "Lakshmi Iyer"},

            # MEDIUM RISK — some late payments
            {"policy_id": "POL004", "customer_id": "CUST004", "customer_name": "Priya Patel",
             "premium_amount": 25000.0, "due_date": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
             "grace_period_days": 30, "status": "active", "risk_tier": "medium",
             "language_preference": "gujarati", "channel_preference": "whatsapp",
             "contact_phone": "9876543213", "contact_email": "priya.patel@email.com",
             "preferred_contact_time": "evening", "payment_history": ["on_time", "late", "on_time", "late"],
             "agent_id": "AG003", "policy_type": "ulip", "sum_assured": 1500000.0,
             "emi_eligible": True, "nominee_name": "Amit Patel"},

            {"policy_id": "POL005", "customer_id": "CUST005", "customer_name": "Mohammed Farooq",
             "premium_amount": 18000.0, "due_date": (today + timedelta(days=25)).strftime("%Y-%m-%d"),
             "grace_period_days": 30, "status": "active", "risk_tier": "medium",
             "language_preference": "english", "channel_preference": "voice",
             "contact_phone": "9876543214", "contact_email": "mohammed.farooq@email.com",
             "preferred_contact_time": "afternoon", "payment_history": ["on_time", "late", "late", "on_time"],
             "agent_id": "AG002", "policy_type": "term_life", "sum_assured": 750000.0,
             "emi_eligible": True, "nominee_name": "Fatima Farooq"},

            {"policy_id": "POL006", "customer_id": "CUST006", "customer_name": "Deepa Nair",
             "premium_amount": 30000.0, "due_date": (today + timedelta(days=35)).strftime("%Y-%m-%d"),
             "grace_period_days": 30, "status": "active", "risk_tier": "medium",
             "language_preference": "malayalam", "channel_preference": "email",
             "contact_phone": "9876543215", "contact_email": "deepa.nair@email.com",
             "preferred_contact_time": "morning", "payment_history": ["on_time", "on_time", "late", "on_time"],
             "agent_id": "AG001", "policy_type": "endowment", "sum_assured": 2500000.0,
             "emi_eligible": True, "nominee_name": "Rahul Nair"},

            {"policy_id": "POL007", "customer_id": "CUST007", "customer_name": "Arjun Reddy",
             "premium_amount": 22000.0, "due_date": (today + timedelta(days=28)).strftime("%Y-%m-%d"),
             "grace_period_days": 30, "status": "active", "risk_tier": "medium",
             "language_preference": "telugu", "channel_preference": "whatsapp",
             "contact_phone": "9876543216", "contact_email": "arjun.reddy@email.com",
             "preferred_contact_time": "weekend", "payment_history": ["late", "on_time", "on_time", "late"],
             "agent_id": "AG003", "policy_type": "term_life", "sum_assured": 1000000.0,
             "emi_eligible": True, "nominee_name": "Sneha Reddy"},

            # HIGH RISK — multiple late payments, grace period
            {"policy_id": "POL008", "customer_id": "CUST008", "customer_name": "Kavitha Menon",
             "premium_amount": 45000.0, "due_date": (today + timedelta(days=15)).strftime("%Y-%m-%d"),
             "grace_period_days": 30, "status": "grace_period", "risk_tier": "high",
             "language_preference": "kannada", "channel_preference": "voice",
             "contact_phone": "9876543217", "contact_email": "kavitha.menon@email.com",
             "preferred_contact_time": "evening", "payment_history": ["late", "late", "missed", "on_time"],
             "agent_id": "AG002", "policy_type": "whole_life", "sum_assured": 3000000.0,
             "emi_eligible": True, "nominee_name": "Sanjay Menon"},

            {"policy_id": "POL009", "customer_id": "CUST009", "customer_name": "Amit Banerjee",
             "premium_amount": 55000.0, "due_date": (today + timedelta(days=10)).strftime("%Y-%m-%d"),
             "grace_period_days": 30, "status": "grace_period", "risk_tier": "high",
             "language_preference": "bengali", "channel_preference": "voice",
             "contact_phone": "9876543218", "contact_email": "amit.banerjee@email.com",
             "preferred_contact_time": "morning", "payment_history": ["late", "late", "late", "on_time"],
             "agent_id": "AG001", "policy_type": "term_life", "sum_assured": 5000000.0,
             "emi_eligible": True, "nominee_name": "Ritu Banerjee"},

            {"policy_id": "POL010", "customer_id": "CUST010", "customer_name": "Sunita Deshmukh",
             "premium_amount": 35000.0, "due_date": (today + timedelta(days=12)).strftime("%Y-%m-%d"),
             "grace_period_days": 30, "status": "grace_period", "risk_tier": "high",
             "language_preference": "marathi", "channel_preference": "whatsapp",
             "contact_phone": "9876543219", "contact_email": "sunita.deshmukh@email.com",
             "preferred_contact_time": "afternoon", "payment_history": ["late", "missed", "late", "on_time"],
             "agent_id": "AG003", "policy_type": "endowment", "sum_assured": 2000000.0,
             "emi_eligible": True, "nominee_name": "Manoj Deshmukh"},

            {"policy_id": "POL011", "customer_id": "CUST011", "customer_name": "Venkatesh Rao",
             "premium_amount": 40000.0, "due_date": (today + timedelta(days=18)).strftime("%Y-%m-%d"),
             "grace_period_days": 30, "status": "grace_period", "risk_tier": "high",
             "language_preference": "kannada", "channel_preference": "email",
             "contact_phone": "9876543220", "contact_email": "venkatesh.rao@email.com",
             "preferred_contact_time": "weekend", "payment_history": ["late", "late", "on_time", "missed"],
             "agent_id": "AG002", "policy_type": "ulip", "sum_assured": 1500000.0,
             "emi_eligible": True, "nominee_name": "Shobha Rao"},

            # CRITICAL RISK — lapsed or about to lapse
            {"policy_id": "POL012", "customer_id": "CUST012", "customer_name": "Ramesh Gupta",
             "premium_amount": 60000.0, "due_date": (today - timedelta(days=5)).strftime("%Y-%m-%d"),
             "grace_period_days": 30, "status": "lapsed", "risk_tier": "critical",
             "language_preference": "hindi", "channel_preference": "voice",
             "contact_phone": "9876543221", "contact_email": "ramesh.gupta@email.com",
             "preferred_contact_time": "evening", "payment_history": ["missed", "late", "missed", "missed"],
             "agent_id": "AG001", "policy_type": "whole_life", "sum_assured": 10000000.0,
             "emi_eligible": True, "lapse_date": (today - timedelta(days=5)).strftime("%Y-%m-%d"),
             "days_since_lapse": 5, "nominee_name": "Sita Gupta"},

            {"policy_id": "POL013", "customer_id": "CUST013", "customer_name": "Lakshmi Krishnan",
             "premium_amount": 75000.0, "due_date": (today - timedelta(days=15)).strftime("%Y-%m-%d"),
             "grace_period_days": 30, "status": "lapsed", "risk_tier": "critical",
             "language_preference": "tamil", "channel_preference": "whatsapp",
             "contact_phone": "9876543222", "contact_email": "lakshmi.krishnan@email.com",
             "preferred_contact_time": "morning", "payment_history": ["missed", "missed", "late", "missed"],
             "agent_id": "AG003", "policy_type": "term_life", "sum_assured": 7500000.0,
             "emi_eligible": True, "lapse_date": (today - timedelta(days=15)).strftime("%Y-%m-%d"),
             "days_since_lapse": 15, "nominee_name": "Ravi Krishnan"},

            {"policy_id": "POL014", "customer_id": "CUST014", "customer_name": "Sanjay Mishra",
             "premium_amount": 50000.0, "due_date": (today + timedelta(days=5)).strftime("%Y-%m-%d"),
             "grace_period_days": 30, "status": "active", "risk_tier": "critical",
             "language_preference": "hindi", "channel_preference": "voice",
             "contact_phone": "9876543223", "contact_email": "sanjay.mishra@email.com",
             "preferred_contact_time": "afternoon", "payment_history": ["missed", "missed", "missed", "late"],
             "agent_id": "AG002", "policy_type": "endowment", "sum_assured": 3000000.0,
             "emi_eligible": True, "nominee_name": "Meera Mishra"},

            {"policy_id": "POL015", "customer_id": "CUST015", "customer_name": "Fatima Begum",
             "premium_amount": 20000.0, "due_date": (today + timedelta(days=7)).strftime("%Y-%m-%d"),
             "grace_period_days": 30, "status": "active", "risk_tier": "critical",
             "language_preference": "bengali", "channel_preference": "email",
             "contact_phone": "9876543224", "contact_email": "fatima.begum@email.com",
             "preferred_contact_time": "evening", "payment_history": ["missed", "late", "missed", "missed"],
             "agent_id": "AG001", "policy_type": "term_life", "sum_assured": 500000.0,
             "emi_eligible": True, "nominee_name": "Ahmed Khan"},

            # Additional policies for edge cases
            # DND registered customer
            {"policy_id": "POL016", "customer_id": "CUST016", "customer_name": "Vikram Singh",
             "premium_amount": 10000.0, "due_date": (today + timedelta(days=20)).strftime("%Y-%m-%d"),
             "grace_period_days": 30, "status": "active", "risk_tier": "medium",
             "language_preference": "hindi", "channel_preference": "voice",
             "contact_phone": "9111111111", "contact_email": "vikram.singh@email.com",
             "preferred_contact_time": "morning", "payment_history": ["on_time", "late", "on_time"],
             "agent_id": "AG003", "policy_type": "term_life", "sum_assured": 750000.0,
             "emi_eligible": False, "nominee_name": "Neha Singh"},

            # Partial payment scenario
            {"policy_id": "POL017", "customer_id": "CUST017", "customer_name": "Gopal Verma",
             "premium_amount": 48000.0, "due_date": (today + timedelta(days=22)).strftime("%Y-%m-%d"),
             "grace_period_days": 30, "status": "active", "risk_tier": "high",
             "language_preference": "hindi", "channel_preference": "whatsapp",
             "contact_phone": "9876543226", "contact_email": "gopal.verma@email.com",
             "preferred_contact_time": "weekend", "payment_history": ["late", "partial", "late", "on_time"],
             "agent_id": "AG002", "policy_type": "ulip", "sum_assured": 2000000.0,
             "emi_eligible": True, "nominee_name": "Rekha Verma"},

            # EMI eligible, Telugu
            {"policy_id": "POL018", "customer_id": "CUST018", "customer_name": "Padma Rani",
             "premium_amount": 36000.0, "due_date": (today + timedelta(days=40)).strftime("%Y-%m-%d"),
             "grace_period_days": 30, "status": "active", "risk_tier": "low",
             "language_preference": "telugu", "channel_preference": "email",
             "contact_phone": "9876543227", "contact_email": "padma.rani@email.com",
             "preferred_contact_time": "afternoon", "payment_history": ["on_time", "on_time", "on_time"],
             "agent_id": "AG001", "policy_type": "endowment", "sum_assured": 1500000.0,
             "emi_eligible": True, "nominee_name": "Srinivas Rani"},

            # Malayalam, weekend preference
            {"policy_id": "POL019", "customer_id": "CUST019", "customer_name": "George Thomas",
             "premium_amount": 28000.0, "due_date": (today + timedelta(days=32)).strftime("%Y-%m-%d"),
             "grace_period_days": 30, "status": "active", "risk_tier": "medium",
             "language_preference": "malayalam", "channel_preference": "whatsapp",
             "contact_phone": "9876543228", "contact_email": "george.thomas@email.com",
             "preferred_contact_time": "weekend", "payment_history": ["on_time", "late", "on_time", "late"],
             "agent_id": "AG003", "policy_type": "whole_life", "sum_assured": 2000000.0,
             "emi_eligible": True, "nominee_name": "Mary Thomas"},

            # Gujarati, high premium
            {"policy_id": "POL020", "customer_id": "CUST020", "customer_name": "Hiren Mehta",
             "premium_amount": 100000.0, "due_date": (today + timedelta(days=15)).strftime("%Y-%m-%d"),
             "grace_period_days": 30, "status": "grace_period", "risk_tier": "high",
             "language_preference": "gujarati", "channel_preference": "voice",
             "contact_phone": "9876543229", "contact_email": "hiren.mehta@email.com",
             "preferred_contact_time": "evening", "payment_history": ["late", "late", "on_time", "late"],
             "agent_id": "AG002", "policy_type": "ulip", "sum_assured": 10000000.0,
             "emi_eligible": True, "nominee_name": "Jyoti Mehta"},

            # Marathi, lapsed recently
            {"policy_id": "POL021", "customer_id": "CUST021", "customer_name": "Pravin Jadhav",
             "premium_amount": 16000.0, "due_date": (today - timedelta(days=10)).strftime("%Y-%m-%d"),
             "grace_period_days": 30, "status": "lapsed", "risk_tier": "critical",
             "language_preference": "marathi", "channel_preference": "voice",
             "contact_phone": "9876543230", "contact_email": "pravin.jadhav@email.com",
             "preferred_contact_time": "morning", "payment_history": ["missed", "missed", "late", "missed"],
             "agent_id": "AG001", "policy_type": "term_life", "sum_assured": 1000000.0,
             "emi_eligible": True, "lapse_date": (today - timedelta(days=10)).strftime("%Y-%m-%d"),
             "days_since_lapse": 10, "nominee_name": "Savita Jadhav"},

            # Kannada, overdue but in grace
            {"policy_id": "POL022", "customer_id": "CUST022", "customer_name": "Nagaraj Gowda",
             "premium_amount": 32000.0, "due_date": (today - timedelta(days=3)).strftime("%Y-%m-%d"),
             "grace_period_days": 30, "status": "grace_period", "risk_tier": "high",
             "language_preference": "kannada", "channel_preference": "whatsapp",
             "contact_phone": "9876543231", "contact_email": "nagaraj.gowda@email.com",
             "preferred_contact_time": "afternoon", "payment_history": ["late", "on_time", "missed", "late"],
             "agent_id": "AG003", "policy_type": "endowment", "sum_assured": 1500000.0,
             "emi_eligible": True, "nominee_name": "Asha Gowda"},

            # Bengali, low risk email
            {"policy_id": "POL023", "customer_id": "CUST023", "customer_name": "Debashis Roy",
             "premium_amount": 9500.0, "due_date": (today + timedelta(days=55)).strftime("%Y-%m-%d"),
             "grace_period_days": 30, "status": "active", "risk_tier": "low",
             "language_preference": "bengali", "channel_preference": "email",
             "contact_phone": "9876543232", "contact_email": "debashis.roy@email.com",
             "preferred_contact_time": "evening", "payment_history": ["on_time", "on_time", "on_time", "on_time"],
             "agent_id": "AG002", "policy_type": "term_life", "sum_assured": 750000.0,
             "emi_eligible": False, "nominee_name": "Mousumi Roy"},

            # Tamil, critical voice
            {"policy_id": "POL024", "customer_id": "CUST024", "customer_name": "Murugan Selvam",
             "premium_amount": 42000.0, "due_date": (today + timedelta(days=3)).strftime("%Y-%m-%d"),
             "grace_period_days": 30, "status": "active", "risk_tier": "critical",
             "language_preference": "tamil", "channel_preference": "voice",
             "contact_phone": "9876543233", "contact_email": "murugan.selvam@email.com",
             "preferred_contact_time": "morning", "payment_history": ["missed", "missed", "late", "missed"],
             "agent_id": "AG001", "policy_type": "whole_life", "sum_assured": 5000000.0,
             "emi_eligible": True, "nominee_name": "Selvi Murugan"},

            # English, medium risk, whatsapp
            {"policy_id": "POL025", "customer_id": "CUST025", "customer_name": "Sarah D'Souza",
             "premium_amount": 14000.0, "due_date": (today + timedelta(days=38)).strftime("%Y-%m-%d"),
             "grace_period_days": 30, "status": "active", "risk_tier": "medium",
             "language_preference": "english", "channel_preference": "whatsapp",
             "contact_phone": "9876543234", "contact_email": "sarah.dsouza@email.com",
             "preferred_contact_time": "afternoon", "payment_history": ["on_time", "late", "on_time", "late"],
             "agent_id": "AG003", "policy_type": "endowment", "sum_assured": 1000000.0,
             "emi_eligible": True, "nominee_name": "Michael D'Souza"},

            # Telugu, high risk, email
            {"policy_id": "POL026", "customer_id": "CUST026", "customer_name": "Srinivas Reddy",
             "premium_amount": 52000.0, "due_date": (today + timedelta(days=8)).strftime("%Y-%m-%d"),
             "grace_period_days": 30, "status": "grace_period", "risk_tier": "high",
             "language_preference": "telugu", "channel_preference": "email",
             "contact_phone": "9876543235", "contact_email": "srinivas.reddy@email.com",
             "preferred_contact_time": "weekend", "payment_history": ["late", "missed", "late", "late"],
             "agent_id": "AG002", "policy_type": "term_life", "sum_assured": 3000000.0,
             "emi_eligible": True, "nominee_name": "Vijaya Reddy"},

            # Cancelled policy edge case
            {"policy_id": "POL027", "customer_id": "CUST027", "customer_name": "Anil Kapoor",
             "premium_amount": 20000.0, "due_date": (today - timedelta(days=60)).strftime("%Y-%m-%d"),
             "grace_period_days": 30, "status": "cancelled", "risk_tier": "critical",
             "language_preference": "hindi", "channel_preference": "email",
             "contact_phone": "9876543236", "contact_email": "anil.kapoor@email.com",
             "preferred_contact_time": "morning", "payment_history": ["missed", "missed", "missed", "missed"],
             "agent_id": "AG001", "policy_type": "ulip", "sum_assured": 500000.0,
             "emi_eligible": False, "lapse_date": (today - timedelta(days=60)).strftime("%Y-%m-%d"),
             "days_since_lapse": 60, "nominee_name": "Sunita Kapoor"},
        ]

        for p in samples:
            self._policies[p["policy_id"]] = p

    def get_policy(self, policy_id: str) -> Optional[PolicyData]:
        """Retrieve a single policy by ID."""
        data = self._policies.get(policy_id)
        if data:
            return PolicyData(**data)
        return None

    def get_customer_policies(self, customer_id: str) -> list[PolicyData]:
        """Get all policies for a customer."""
        return [
            PolicyData(**p) for p in self._policies.values()
            if p["customer_id"] == customer_id
        ]

    def update_policy_status(self, policy_id: str, status: str) -> bool:
        """Update a policy's status."""
        if policy_id in self._policies:
            self._policies[policy_id]["status"] = status
            return True
        return False

    def get_due_policies(self, days_ahead: int = 60) -> list[PolicyData]:
        """Get all policies due within the next N days."""
        today = datetime.now()
        cutoff = today + timedelta(days=days_ahead)
        results = []
        for p in self._policies.values():
            if p["status"] in ("active", "grace_period"):
                due = datetime.strptime(p["due_date"], "%Y-%m-%d")
                if today <= due <= cutoff:
                    results.append(PolicyData(**p))
        return results

    def check_payment_status(self, policy_id: str) -> dict:
        """Check current payment status for a policy."""
        p = self._policies.get(policy_id)
        if not p:
            return {"status": "not_found"}
        today = datetime.now()
        due = datetime.strptime(p["due_date"], "%Y-%m-%d")
        if due > today:
            return {"status": "upcoming", "days_to_due": (due - today).days}
        elif (today - due).days <= p["grace_period_days"]:
            return {"status": "overdue_in_grace", "days_overdue": (today - due).days}
        else:
            return {"status": "lapsed", "days_overdue": (today - due).days}

    def get_lapsed_policies(self, days_since_lapse: int = 30) -> list[PolicyData]:
        """Get all policies that have lapsed within the given number of days."""
        return [
            PolicyData(**p) for p in self._policies.values()
            if p["status"] == "lapsed"
            and p.get("days_since_lapse") is not None
            and p["days_since_lapse"] <= days_since_lapse
        ]

    def get_all_policies(self) -> list[PolicyData]:
        """Get all policies in the system."""
        return [PolicyData(**p) for p in self._policies.values()]
