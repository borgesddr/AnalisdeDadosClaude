import {
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from 'recharts';
import { COLORS } from '../../../lib/theme';
import { formatBRL } from '../../../lib/format';
import type { ParityPoint } from '../hooks/usePricing';

type Props = { data: ParityPoint[] };

type TooltipEntry = { payload: ParityPoint };

function ChartTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: TooltipEntry[];
}) {
  if (!active || !payload || payload.length === 0) return null;
  const d = payload[0].payload;
  const maisCaro = d.preco > d.avgComp;
  return (
    <div className="bg-surface border border-border rounded-lg shadow-sm p-3 text-sm">
      <p className="font-semibold text-text">{d.nome}</p>
      <p className="text-text-muted">{d.categoria}</p>
      <p className="text-text-muted">
        Nosso preço: {formatBRL(d.preco)} · média concorrentes:{' '}
        {formatBRL(d.avgComp)}
      </p>
      <p className={maisCaro ? 'text-danger' : 'text-success'}>
        {maisCaro ? 'Acima do mercado' : 'Igual ou abaixo do mercado'}
      </p>
    </div>
  );
}

export default function PriceParityScatter({ data }: Props) {
  const acima = data.filter((d) => d.preco > d.avgComp);
  const abaixo = data.filter((d) => d.preco <= d.avgComp);

  const max = Math.max(
    ...data.map((d) => Math.max(d.preco, d.avgComp)),
    1,
  );
  const parity = [
    { avgComp: 0, preco: 0 },
    { avgComp: max, preco: max },
  ];

  return (
    <ResponsiveContainer width="100%" height={300}>
      <ScatterChart margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} />
        <XAxis
          type="number"
          dataKey="avgComp"
          name="Média concorrentes"
          domain={[0, Math.ceil(max)]}
          tickFormatter={(v: number) => formatBRL(v)}
          tick={{ fontSize: 11, fill: COLORS.textMuted }}
          stroke={COLORS.border}
        />
        <YAxis
          type="number"
          dataKey="preco"
          name="Nosso preço"
          domain={[0, Math.ceil(max)]}
          tickFormatter={(v: number) => formatBRL(v)}
          tick={{ fontSize: 11, fill: COLORS.textMuted }}
          stroke={COLORS.border}
          width={78}
        />
        <ZAxis range={[40, 40]} />
        <Tooltip content={<ChartTooltip />} cursor={{ strokeDasharray: '3 3' }} />
        <Scatter
          name="Linha de paridade"
          data={parity}
          line={{ stroke: COLORS.neutral, strokeDasharray: '5 5' }}
          fill="none"
          shape={() => <g />}
        />
        <Scatter name="Acima do mercado" data={acima} fill={COLORS.danger} fillOpacity={0.7} />
        <Scatter
          name="Igual ou abaixo"
          data={abaixo}
          fill={COLORS.success}
          fillOpacity={0.7}
        />
      </ScatterChart>
    </ResponsiveContainer>
  );
}
