import { useState, useEffect } from 'react';
import { getKPISummary, triggerBatchScan } from '../api/client';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

interface KPIData {
    total_interactions: number; conversions: number; escalations: number;
    persistency_rate: number; escalation_rate: number; cost_per_renewal: number;
    channel_performance: any[]; critique_stats: any; timestamp: string;
}

const COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b'];

export default function Dashboard() {
    const [kpi, setKpi] = useState<KPIData | null>(null);
    const [loading, setLoading] = useState(true);

    const fetchKPI = async () => {
        try {
            const res = await getKPISummary();
            setKpi(res.data);
        } catch (e) { console.error(e); }
        finally { setLoading(false); }
    };

    const handleScan = async () => {
        setLoading(true);
        try {
            await triggerBatchScan(45);
            await fetchKPI();
        } catch (e) { console.error(e); }
        finally { setLoading(false); }
    };

    useEffect(() => { fetchKPI(); const iv = setInterval(fetchKPI, 30000); return () => clearInterval(iv); }, []);

    const kpiCards = kpi ? [
        { label: 'Persistency Rate', value: `${kpi.persistency_rate}%`, icon: '📈', color: 'from-green-500 to-emerald-600' },
        { label: 'Total Interactions', value: kpi.total_interactions, icon: '💬', color: 'from-blue-500 to-primary-600' },
        { label: 'Conversions', value: kpi.conversions, icon: '✅', color: 'from-purple-500 to-accent-600' },
        { label: 'Escalation Rate', value: `${kpi.escalation_rate}%`, icon: '🚨', color: 'from-orange-500 to-red-600' },
        { label: 'Cost/Renewal', value: `₹${kpi.cost_per_renewal}`, icon: '💰', color: 'from-cyan-500 to-blue-600' },
        { label: 'Critique Avg', value: kpi.critique_stats?.avg_score || 0, icon: '⭐', color: 'from-yellow-500 to-orange-600' },
    ] : [];

    const channelData = kpi?.channel_performance?.map(ch => ({
        name: ch.channel || 'N/A', attempts: ch.attempts || 0, conversions: ch.conversions || 0, escalations: ch.escalations || 0,
    })) || [];

    return (
        <div className="animate-fadeIn">
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-white">Dashboard</h1>
                    <p className="text-slate-400 mt-1">Real-time KPI monitoring</p>
                </div>
                <div className="flex gap-3">
                    <button onClick={handleScan} disabled={loading}
                        className="px-4 py-2 rounded-xl bg-accent-500/20 text-accent-400 hover:bg-accent-500/30 transition text-sm font-medium border border-accent-500/30 disabled:opacity-50">
                        🚀 Run T-45 Scan
                    </button>
                    <button onClick={fetchKPI} className="px-4 py-2 rounded-xl bg-primary-500/20 text-primary-400 hover:bg-primary-500/30 transition text-sm font-medium">↻ Refresh</button>
                </div>
            </div>

            {loading ? (
                <div className="flex items-center justify-center h-64"><div className="text-slate-400">Loading metrics...</div></div>
            ) : (
                <>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
                        {kpiCards.map((card, i) => (
                            <div key={i} className="glass-card p-6 hover:scale-[1.02] transition-transform duration-200">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-slate-400 mb-1">{card.label}</p>
                                        <p className="text-3xl font-bold text-white">{card.value}</p>
                                    </div>
                                    <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${card.color} flex items-center justify-center text-xl`}>{card.icon}</div>
                                </div>
                            </div>
                        ))}
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <div className="glass-card p-6">
                            <h3 className="text-lg font-semibold text-white mb-4">Channel Performance</h3>
                            <ResponsiveContainer width="100%" height={300}>
                                <BarChart data={channelData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                    <XAxis dataKey="name" stroke="#94a3b8" />
                                    <YAxis stroke="#94a3b8" />
                                    <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#fff' }} />
                                    <Bar dataKey="attempts" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                                    <Bar dataKey="conversions" fill="#10b981" radius={[4, 4, 0, 0]} />
                                    <Bar dataKey="escalations" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                        <div className="glass-card p-6">
                            <h3 className="text-lg font-semibold text-white mb-4">Critique Results</h3>
                            <ResponsiveContainer width="100%" height={300}>
                                <PieChart>
                                    <Pie data={[
                                        { name: 'Approved', value: kpi?.critique_stats?.approved || 1 },
                                        { name: 'Rejected', value: kpi?.critique_stats?.rejected || 0 },
                                    ]} dataKey="value" cx="50%" cy="50%" outerRadius={100} label>
                                        {[0, 1].map((_, i) => <Cell key={i} fill={COLORS[i]} />)}
                                    </Pie>
                                    <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#fff' }} />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}
