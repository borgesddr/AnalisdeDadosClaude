import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { COLORS } from '../../../lib/theme';
import { formatBRL } from '../../../lib/format';
import type { DayPoint } from '../hooks/useVendas';

const shortDay = (iso: string) => {
  const [, m, d] = iso.split('-');
  return `${d}/${m}`;
};

export default function RevenueTrendChart({ data }: { data: DayPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={data} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
        <defs>
          <linearGradient id="receitaFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={COLORS.cyan} stopOpacity={0.35} />
            <stop offset="100%" stopColor={COLORS.cyan} stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke={COLORS.border} vertical={false} />
        <XAxis
          dataKey="dia"
          tickFormatter={shortDay}
          tick={{ fill: COLORS.textMuted, fontSize: 12 }}
          axisLine={{ stroke: COLORS.border }}
          tickLine={false}
          minTickGap={16}
        />
        <YAxis
          tickFormatter={(v) => `R$${(v / 1000).toFixed(0)}k`}
          tick={{ fill: COLORS.textMuted, fontSize: 12 }}
          axisLine={false}
          tickLine={false}
          width={52}
        />
        <Tooltip
          formatter={(v: number) => [formatBRL(v), 'Receita']}
          labelFormatter={(l: string) => `Dia ${shortDay(l)}`}
          contentStyle={{
            borderRadius: 12,
            border: `1px solid ${COLORS.border}`,
            fontSize: 13,
          }}
        />
        <Area
          type="monotone"
          dataKey="receita"
          stroke={COLORS.cyan}
          strokeWidth={2}
          fill="url(#receitaFill)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
