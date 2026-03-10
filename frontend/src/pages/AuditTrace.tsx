import { useState } from 'react';
import { getAuditTrace, getAuditPolicy } from '../api/client';

interface AuditStep {
    id: number; trace_id: string; step_sequence: number; agent_id: string;
    policy_id: string; customer_id: string; agent_input: any; agent_response: any;
    critique_result: any; critique_score: number; compliance_verdict: string; created_at: string;
}

export default function AuditTrace() {
    const [searchId, setSearchId] = useState('');
    const [searchType, setSearchType] = useState<'trace' | 'policy'>('trace');
    const [steps, setSteps] = useState<AuditStep[]>([]);
    const [expanded, setExpanded] = useState<number | null>(null);
    const [loading, setLoading] = useState(false);

    const handleSearch = async () => {
        if (!searchId) return;
        setLoading(true);
        try {
            const res = searchType === 'trace' ? await getAuditTrace(searchId) : await getAuditPolicy(searchId);
            setSteps(res.data.steps || res.data.interactions || []);
        } catch (e) { console.error(e); setSteps([]); }
        finally { setLoading(false); }
    };

    return (
        <div className="animate-fadeIn">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-white">Audit Trail</h1>
                <p className="text-slate-400 mt-1">Track every agent action step-by-step</p>
            </div>

            <div className="glass-card p-6 mb-6">
                <div className="flex gap-3">
                    <select value={searchType} onChange={e => setSearchType(e.target.value as any)}
                        className="px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-white focus:outline-none focus:ring-2 focus:ring-primary-500">
                        <option value="trace">Trace ID</option>
                        <option value="policy">Policy ID</option>
                    </select>
                    <input value={searchId} onChange={e => setSearchId(e.target.value)} placeholder={searchType === 'trace' ? 'Enter trace ID...' : 'Enter policy ID (e.g. POL001)...'}
                        className="flex-1 px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
                        onKeyDown={e => e.key === 'Enter' && handleSearch()} />
                    <button onClick={handleSearch} className="px-6 py-2 rounded-xl bg-primary-500 text-white font-medium hover:bg-primary-600 transition">Search</button>
                </div>
            </div>

            {loading ? <p className="text-slate-400">Searching...</p> :
                steps.length === 0 ? <div className="glass-card p-8 text-center text-slate-400">No audit entries found. Try searching by trace or policy ID.</div> : (
                    <div className="space-y-3">
                        {steps.map((step, i) => (
                            <div key={step.id || i} className="glass-card overflow-hidden">
                                <div onClick={() => setExpanded(expanded === i ? null : i)}
                                    className="p-4 cursor-pointer hover:bg-white/5 transition flex items-center justify-between">
                                    <div className="flex items-center gap-4">
                                        <div className="w-8 h-8 rounded-full bg-primary-500/20 flex items-center justify-center text-primary-400 text-sm font-bold">{step.step_sequence}</div>
                                        <div>
                                            <span className="text-white font-medium">{step.agent_id}</span>
                                            <span className="text-slate-400 text-sm ml-3">{step.policy_id}</span>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        {step.critique_score != null && (
                                            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${step.critique_score >= 7 ? 'badge-low' : step.critique_score >= 5 ? 'badge-medium' : 'badge-critical'}`}>
                                                Score: {step.critique_score}
                                            </span>
                                        )}
                                        {step.compliance_verdict && (
                                            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${step.compliance_verdict === 'PASS' ? 'badge-low' : step.compliance_verdict === 'FAIL' ? 'badge-high' : 'badge-critical'}`}>
                                                {step.compliance_verdict}
                                            </span>
                                        )}
                                        <span className="text-slate-500 text-xs">{expanded === i ? '▲' : '▼'}</span>
                                    </div>
                                </div>
                                {expanded === i && (
                                    <div className="border-t border-white/10 p-4 bg-white/5">
                                        <div className="grid grid-cols-2 gap-4">
                                            <div><label className="text-xs text-slate-400 block mb-1">Input</label>
                                                <pre className="text-xs text-slate-300 bg-black/20 p-3 rounded-lg overflow-auto max-h-48">{JSON.stringify(step.agent_input, null, 2)}</pre>
                                            </div>
                                            <div><label className="text-xs text-slate-400 block mb-1">Response</label>
                                                <pre className="text-xs text-slate-300 bg-black/20 p-3 rounded-lg overflow-auto max-h-48">{JSON.stringify(step.agent_response, null, 2)}</pre>
                                            </div>
                                        </div>
                                        {step.critique_result && (
                                            <div className="mt-3"><label className="text-xs text-slate-400 block mb-1">Critique</label>
                                                <pre className="text-xs text-slate-300 bg-black/20 p-3 rounded-lg overflow-auto max-h-32">{JSON.stringify(step.critique_result, null, 2)}</pre>
                                            </div>
                                        )}
                                        <p className="text-xs text-slate-500 mt-2">{step.created_at}</p>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
        </div>
    );
}
