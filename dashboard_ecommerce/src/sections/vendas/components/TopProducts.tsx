import { CATEGORY_COLORS, COLORS } from '../../../lib/theme';
import { formatBRL, formatNumber } from '../../../lib/format';
import type { RankItem } from '../hooks/useVendas';

export default function TopProducts({ data }: { data: RankItem[] }) {
  const max = Math.max(...data.map((d) => d.receita), 1);

  return (
    <ol className="space-y-4">
      {data.map((p, i) => (
        <li key={p.nome}>
          <div className="flex items-baseline justify-between gap-3">
            <span className="text-sm font-medium text-text">
              <span className="text-text-muted mr-2">{i + 1}.</span>
              {p.nome}
            </span>
            <span className="text-sm font-semibold text-text whitespace-nowrap">
              {formatBRL(p.receita)}
            </span>
          </div>
          <div className="mt-1 flex items-center gap-2">
            <div className="h-2 flex-1 rounded-full bg-bg overflow-hidden">
              <div
                className="h-full rounded-full"
                style={{
                  width: `${(p.receita / max) * 100}%`,
                  backgroundColor: CATEGORY_COLORS[p.categoria] ?? COLORS.neutral,
                }}
              />
            </div>
            <span className="text-xs text-text-muted whitespace-nowrap">
              {p.categoria} · {formatNumber(p.itens)} un.
            </span>
          </div>
        </li>
      ))}
    </ol>
  );
}
