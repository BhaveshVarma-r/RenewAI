export default function CritiqueScoreBadge({ score, label }: { score: number; label?: string }) {
    const color = score >= 8 ? 'badge-low' : score >= 6 ? 'badge-medium' : score >= 4 ? 'badge-high' : 'badge-critical';
    return (
        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${color}`}>
            {label ? `${label}: ` : ''}{score.toFixed(1)}
        </span>
    );
}
