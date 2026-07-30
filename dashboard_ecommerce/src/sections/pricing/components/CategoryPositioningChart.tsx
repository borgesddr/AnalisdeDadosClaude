import {
  Bar,
  BarChart,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { COLORS } from '../../../lib/theme';
import { formatPercent } from '../../../lib/format';
import type { CategoryPosition } from '../hooks/usePricing';

type Props = { data: CategoryPosition[] };

type TooltipEntry = { payload: CategoryPosition };

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
      <p className="font-semibold text-text">{d.categoria}</p>
      <p className="text-text-muted">
        Gap médio:{' '}
        <span className={d.gapFrac > 0 ? 'text-danger' : 'text-success'}>
          {d.gapFrac > 0 ? '+' : ''}
          {formatPercent(d.gapFrac)}
        </span>
      </p>
      <p className="text-text-muted">
        {d.maisCaros} de {d.n} acima do mercado
      </p>
    </div>
  );
}

export default function CategoryPositioningChart({ data }: Props) {
  return (
    <ResponsiveContainer width="100%" height={340}>
      <BarChart
        data={data}
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
          dataKey="categoria"
          width={92}
          tick={{ fontSize: 12, fill: COLORS.textMuted }}
          stroke={COLORS.border}
        />
        <Tooltip content={<ChartTooltip />} cursor={{ fill: 'rgba(0,0,0,0.03)' }} />
        <ReferenceLine x={0} stroke={COLORS.neutral} />
        <Bar dataKey="gapFrac" radius={[0, 4, 4, 0]}>
          {data.map((d) => (
            <Cell
              key={d.categoria}
              fill={d.gapFrac > 0 ? COLORS.danger : COLORS.success}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
