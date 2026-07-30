import {
  Bar,
  BarChart,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { COLORS, CATEGORY_COLORS } from '../../../lib/theme';
import { formatBRL, formatPercent } from '../../../lib/format';
import type { RiskProduct } from '../hooks/usePricing';

type Props = { data: RiskProduct[] };

type Row = RiskProduct & { label: string };

type TooltipEntry = { payload: Row };

function ChartTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: TooltipEntry[];
}) {
  if (!active || !payload || payload.length === 0) return null;
  const d = payload[0].payload;
  return (
    <div className="bg-surface border border-border rounded-lg shadow-sm p-3 text-sm">
      <p className="font-semibold text-text">{d.nome}</p>
      <p className="text-text-muted">{d.categoria}</p>
      <p className="text-text-muted">
        Nosso preço: {formatBRL(d.preco)} · menor concorrente:{' '}
        {formatBRL(d.menorComp)}
      </p>
      <p className="text-danger">Sobrepreço: +{formatPercent(d.sobreprecoFrac)}</p>
    </div>
  );
}

export default function RiskRankingChart({ data }: Props) {
  const rows: Row[] = data.map((d) => ({
    ...d,
    label: d.nome.length > 24 ? `${d.nome.slice(0, 23)}…` : d.nome,
  }));

  return (
    <ResponsiveContainer width="100%" height={340}>
      <BarChart
        data={rows}
        layout="vertical"
        margin={{ top: 4, right: 24, left: 8, bottom: 4 }}
      >
        <XAxis
          type="number"
          tickFormatter={(v: number) => formatPercent(v)}
          tick={{ fontSize: 12, fill: COLORS.textMuted }}
          stroke={COLORS.border}
        />
        <YAxis
          type="category"
          dataKey="label"
          width={150}
          tick={{ fontSize: 11, fill: COLORS.textMuted }}
          stroke={COLORS.border}
        />
        <Tooltip content={<ChartTooltip />} cursor={{ fill: 'rgba(0,0,0,0.03)' }} />
        <Bar dataKey="sobreprecoFrac" radius={[0, 4, 4, 0]}>
          {rows.map((d) => (
            <Cell
              key={d.id}
              fill={CATEGORY_COLORS[d.categoria] ?? COLORS.danger}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
