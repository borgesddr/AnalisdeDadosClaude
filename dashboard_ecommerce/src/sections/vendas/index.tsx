import { useVendas } from './hooks/useVendas';
import { formatBRL, formatNumber, formatPercent } from '../../lib/format';
import KpiCard from './components/KpiCard';
import ChartCard from './components/ChartCard';
import RevenueTrendChart from './components/RevenueTrendChart';
import ChannelComparison from './components/ChannelComparison';
import CategoryRanking from './components/CategoryRanking';
import TopProducts from './components/TopProducts';

const CONTAINER = 'max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6';

function SectionHeader() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-text">Vendas &amp; Receita</h1>
      <p className="mt-1 text-sm text-text-muted leading-relaxed">
        Desempenho comercial de 13/dez/2025 a 11/jan/2026 — receita, canais e os
        produtos que puxam o resultado.
      </p>
    </div>
  );
}

export default function VendasSection() {
  const { data, loading, error } = useVendas();

  if (loading) {
    return (
      <div className={CONTAINER}>
        <SectionHeader />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="bg-surface rounded-2xl border border-border shadow-sm p-6 h-28 animate-pulse"
            />
          ))}
        </div>
        <div className="bg-surface rounded-2xl border border-border shadow-sm p-6 h-80 animate-pulse" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className={CONTAINER}>
        <SectionHeader />
        <div className="bg-surface rounded-2xl border border-danger/30 shadow-sm p-6 text-danger">
          Não foi possível carregar os dados de vendas.
          {error ? ` (${error})` : ''}
        </div>
      </div>
    );
  }

  const topCategoria = data.topCategorias[0];
  const pctTopCategoria = topCategoria
    ? topCategoria.receita / data.receitaTotal
    : 0;
  const melhorDia = [...data.serieDiaria].sort(
    (a, b) => b.receita - a.receita,
  )[0];

  return (
    <div className={CONTAINER}>
      <SectionHeader />

      {/* KPIs-resumo */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard label="Receita total" value={formatBRL(data.receitaTotal)} />
        <KpiCard label="Ticket médio" value={formatBRL(data.ticketMedio)} />
        <KpiCard
          label="Total de vendas"
          value={formatNumber(data.totalVendas)}
          hint={`${formatNumber(data.itensVendidos)} itens vendidos`}
        />
        <KpiCard
          label="Clientes ativos"
          value={formatNumber(data.clientesAtivos)}
        />
        <KpiCard
          label="Receita e-commerce"
          value={formatPercent(data.pctEcommerce)}
          hint="participação no faturamento"
        />
        <KpiCard
          label="Categoria líder"
          value={topCategoria?.categoria ?? '—'}
          hint={
            topCategoria
              ? `${formatBRL(topCategoria.receita)} · ${formatPercent(pctTopCategoria)}`
              : undefined
          }
        />
      </div>

      {/* Tendência temporal */}
      <ChartCard
        title="Evolução diária da receita"
        subtitle={
          melhorDia
            ? `Faturamento diário estável em torno do ticket médio; pico em ${
                melhorDia.dia.slice(8, 10) + '/' + melhorDia.dia.slice(5, 7)
              } com ${formatBRL(melhorDia.receita)}.`
            : undefined
        }
      >
        <RevenueTrendChart data={data.serieDiaria} />
      </ChartCard>

      {/* Comparação de canais */}
      <ChartCard
        title="Receita por canal"
        subtitle={`O e-commerce responde por ${formatPercent(
          data.pctEcommerce,
        )} da receita e ainda tem o maior ticket médio — o digital é o motor do negócio.`}
      >
        <ChannelComparison data={data.canais} />
      </ChartCard>

      {/* Rankings */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard
          title="Receita por categoria"
          subtitle={
            topCategoria
              ? `${topCategoria.categoria} lidera com ${formatPercent(
                  pctTopCategoria,
                )} do faturamento.`
              : undefined
          }
        >
          <CategoryRanking data={data.topCategorias} />
        </ChartCard>

        <ChartCard
          title="Top 5 produtos por receita"
          subtitle="Poucos SKUs concentram boa parte do faturamento — atenção a estoque e disponibilidade."
        >
          <TopProducts data={data.topProdutos} />
        </ChartCard>
      </div>
    </div>
  );
}
