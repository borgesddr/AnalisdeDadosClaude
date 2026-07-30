interface KpiCardProps {
  label: string;
  value: string;
  hint?: string;
}

export default function KpiCard({ label, value, hint }: KpiCardProps) {
  return (
    <div className="bg-surface rounded-2xl border border-border shadow-sm p-6">
      <p className="text-xs text-text-muted uppercase tracking-wide">{label}</p>
      <p className="mt-2 text-3xl font-bold text-text">{value}</p>
      {hint && <p className="mt-1 text-xs text-text-muted">{hint}</p>}
    </div>
  );
}
