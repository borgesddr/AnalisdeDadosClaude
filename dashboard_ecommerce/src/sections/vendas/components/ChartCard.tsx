import type { ReactNode } from 'react';

interface ChartCardProps {
  title: string;
  subtitle?: string;
  children: ReactNode;
  className?: string;
}

export default function ChartCard({
  title,
  subtitle,
  children,
  className = '',
}: ChartCardProps) {
  return (
    <div
      className={`bg-surface rounded-2xl border border-border shadow-sm p-6 ${className}`}
    >
      <h3 className="text-lg font-semibold text-text">{title}</h3>
      {subtitle && (
        <p className="mt-1 text-sm text-text-muted leading-relaxed">{subtitle}</p>
      )}
      <div className="mt-4">{children}</div>
    </div>
  );
}
