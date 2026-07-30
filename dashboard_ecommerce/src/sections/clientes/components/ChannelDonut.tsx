import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';
import { CHANNEL_COLORS } from '../../../lib/theme';
import { formatBRL } from '../../../lib/format';
import type { CanalMetric } from '../hooks/useClientes';

const LABEL: Record<string, string> = {
  ecommerce: 'E-commerce',
  loja_fisica: 'Loja física',
};

export default function ChannelDonut({ data }: { data: CanalMetric[] }) {
  const rows = data.map((c) => ({ ...c, nome: LABEL[c.canal] }));
  return (
    <ResponsiveContainer width="100%" height={340}>
      <PieChart>
        <Pie
          data={rows}
          dataKey="receita"
          nameKey="nome"
          innerRadius={70}
          outerRadius={110}
          paddingAngle={2}
        >
          {rows.map((r) => (
            <Cell key={r.canal} fill={CHANNEL_COLORS[r.canal]} />
          ))}
        </Pie>
        <Tooltip formatter={(v: number) => [formatBRL(v), 'Receita']} />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}
