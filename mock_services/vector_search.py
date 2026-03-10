"""Vector Search using ChromaDB and Gemini Embeddings."""

import os
import chromadb
from typing import Optional, List, Dict, Any
import asyncio
from services.gemini_client import GeminiClient
from config.settings import MOCK_DATA_DIR

# Pre-loaded objection-response pairs
OBJECTION_RESPONSE_PAIRS = [
    {"objection": "I can't afford the premium right now",
     "response": "I completely understand that finances can be tight. Let me share some options that might help. We offer EMI plans that can break your premium into smaller, manageable monthly payments. Your policy of ₹{sum_assured} provides crucial protection for your family, and we want to help you keep it active."},
    {"objection": "I want to cancel my policy",
     "response": "I understand you're considering cancellation. Before you decide, let me share what you'd be giving up: your ₹{sum_assured} coverage has been building value, and cancelling now means losing all the premiums you've already paid. Would you consider keeping the policy with a reduced premium option instead?"},
    {"objection": "What happens if I miss the payment?",
     "response": "Great question! You have a grace period of {grace_period_days} days after your due date. During this time, your coverage remains active. After the grace period, your policy will lapse, and you may need to go through medical underwriting again to restart it. We want to help you avoid that."},
    {"objection": "I already have another insurance policy",
     "response": "Having multiple policies is actually a wise strategy! Each policy serves a different purpose. Your Suraksha Life policy provides unique benefits like {policy_type} coverage with a sum assured of ₹{sum_assured}. This complements your other coverage and ensures complete financial protection for your family."},
    {"objection": "The premium is too expensive",
     "response": "I hear your concern about the cost. Let's look at this differently - your premium of ₹{premium_amount} works out to just ₹{daily_cost} per day for ₹{sum_assured} of protection. We also have EMI options that can make it even more affordable."},
    {"objection": "I don't trust insurance companies",
     "response": "Your concerns are valid, and I appreciate your honesty. Suraksha Life Insurance is regulated by IRDAI and has a claim settlement ratio of 97.3%. We're committed to transparency - you can track your policy status anytime, and our grievance helpline (1800-XXX-XXXX) is always available."},
    {"objection": "I need to discuss with my family first",
     "response": "Absolutely, this is an important family decision. I'd suggest sharing these key points: your policy provides ₹{sum_assured} protection, and the grace period ends on {due_date}. Would it help if I sent you a summary that you can share with your family?"},
    {"objection": "Can I pay in installments?",
     "response": "Yes! We offer convenient EMI options. Your annual premium of ₹{premium_amount} can be split into quarterly (₹{quarterly_amount}) or monthly (₹{monthly_amount}) payments. This makes it much easier to manage. Shall I set up an EMI plan for you?"},
    {"objection": "I've had bad experiences with claims",
     "response": "I'm sorry to hear about your past experience. At Suraksha Life, we've improved our claims process significantly. Our average claim processing time is now 7 working days, and we provide a dedicated claims assistant. Your nominee {nominee_name} will receive full support during the claims process."},
    {"objection": "I'll pay later, not now",
     "response": "I understand you'd like more time. Just a gentle reminder that your payment is due on {due_date}, and you have {grace_period_days} days of grace period. After that, you risk losing your coverage and may face reinstatement charges. Can we schedule a reminder for a date that works better for you?"},
    {"objection": "My financial situation has changed",
     "response": "I completely understand that life circumstances change. We have several options to help: premium reduction plans, policy conversion options, or EMI payments. The most important thing is to keep your coverage active. Let's find a solution that works with your current budget."},
    {"objection": "I don't need life insurance anymore",
     "response": "I understand your perspective. However, life insurance isn't just about you - it's about protecting those who depend on you. Your policy ensures that {nominee_name} and your family maintain their lifestyle even in your absence. At ₹{sum_assured}, this coverage provides significant financial security."},
    {"objection": "The returns are not good enough",
     "response": "I understand your concern about returns. While life insurance is primarily about protection, your {policy_type} policy also offers tax benefits under Section 80C. The real value lies in the ₹{sum_assured} protection it provides your family. Would you like me to explain the tax savings?"},
    {"objection": "I'm healthy, I don't need insurance",
     "response": "It's wonderful that you're healthy! That's actually the best time to have insurance - premiums are lower, and you're guaranteed coverage. If health conditions develop later, getting new coverage becomes difficult and expensive. Your current policy locks in favorable terms."},
    {"objection": "I want to switch to a different company",
     "response": "Before switching, please consider: you'll lose the premium tenure you've built with us, may face new medical exams, and could get higher premiums due to age. Your current Suraksha Life policy has established benefits. Would you like me to compare what you'd gain versus what you'd lose?"},
    {"objection": "Government schemes are enough for me",
     "response": "Government schemes like PMJJBY provide basic coverage up to ₹2 lakhs. Your Suraksha Life policy offers ₹{sum_assured} - significantly more protection. They actually complement each other well. Your family deserves comprehensive coverage."},
    {"objection": "I lost my job recently",
     "response": "I'm sorry to hear about your job situation. This is exactly when insurance protection matters most. We have a special hardship program that can reduce your premium temporarily or pause payments for up to 3 months while keeping your coverage active. Let me connect you with our support team."},
    {"objection": "Can you reduce the premium amount?",
     "response": "Let me explore options for you. We can adjust your coverage or move to a more affordable plan. Your current premium is ₹{premium_amount} for ₹{sum_assured} coverage. We could also explore paid-up options. What premium range would work better for you?"},
    {"objection": "I forgot about the payment",
     "response": "No worries at all! Your payment of ₹{premium_amount} is due on {due_date}. You still have time within the grace period. I can send you a payment link right now for quick online payment. Would you prefer UPI, net banking, or card payment?"},
    {"objection": "I'm planning to take a different type of policy",
     "response": "That's a thoughtful decision. Before you make the switch, remember that your current {policy_type} policy has unique advantages. Starting a new policy means new waiting periods and potentially higher premiums. Could we discuss what you're looking for? Maybe we can modify your existing policy to better suit your needs."},
    {"objection": "Send me the details on WhatsApp",
     "response": "Sure! I'll send you a detailed summary of your policy on WhatsApp right away. This will include your policy number {policy_id}, premium amount, due date, and payment options. You can review it at your convenience and pay directly through the link."},
    {"objection": "I need to check my bank balance first",
     "response": "Of course, take your time. Your premium of ₹{premium_amount} is due by {due_date}. Remember, we also accept partial payments and EMI options. I'll send you the payment link so you can pay whenever you're ready within the grace period."},
    {"objection": "The agent who sold me the policy made false promises",
     "response": "I sincerely apologize for any miscommunication. This is a serious concern and I want to help resolve it. I can connect you with our grievance department at 1800-XXX-XXXX. Meanwhile, let me clarify the actual benefits of your policy so you have accurate information."},
    {"objection": "I want a loan against my policy instead",
     "response": "That's a great option! If your {policy_type} policy has accumulated sufficient surrender value, you may be eligible for a loan of up to 80% of that value. This way, you get the funds you need while keeping your policy active. Shall I check your eligibility?"},
    {"objection": "My nominee details need to be updated",
     "response": "I can help you update your nominee details right away. This is an important step to ensure your policy benefits reach the right person. I'll guide you through the simple process. It won't affect your premium or coverage at all."},
    {"objection": "I'm not getting enough tax benefits",
     "response": "Your premium of ₹{premium_amount} qualifies for tax deduction under Section 80C (up to ₹1.5 lakh). The maturity proceeds are also tax-free under Section 10(10D). This effectively reduces your actual cost of insurance significantly."},
    {"objection": "The claim process seems too complicated",
     "response": "I understand your concern. We've simplified our claims process significantly. It's now a 3-step digital process: submit documents online, get acknowledgment within 24 hours, and receive settlement within 7 working days. Your nominee {nominee_name} will receive full support during the claims process."},
    {"objection": "I'll think about it and call back",
     "response": "Absolutely, take your time to think. Just keep in mind that your grace period ends on {due_date} plus {grace_period_days} days. I'll send you a summary of your policy and payment options. You can reach us anytime at 1800-XXX-XXXX. Is there any specific concern I can address before you decide?"},
    {"objection": "My spouse doesn't want me to continue the policy",
     "response": "I understand family decisions are important. Perhaps I could help by sharing a family benefits summary that shows how this policy protects your family? The ₹{sum_assured} coverage is designed to secure your spouse and dependents' financial future in case of any eventuality."},
    {"objection": "I received a better offer from another company",
     "response": "I'd be happy to help you compare. Often, new policies come with waiting periods, new medical requirements, and age-based premium increases. Your current policy has established benefits and no new waiting periods. Could you share the offer details so I can make an objective comparison?"},
    {"objection": "Why should I pay when I'm not sick?",
     "response": "Insurance works best when you're healthy! Think of it as an emergency fund that gives your family ₹{sum_assured} when they need it most. Just like you maintain your car even when it runs fine, your insurance policy ensures you're always protected."},
    {"objection": "I want to reduce the sum assured",
     "response": "We can explore reducing your sum assured, which would lower your premium. However, please consider if the reduced coverage would adequately protect your family. Your current ₹{sum_assured} was chosen based on your family's needs. Would you like to discuss what level of coverage makes sense?"},
    {"objection": "The waiting period is too long",
     "response": "Your policy's waiting period is designed to ensure the best service for all policyholders. The good news is, since you've been with us, you may have already completed your waiting period. Let me check your specific policy terms and explain exactly what's covered right now."},
    {"objection": "I want a refund of all premiums paid",
     "response": "I understand your frustration. While a full refund isn't possible outside the free-look period, your policy has accumulated a surrender value. However, surrendering would mean losing your ₹{sum_assured} coverage and the premiums you've invested. Let's explore alternatives that keep your benefits intact."},
    {"objection": "Just leave me alone, stop calling",
     "response": "I sincerely apologize for any inconvenience. Your preferences matter to us. I'll note your request and ensure minimal future contact. Before I go, I just want to make sure you're aware that your policy premium of ₹{premium_amount} is due soon. You can always reach us at 1800-XXX-XXXX if you need help."},
    {"objection": "EMI pe kar sakte hain kya?",
     "response": "Haan bilkul! Aapki annual premium ko monthly ya quarterly installments mein divide kar sakte hain. Isse aapko ek saath bada amount nahi dena padega. Kya aap monthly EMI plan prefer karenge?"},
    {"objection": "Abhi mere paas paise nahi hain",
     "response": "Main samajhta/samajhti hoon aapki situation. Hum aapke liye kuch options dhundh sakte hain - EMI plan, premium holiday, ya reduced coverage. Sabse zaroori hai ki aapki policy active rahe aur aapke parivaar ki suraksha bani rahe."},
    {"objection": "Mujhe kisi se baat karni hai",
     "response": "Bilkul, main aapko humare specialist se connect karta/karti hoon. Woh aapke saare sawaalon ka jawab denge. Aapki policy number {policy_id} hai, toh woh aapki details dekh sake. Kya aap abhi baat kar sakte hain?"},
    {"objection": "Premium bahut zyada hai",
     "response": "Main aapki baat samajhta/samajhti hoon. Lekin dekhiye, aapki ₹{premium_amount} ki premium se aapke parivaar ko ₹{sum_assured} ki suraksha milti hai. Hum EMI option bhi de sakte hain jisse monthly payment chhota ho jaaye."},
    {"objection": "Policy cancel karo",
     "response": "Rukiye, cancel karne se pehle ek baar sochiye - aapne ab tak jo premiums diye hain woh sab jaayenge, aur naya insurance lena mehnga padega. Kya hum koi aur option explore kar sakte hain? Jaise premium reduce karna ya EMI plan?"},
    {"objection": "I'm going through a medical emergency",
     "response": "I'm very sorry to hear about your medical emergency. Your health and well-being come first. We have a special medical hardship provision that can help. Let me connect you with our priority support team who can assist you with premium deferral options. Please take care."},
    {"objection": "Can't pay online, I prefer offline payment",
     "response": "Of course! You can pay your premium at any Suraksha Life branch near you, or through our authorized collection agents. You can also pay at select bank branches. Would you like me to share the nearest payment location?"},
    {"objection": "I want to convert to a paid-up policy",
     "response": "Converting to a paid-up policy is an option if you've paid premiums for at least 3 years. Your paid-up value would be reduced proportionally. However, I'd recommend continuing the full premium to get the complete ₹{sum_assured} benefit. Shall I show you both scenarios?"},
    {"objection": "Mera experience bahut kharab raha hai",
     "response": "Mujhe bahut dukh hai yeh sunke. Aapka feedback humare liye bahut important hai. Main personally ensure karunga/karungi ki aapka experience better ho. Aap humare grievance helpline 1800-XXX-XXXX pe bhi complaint register kar sakte hain. Kya aap mujhe batayenge ki kya problem hui?"},
    {"objection": "I have too many financial commitments right now",
     "response": "I understand juggling multiple financial commitments is challenging. However, your insurance policy is a fundamental financial safety net. Let's look at how we can make it fit your budget - perhaps through EMI, a temporary premium reduction, or adjusting the payment schedule."},
    {"objection": "What's the point of insurance anyway?",
     "response": "That's a fair question. Insurance is essentially a promise to protect your family financially when they need it most. Your ₹{sum_assured} policy ensures that even in the worst scenario, your family can maintain their lifestyle, children's education continues, and EMIs are covered. It's peace of mind you can't put a price on."},
    {"objection": "I want to add a rider to my policy",
     "response": "Great thinking! Adding riders like accidental death benefit, critical illness cover, or premium waiver can enhance your protection significantly. I can share the available riders and their costs. This wouldn't affect your current premium due date. Shall I proceed?"},
    {"objection": "My policy documents are lost",
     "response": "Don't worry, we can help! You can get a duplicate policy document by submitting a simple request. Your policy number is {policy_id}, so all your details are safe in our system. I can start the process for you right now. Would you like that?"},
    {"objection": "Payment link is not working",
     "response": "I apologize for the inconvenience. Let me generate a fresh payment link for you right away. You can also pay via UPI to {upi_id} or through our website. Would you prefer I send the new link on WhatsApp or email?"},
    {"objection": "I want to increase my coverage",
     "response": "That's a wise decision! Increasing your sum assured means better protection for your family. Based on your current policy, we can offer enhanced coverage options. This might slightly increase your premium, but the added protection is well worth it. Shall I share the options?"},
]

class MockVectorSearch:
    """Vector search using ChromaDB and Gemini Embeddings."""

    def __init__(self):
        self.chroma_path = str(MOCK_DATA_DIR / "chroma_db_gemini")
        self.client = chromadb.PersistentClient(path=self.chroma_path)
        self.gemini = GeminiClient()
        self.collection_name = "insurance_objections_gemini"

    async def _init_collection(self):
        """Initialize ChromaDB collection."""
        try:
            # get_or_create is the safest way to handle this
            self.collection = self.client.get_or_create_collection(name=self.collection_name)
            if self.collection.count() == 0:
                await self._load_objection_pairs()
        except Exception as e:
            print(f"Error initializing collection: {e}")
            # Final attempt: just try to get it if it exists
            self.collection = self.client.get_collection(name=self.collection_name)

    async def async_init(self):
        await self._init_collection()

    async def _load_objection_pairs(self):
        """Load initial data into ChromaDB using Gemini Embeddings."""
        print(f"Initializing Gemini ChromaDB collection '{self.collection_name}'...")
        objections = [p["objection"] for p in OBJECTION_RESPONSE_PAIRS]
        ids = [f"obj_{i}" for i in range(len(OBJECTION_RESPONSE_PAIRS))]
        metadatas = [{"response": p["response"]} for p in OBJECTION_RESPONSE_PAIRS]
        
        # Await the async embedding call directly
        embeddings = await self.gemini.embed_batch(objections)
        
        self.collection.add(
            embeddings=embeddings,
            documents=objections,
            metadatas=metadatas,
            ids=ids
        )
        print("ChromaDB Gemini initialization complete.")

    async def async_similarity_search(self, query: str, k: int = 5) -> list[dict]:
        """Awaited semantic search using Gemini Embeddings."""
        query_embedding = await self.gemini.embed(query)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k
        )
        
        formatted = []
        if results['documents'] and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                formatted.append({
                    "objection": results['documents'][0][i],
                    "response": results['metadatas'][0][i]["response"],
                    "score": 1.0 - (results['distances'][0][i] if results['distances'] else 0.5)
                })
        return formatted

    async def similarity_search(self, query: str, k: int = 5) -> list[dict]:
        """Semantic search using Gemini Embeddings."""
        return await self.async_similarity_search(query, k)
