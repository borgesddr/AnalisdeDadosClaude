import {
  Bar,
  BarChart,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { CATEGORY_COLORS, COLORS } from '../../../lib/theme';
import { formatBRL } from '../../../lib/format';
import type { RankItem } from '../hooks/useVendas';

export default function CategoryRanking({ data }: { data: RankItem[] }) {
  return (
    <ResponsiveContainer width="100%" height={Math.max(260, data.length * 34)}>
      <BarChart
        data={data}
        layout="vertical"
        margin={{ top: 4, right: 16, left: 8, bottom: 4 }}
      >
        <XAxis type="number" hide />
        <YAxis
          type="category"
          dataKey="categoria"
          width={92}
          tick={{ fill: COLORS.textMuted, fontSize: 12 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          cursor={{ fill: COLORS.border, opacity: 0.4 }}
          formatter={(v: number) => [formatBRL(v), 'Receita']}
          contentStyle={{
            borderRadius: 12,
            border: `1px solid ${COLORS.border}`,
            fontSize: 13,
          }}
        />
        <Bar dataKey="receita" radius={[0, 6, 6, 0]} barSize={18}>
          {data.map((d) => (
            <Cell
              key={d.categoria}
              fill={CATEGORY_COLORS[d.categoria] ?? COLORS.neutral}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
