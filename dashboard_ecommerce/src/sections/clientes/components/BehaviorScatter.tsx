import {
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from 'recharts';
import { COLORS } from '../../../lib/theme';
import { formatBRL, formatNumber } from '../../../lib/format';
import type { ClienteMetric } from '../hooks/useClientes';

type Props = {
  data: ClienteMetric[];
  ticketMedio: number;
  frequenciaMedia: number;
};

export default function BehaviorScatter({ data, ticketMedio, frequenciaMedia }: Props) {
  const pontos = data.map((c) => ({
    x: c.compras,
    y: c.ticketMedio,
    z: c.receita,
    nome: c.nome,
  }));

  return (
    <ResponsiveContainer width="100%" height={340}>
      <ScatterChart margin={{ left: 8, right: 24, top: 8, bottom: 8 }}>
        <CartesianGrid stroke={COLORS.border} />
        <XAxis
          type="number"
          dataKey="x"
          name="Compras"
          tick={{ fontSize: 12, fill: COLORS.textMuted }}
          label={{ value: 'Frequência (nº de compras)', position: 'insideBottom', offset: -4, fontSize: 12, fill: COLORS.textMuted }}
        />
        <YAxis
          type="number"
          dataKey="y"
          name="Ticket médio"
          tick={{ fontSize: 12, fill: COLORS.textMuted }}
          tickFormatter={(v: number) => formatBRL(v)}
          width={80}
        />
        <ZAxis type="number" dataKey="z" range={[40, 400]} name="Receita" />
        <Tooltip
          cursor={{ strokeDasharray: '3 3' }}
          formatter={(value: number, name: string) => {
            if (name === 'Ticket médio' || name === 'Receita') return [formatBRL(value), name];
            return [formatNumber(value), name];
          }}
          labelFormatter={() => ''}
          content={({ payload }) => {
            if (!payload || !payload.length) return null;
            const p = payload[0].payload as { nome: string; x: number; y: number; z: number };
            return (
              <div className="bg-surface border border-border rounded-lg shadow-sm p-3 text-sm">
                <p className="font-semibold text-text">{p.nome}</p>
                <p className="text-text-muted">Compras: {formatNumber(p.x)}</p>
                <p className="text-text-muted">Ticket médio: {formatBRL(p.y)}</p>
                <p className="text-text-muted">Receita: {formatBRL(p.z)}</p>
              </div>
            );
          }}
        />
        <Scatter data={pontos}>
          {pontos.map((p, i) => (
            <Cell
              key={i}
              fill={p.x >= frequenciaMedia && p.y >= ticketMedio ? COLORS.success : COLORS.cyan}
              fillOpacity={0.75}
            />
          ))}
        </Scatter>
      </ScatterChart>
    </ResponsiveContainer>
  );
}
