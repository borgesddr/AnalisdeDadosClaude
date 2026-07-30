import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { COLORS } from '../../../lib/theme';
import { formatNumber, formatPercent } from '../../../lib/format';
import type { CompetitorPosition } from '../hooks/usePricing';

type Props = { data: CompetitorPosition[] };

type TooltipEntry = { payload: CompetitorPosition };

function ChartTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: TooltipEntry[];
}) {
  if (!active || !payload || payload.length === 0) return null;
  const d = payload[0].payload;
  const total = d.maisCaros + d.maisBaratos;
  const share = total ? d.maisCaros / total : 0;
  return (
    <div className="bg-surface border border-border rounded-lg shadow-sm p-3 text-sm">
      <p className="font-semibold text-text">{d.nome}</p>
      <p className="text-danger">Somos mais caros: {formatNumber(d.maisCaros)}</p>
      <p className="text-success">Somos mais baratos: {formatNumber(d.maisBaratos)}</p>
      <p className="text-text-muted">
        Perdemos em {formatPercent(share)} das comparações
      </p>
    </div>
  );
}

export default function CompetitorPositionChart({ data }: Props) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} vertical={false} />
        <XAxis
          dataKey="nome"
          tick={{ fontSize: 12, fill: COLORS.textMuted }}
          stroke={COLORS.border}
        />
        <YAxis
          tick={{ fontSize: 12, fill: COLORS.textMuted }}
          stroke={COLORS.border}
        />
        <Tooltip content={<ChartTooltip />} cursor={{ fill: 'rgba(0,0,0,0.03)' }} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar
          dataKey="maisBaratos"
          name="Somos mais baratos"
          stackId="a"
          fill={COLORS.success}
          radius={[0, 0, 0, 0]}
        />
        <Bar
          dataKey="maisCaros"
          name="Somos mais caros"
          stackId="a"
          fill={COLORS.danger}
          radius={[4, 4, 0, 0]}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}
