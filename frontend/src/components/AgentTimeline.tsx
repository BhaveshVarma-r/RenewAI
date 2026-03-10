export default function AgentTimeline({ steps }: { steps: any[] }) {
    return (
        <div className="space-y-2">
            {steps.map((step, i) => (
                <div key={i} className="flex items-start gap-3">
                    <div className="flex flex-col items-center">
                        <div className="w-3 h-3 rounded-full bg-primary-500 mt-1"></div>
                        {i < steps.length - 1 && <div className="w-0.5 h-8 bg-white/10"></div>}
                    </div>
                    <div className="flex-1 pb-2">
                        <p className="text-sm text-white font-medium">{step.agent_id}</p>
                        <p className="text-xs text-slate-400">{step.created_at}</p>
                    </div>
                </div>
            ))}
        </div>
    );
}
