import { useState, useEffect } from 'react';
import { getPendingQueue, resolveQueueCase } from '../api/client';

interface QueueCase {
    queue_id: string; trace_id: string; policy_id: string; priority: number;
    reason: string; context_briefing: string; status: string; assigned_to: string;
    created_at: string; resolved_at: string | null;
}

const priorityLabels: Record<number, { label: string; class: string }> = {
    1: { label: 'CRITICAL', class: 'badge-critical' },
    2: { label: 'HIGH', class: 'badge-high' },
    3: { label: 'MEDIUM', class: 'badge-medium' },
    4: { label: 'LOW', class: 'badge-low' },
    5: { label: 'INFO', class: 'badge-low' },
};

export default function HumanQueue() {
    const [cases, setCases] = useState<QueueCase[]>([]);
    const [selected, setSelected] = useState<QueueCase | null>(null);
    const [resolution, setResolution] = useState('');
    const [notes, setNotes] = useState('');
    const [loading, setLoading] = useState(true);

    const fetchCases = async () => {
        try { const res = await getPendingQueue(); setCases(res.data.cases || []); }
        catch (e) { console.error(e); } finally { setLoading(false); }
    };

    useEffect(() => { fetchCases(); }, []);

    const handleResolve = async () => {
        if (!selected || !resolution) return;
        try {
            await resolveQueueCase(selected.queue_id, resolution, notes);
            setSelected(null); setResolution(''); setNotes('');
            fetchCases();
        } catch (e) { console.error(e); }
    };

    return (
        <div className="animate-fadeIn">
            <div className="flex items-center justify-between mb-8">
                <div><h1 className="text-3xl font-bold text-white">Human Queue</h1><p className="text-slate-400 mt-1">Escalated cases requiring specialist attention</p></div>
                <button onClick={fetchCases} className="px-4 py-2 rounded-xl bg-primary-500/20 text-primary-400 hover:bg-primary-500/30 transition text-sm font-medium">↻ Refresh</button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="space-y-3">
                    {loading ? <p className="text-slate-400">Loading...</p> :
                        cases.length === 0 ? <div className="glass-card p-8 text-center text-slate-400">No pending cases 🎉</div> :
                            cases.map(c => (
                                <div key={c.queue_id} onClick={() => setSelected(c)}
                                    className={`glass-card p-4 cursor-pointer hover:bg-white/10 transition ${selected?.queue_id === c.queue_id ? 'ring-2 ring-primary-500' : ''}`}>
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="font-mono text-sm text-slate-300">{c.queue_id}</span>
                                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${priorityLabels[c.priority]?.class || 'badge-medium'}`}>
                                            {priorityLabels[c.priority]?.label || 'MEDIUM'}
                                        </span>
                                    </div>
                                    <p className="text-sm text-slate-300 mb-1">Policy: <span className="text-white font-medium">{c.policy_id}</span></p>
                                    <p className="text-xs text-slate-400 truncate">{c.reason}</p>
                                    <p className="text-xs text-slate-500 mt-1">{new Date(c.created_at).toLocaleString()}</p>
                                </div>
                            ))}
                </div>

                {selected && (
                    <div className="glass-card p-6">
                        <h3 className="text-lg font-semibold text-white mb-4">Case Details</h3>
                        <div className="space-y-3 mb-6">
                            <div><label className="text-xs text-slate-400">Queue ID</label><p className="text-white font-mono">{selected.queue_id}</p></div>
                            <div><label className="text-xs text-slate-400">Policy</label><p className="text-white">{selected.policy_id}</p></div>
                            <div><label className="text-xs text-slate-400">Reason</label><p className="text-white text-sm">{selected.reason}</p></div>
                            <div><label className="text-xs text-slate-400">AI Briefing</label>
                                <p className="text-slate-300 text-sm bg-white/5 p-3 rounded-lg mt-1">{selected.context_briefing}</p>
                            </div>
                        </div>
                        <div className="space-y-3">
                            <input value={resolution} onChange={e => setResolution(e.target.value)} placeholder="Resolution..."
                                className="w-full px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500" />
                            <textarea value={notes} onChange={e => setNotes(e.target.value)} placeholder="Specialist notes..."
                                className="w-full px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500 h-24 resize-none" />
                            <button onClick={handleResolve} className="w-full py-3 rounded-xl bg-gradient-to-r from-green-500 to-emerald-600 text-white font-semibold hover:opacity-90 transition">
                                ✓ Resolve Case
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
