import {
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';
import { CHANNEL_COLORS, COLORS } from '../../../lib/theme';
import { formatBRL, formatPercent } from '../../../lib/format';
import type { ChannelStat } from '../hooks/useVendas';

const LABELS: Record<string, string> = {
  ecommerce: 'E-commerce',
  loja_fisica: 'Loja física',
};

const label = (canal: string) => LABELS[canal] ?? canal;

export default function ChannelComparison({ data }: { data: ChannelStat[] }) {
  const pieData = data.map((c) => ({
    name: label(c.canal),
    canal: c.canal,
    value: c.receita,
  }));

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 items-center">
      <ResponsiveContainer width="100%" height={240}>
        <PieChart>
          <Pie
            data={pieData}
            dataKey="value"
            nameKey="name"
            innerRadius={55}
            outerRadius={90}
            paddingAngle={2}
          >
            {pieData.map((d) => (
              <Cell key={d.canal} fill={CHANNEL_COLORS[d.canal] ?? COLORS.neutral} />
            ))}
          </Pie>
          <Tooltip
            formatter={(v: number) => formatBRL(v)}
            contentStyle={{
              borderRadius: 12,
              border: `1px solid ${COLORS.border}`,
              fontSize: 13,
            }}
          />
          <Legend
            verticalAlign="bottom"
            iconType="circle"
            wrapperStyle={{ fontSize: 12, color: COLORS.textMuted }}
          />
        </PieChart>
      </ResponsiveContainer>

      <div className="space-y-3">
        {data.map((c) => (
          <div
            key={c.canal}
            className="rounded-xl border border-border p-4"
          >
            <div className="flex items-center gap-2">
              <span
                className="inline-block h-3 w-3 rounded-full"
                style={{ backgroundColor: CHANNEL_COLORS[c.canal] ?? COLORS.neutral }}
              />
              <span className="text-sm font-semibold text-text">
                {label(c.canal)}
              </span>
              <span className="ml-auto text-sm font-semibold text-text">
                {formatPercent(c.pctReceita)}
              </span>
            </div>
            <dl className="mt-3 grid grid-cols-2 gap-2 text-sm">
              <div>
                <dt className="text-xs text-text-muted">Receita</dt>
                <dd className="font-semibold text-text">{formatBRL(c.receita)}</dd>
              </div>
              <div>
                <dt className="text-xs text-text-muted">Ticket médio</dt>
                <dd className="font-semibold text-text">
                  {formatBRL(c.ticketMedio)}
                </dd>
              </div>
            </dl>
          </div>
        ))}
      </div>
    </div>
  );
}
