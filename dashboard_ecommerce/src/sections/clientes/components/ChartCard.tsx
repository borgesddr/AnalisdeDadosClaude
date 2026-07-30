import type { ReactNode } from 'react';

type Props = {
  title: string;
  subtitle?: string;
  children: ReactNode;
};

export default function ChartCard({ title, subtitle, children }: Props) {
  return (
    <div className="bg-surface rounded-2xl border border-border shadow-sm p-6">
      <h2 className="text-lg font-semibold text-text">{title}</h2>
      {subtitle && <p className="mt-1 text-sm text-text-muted leading-relaxed">{subtitle}</p>}
      <div className="mt-4">{children}</div>
    </div>
  );
}
