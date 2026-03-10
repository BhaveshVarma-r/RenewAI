export default function KPICard({ label, value, icon, color }: {
    label: string; value: string | number; icon: string; color: string;
}) {
    return (
        <div className="glass-card p-6 hover:scale-[1.02] transition-transform duration-200">
            <div className="flex items-center justify-between">
                <div>
                    <p className="text-sm text-slate-400 mb-1">{label}</p>
                    <p className="text-3xl font-bold text-white">{value}</p>
                </div>
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${color} flex items-center justify-center text-xl`}>{icon}</div>
            </div>
        </div>
    );
}
