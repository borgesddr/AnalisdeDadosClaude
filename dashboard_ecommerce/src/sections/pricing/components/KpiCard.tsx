type Tone = 'neutral' | 'success' | 'danger' | 'warning';

const toneClass: Record<Tone, string> = {
  neutral: 'text-text',
  success: 'text-success',
  danger: 'text-danger',
  warning: 'text-warning',
};

type Props = {
  label: string;
  value: string;
  hint?: string;
  tone?: Tone;
};

export default function KpiCard({ label, value, hint, tone = 'neutral' }: Props) {
  return (
    <div className="bg-surface rounded-2xl border border-border shadow-sm p-6">
      <p className="text-xs text-text-muted uppercase tracking-wide">{label}</p>
      <p className={`mt-2 text-3xl font-bold ${toneClass[tone]}`}>{value}</p>
      {hint ? <p className="mt-1 text-xs text-text-muted">{hint}</p> : null}
    </div>
  );
}
