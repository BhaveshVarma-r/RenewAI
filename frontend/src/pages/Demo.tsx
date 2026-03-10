import { useState } from 'react';
import { runDemo } from '../api/client';

interface DemoResult {
    policy_id: string; customer_name: string; risk_tier: string;
    channel: string; status: string; converted: boolean; escalated: boolean; trace_id: string;
}

const tierColors: Record<string, string> = { low: 'badge-low', medium: 'badge-medium', high: 'badge-high', critical: 'badge-critical' };

export default function Demo() {
    const [running, setRunning] = useState(false);
    const [results, setResults] = useState<DemoResult[]>([]);
    const [summary, setSummary] = useState<any>(null);

    const handleRun = async () => {
        setRunning(true); setResults([]); setSummary(null);
        try {
            const res = await runDemo();
            setResults(res.data.results || []);
            setSummary({ total: res.data.total_policies, converted: res.data.converted, escalated: res.data.escalated, rate: res.data.conversion_rate });
        } catch (e) { console.error(e); }
        finally { setRunning(false); }
    };

    return (
        <div className="animate-fadeIn">
            <div className="flex items-center justify-between mb-8">
                <div><h1 className="text-3xl font-bold text-white">Demo Runner</h1><p className="text-slate-400 mt-1">Run the full RenewAI pipeline across all sample policies</p></div>
                <button onClick={handleRun} disabled={running}
                    className="px-6 py-3 rounded-xl bg-gradient-to-r from-primary-500 to-accent-500 text-white font-semibold hover:opacity-90 transition disabled:opacity-50 flex items-center gap-2">
                    {running ? <><span className="animate-spin">⏳</span> Running...</> : <><span>🚀</span> Run Demo</>}
                </button>
            </div>

            {summary && (
                <div className="grid grid-cols-4 gap-4 mb-6">
                    {[
                        { label: 'Total Processed', value: summary.total, color: 'from-blue-500 to-primary-600' },
                        { label: 'Converted', value: summary.converted, color: 'from-green-500 to-emerald-600' },
                        { label: 'Escalated', value: summary.escalated, color: 'from-orange-500 to-red-600' },
                        { label: 'Conversion Rate', value: summary.rate, color: 'from-purple-500 to-accent-600' },
                    ].map((s, i) => (
                        <div key={i} className="glass-card p-4">
                            <p className="text-sm text-slate-400">{s.label}</p>
                            <p className="text-2xl font-bold text-white mt-1">{s.value}</p>
                        </div>
                    ))}
                </div>
            )}

            {results.length > 0 && (
                <div className="glass-card overflow-hidden">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="border-b border-white/10">
                                {['Policy', 'Customer', 'Risk', 'Channel', 'Status', 'Converted', 'Escalated'].map(h => (
                                    <th key={h} className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase">{h}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {results.map(r => (
                                <tr key={r.policy_id} className="border-b border-white/5 hover:bg-white/5 transition">
                                    <td className="px-4 py-3 font-mono text-primary-400">{r.policy_id}</td>
                                    <td className="px-4 py-3 text-white">{r.customer_name}</td>
                                    <td className="px-4 py-3"><span className={`px-2 py-0.5 rounded-full text-xs ${tierColors[r.risk_tier] || ''}`}>{r.risk_tier}</span></td>
                                    <td className="px-4 py-3 text-slate-300">{r.channel || '—'}</td>
                                    <td className="px-4 py-3 text-slate-300">{r.status}</td>
                                    <td className="px-4 py-3">{r.converted ? '✅' : '❌'}</td>
                                    <td className="px-4 py-3">{r.escalated ? '🚨' : '—'}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {!running && results.length === 0 && (
                <div className="glass-card p-12 text-center">
                    <p className="text-6xl mb-4">🎯</p>
                    <p className="text-xl text-white font-semibold mb-2">Ready to run the demo</p>
                    <p className="text-slate-400">Click "Run Demo" to process all sample policies through the AI renewal pipeline</p>
                </div>
            )}
        </div>
    );
}
