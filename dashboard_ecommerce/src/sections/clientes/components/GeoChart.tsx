import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { COLORS } from '../../../lib/theme';
import { formatBRL } from '../../../lib/format';
import type { EstadoMetric } from '../hooks/useClientes';

export default function GeoChart({ data }: { data: EstadoMetric[] }) {
  const max = data[0]?.receita ?? 0;
  return (
    <ResponsiveContainer width="100%" height={480}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 24 }}>
        <CartesianGrid stroke={COLORS.border} horizontal={false} />
        <XAxis
          type="number"
          tick={{ fontSize: 12, fill: COLORS.textMuted }}
          tickFormatter={(v: number) => formatBRL(v)}
        />
        <YAxis
          type="category"
          dataKey="estado"
          width={36}
          tick={{ fontSize: 12, fill: COLORS.textMuted }}
        />
        <Tooltip
          formatter={(v: number) => [formatBRL(v), 'Receita']}
          labelFormatter={(l: string) => `Estado ${l}`}
        />
        <Bar dataKey="receita" radius={[0, 4, 4, 0]}>
          {data.map((d) => (
            <Cell
              key={d.estado}
              fill={d.receita === max ? COLORS.navy : COLORS.cyan}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
