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
import type { ClienteMetric } from '../hooks/useClientes';

const primeiroNome = (nome: string) => {
  const partes = nome.replace(/^(Dr\.|Dra\.|Sr\.|Sra\.|Srta\.)\s*/i, '').split(' ');
  return partes.slice(0, 2).join(' ');
};

export default function TopClientsChart({ data }: { data: ClienteMetric[] }) {
  const rows = data.map((c) => ({ ...c, label: primeiroNome(c.nome) }));
  const max = rows[0]?.receita ?? 0;
  return (
    <ResponsiveContainer width="100%" height={400}>
      <BarChart data={rows} layout="vertical" margin={{ left: 8, right: 24 }}>
        <CartesianGrid stroke={COLORS.border} horizontal={false} />
        <XAxis
          type="number"
          tick={{ fontSize: 12, fill: COLORS.textMuted }}
          tickFormatter={(v: number) => formatBRL(v)}
        />
        <YAxis
          type="category"
          dataKey="label"
          width={130}
          tick={{ fontSize: 12, fill: COLORS.textMuted }}
        />
        <Tooltip
          formatter={(v: number) => [formatBRL(v), 'Receita']}
          labelFormatter={(l: string) => l}
        />
        <Bar dataKey="receita" radius={[0, 4, 4, 0]}>
          {rows.map((d) => (
            <Cell key={d.id} fill={d.receita === max ? COLORS.orange : COLORS.navy} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
