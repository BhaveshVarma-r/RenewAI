import { useState, useEffect } from 'react';
import { getPolicies, triggerDueDate, triggerInbound, triggerLapse, getAuditPolicy } from '../api/client';

interface Policy {
    policy_id: string; customer_id: string; customer_name: string; premium_amount: number;
    due_date: string; grace_period_days: number; status: string; risk_tier: string;
    language_preference: string; channel_preference: string; contact_phone: string;
    contact_email: string; preferred_contact_time: string; payment_history: string[];
    emi_eligible: boolean; sum_assured: number; days_since_lapse?: number; nominee_name: string;
}

const tierColors: Record<string, string> = { low: 'badge-low', medium: 'badge-medium', high: 'badge-high', critical: 'badge-critical' };

export default function PolicyLookup() {
    const [policies, setPolicies] = useState<Policy[]>([]);
    const [search, setSearch] = useState('');
    const [selected, setSelected] = useState<Policy | null>(null);
    const [triggerResult, setTriggerResult] = useState<any>(null);
    const [triggering, setTriggering] = useState(false);
    const [history, setHistory] = useState<any[]>([]);

    useEffect(() => { getPolicies().then(r => setPolicies(r.data.policies || [])).catch(console.error); }, []);

    const fetchHistory = async (policyId: string) => {
        try {
            const res = await getAuditPolicy(policyId);
            setHistory(res.data.steps || []);
        } catch (e) { console.error(e); }
    };

    const handleSelect = (p: Policy) => {
        setSelected(p);
        setTriggerResult(null);
        setHistory([]);
        fetchHistory(p.policy_id);
    };

    const handleTrigger = async (type: 'due' | 'inbound' | 'lapse') => {
        if (!selected) return;
        setTriggering(true); setTriggerResult(null);
        try {
            let res;
            if (type === 'due') res = await triggerDueDate(selected.policy_id, 30);
            else if (type === 'inbound') res = await triggerInbound(selected.policy_id, 'whatsapp', 'Test message', selected.contact_phone);
            else res = await triggerLapse(selected.policy_id, selected.days_since_lapse || 10);
            setTriggerResult(res.data);
            fetchHistory(selected.policy_id);
        } catch (e: any) { setTriggerResult({ error: e.message }); }
        finally { setTriggering(false); }
    };

    const filtered = policies.filter(p =>
        p.policy_id.toLowerCase().includes(search.toLowerCase()) ||
        p.customer_name.toLowerCase().includes(search.toLowerCase())
    );

    return (
        <div className="animate-fadeIn">
            <div className="mb-8"><h1 className="text-3xl font-bold text-white">Policy Lookup</h1><p className="text-slate-400 mt-1">Search and test any of {policies.length} sample policies</p></div>

            <div className="glass-card p-4 mb-6">
                <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search by policy ID or customer name..."
                    className="w-full px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-2 max-h-[800px] overflow-auto">
                    {filtered.map(p => (
                        <div key={p.policy_id} onClick={() => handleSelect(p)}
                            className={`glass-card p-4 cursor-pointer hover:bg-white/10 transition ${selected?.policy_id === p.policy_id ? 'ring-2 ring-primary-500' : ''}`}>
                            <div className="flex items-center justify-between">
                                <div>
                                    <span className="font-mono text-primary-400 font-medium">{p.policy_id}</span>
                                    <span className="text-slate-300 ml-3">{p.customer_name}</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${tierColors[p.risk_tier]}`}>{p.risk_tier}</span>
                                    <span className="text-slate-400 text-xs">₹{p.premium_amount.toLocaleString()}</span>
                                </div>
                            </div>
                            <div className="flex gap-4 mt-2 text-xs text-slate-400">
                                <span>📅 {p.due_date}</span><span>🌐 {p.language_preference}</span><span>📱 {p.channel_preference}</span><span>{p.status}</span>
                            </div>
                        </div>
                    ))}
                </div>

                {selected && (
                    <div className="space-y-6">
                        <div className="glass-card p-6">
                            <h3 className="text-lg font-semibold text-white mb-4">{selected.customer_name}</h3>
                            <div className="space-y-2 text-sm mb-6">
                                {[
                                    ['Policy', selected.policy_id], ['Premium', `₹${selected.premium_amount.toLocaleString()}`],
                                    ['Due Date', selected.due_date], ['Status', selected.status], ['Risk', selected.risk_tier],
                                    ['Language', selected.language_preference], ['Channel', selected.channel_preference],
                                    ['Sum Assured', `₹${selected.sum_assured.toLocaleString()}`], ['EMI', selected.emi_eligible ? 'Yes' : 'No'],
                                    ['Nominee', selected.nominee_name], ['Time Pref', selected.preferred_contact_time],
                                ].map(([k, v]) => (
                                    <div key={k as string} className="flex justify-between"><span className="text-slate-400">{k}</span><span className="text-white">{v}</span></div>
                                ))}
                            </div>
                            <div className="space-y-2">
                                <button onClick={() => handleTrigger('due')} disabled={triggering}
                                    className="w-full py-2 rounded-xl bg-primary-500/20 text-primary-400 hover:bg-primary-500/30 transition text-sm font-medium disabled:opacity-50">
                                    🔔 Trigger Due Date
                                </button>
                                <button onClick={() => handleTrigger('inbound')} disabled={triggering}
                                    className="w-full py-2 rounded-xl bg-green-500/20 text-green-400 hover:bg-green-500/30 transition text-sm font-medium disabled:opacity-50">
                                    📩 Simulate Inbound
                                </button>
                                <button onClick={() => handleTrigger('lapse')} disabled={triggering}
                                    className="w-full py-2 rounded-xl bg-orange-500/20 text-orange-400 hover:bg-orange-500/30 transition text-sm font-medium disabled:opacity-50">
                                    ⚠ Trigger Lapse
                                </button>
                            </div>
                            {triggerResult && (
                                <div className="mt-4 p-3 rounded-lg bg-primary-500/10 border border-primary-500/20 text-xs text-primary-300">
                                    <p className="font-semibold mb-1">Process Started</p>
                                    <p className="font-mono">Trace: {triggerResult.trace_id}</p>
                                </div>
                            )}
                        </div>

                        {history.length > 0 && (
                            <div className="glass-card p-6">
                                <h3 className="text-lg font-semibold text-white mb-6">Journey Timeline</h3>
                                <div className="space-y-6 relative before:absolute before:inset-y-0 before:left-3 before:w-0.5 before:bg-slate-700">
                                    {history.map((step, i) => (
                                        <div key={i} className="relative pl-10">
                                            <div className="absolute left-0 w-6 h-6 rounded-full bg-slate-800 border-4 border-primary-500 z-10"></div>
                                            <div className="text-xs text-primary-400 font-mono mb-1">{step.agent_id}</div>
                                            <div className="text-sm text-white font-medium mb-1">
                                                {step.agent_response?.status || step.agent_response?.outcome || step.agent_id}
                                            </div>
                                            {step.compliance_verdict && (
                                                <div className={`text-[10px] px-2 py-0.5 rounded inline-block font-bold ${step.compliance_verdict === 'PASS' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                                                    Safety: {step.compliance_verdict}
                                                </div>
                                            )}
                                            <div className="text-[10px] text-slate-500 mt-1">{step.created_at}</div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
