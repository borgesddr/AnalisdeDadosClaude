import { usePricing } from './hooks/usePricing';
import { formatNumber, formatPercent } from '../../lib/format';
import KpiCard from './components/KpiCard';
import ChartCard from './components/ChartCard';
import CategoryPositioningChart from './components/CategoryPositioningChart';
import PriceParityScatter from './components/PriceParityScatter';
import CompetitorPositionChart from './components/CompetitorPositionChart';
import RiskRankingChart from './components/RiskRankingChart';

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-text">Pricing &amp; Margem</h1>
        <p className="mt-1 text-sm text-text-muted leading-relaxed">
          Posicionamento competitivo dos nossos preços frente aos marketplaces
          concorrentes.
        </p>
      </div>
      {children}
    </div>
  );
}

export default function PricingSection() {
  const { loading, error, data } = usePricing();

  if (loading) {
    return (
      <Shell>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="bg-surface rounded-2xl border border-border shadow-sm p-6 h-28 animate-pulse"
            />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="bg-surface rounded-2xl border border-border shadow-sm p-6 h-80 animate-pulse"
            />
          ))}
        </div>
      </Shell>
    );
  }

  if (error || !data) {
    return (
      <Shell>
        <div className="bg-surface rounded-2xl border border-border shadow-sm p-6 text-danger">
          Não foi possível carregar os dados de pricing. {error}
        </div>
      </Shell>
    );
  }

  const { summary, byCategory, parity, byCompetitor, risk } = data;
  const alerta = summary.categoriaAlerta;

  return (
    <Shell>
      {/* Resumo executivo */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          label="Gap médio vs mercado"
          value={`${summary.gapMedioFrac > 0 ? '+' : ''}${formatPercent(summary.gapMedioFrac)}`}
          hint="Nosso preço vs média dos concorrentes"
          tone={summary.gapMedioFrac > 0 ? 'danger' : 'success'}
        />
        <KpiCard
          label="Acima do mercado"
          value={formatPercent(summary.pctAcimaMercado)}
          hint={`${formatNumber(summary.nAcimaMercado)} de ${formatNumber(summary.nProdutos)} produtos mais caros que a média`}
          tone="warning"
        />
        <KpiCard
          label="Líderes de preço"
          value={formatNumber(summary.nLideres)}
          hint={`${formatPercent(summary.pctLideres)} igualam ou batem o menor concorrente`}
          tone="success"
        />
        <KpiCard
          label="Categoria em alerta"
          value={alerta ? alerta.categoria : '—'}
          hint={
            alerta
              ? `Gap médio de +${formatPercent(alerta.gapFrac)} vs mercado`
              : undefined
          }
          tone="danger"
        />
      </div>

      {/* Narrativa principal */}
      <div className="bg-surface rounded-2xl border border-border shadow-sm p-6">
        <p className="text-sm text-text leading-relaxed">
          Na média, praticamos preços{' '}
          <strong className="text-danger">
            {formatPercent(summary.gapMedioFrac)} acima
          </strong>{' '}
          dos {formatNumber(summary.nConcorrentes)} marketplaces monitorados, e{' '}
          <strong>{formatNumber(summary.nAcimaMercado)}</strong> dos{' '}
          {formatNumber(summary.nProdutos)} produtos estão mais caros que a média
          do mercado. O ofensor é claro:{' '}
          {alerta ? (
            <>
              a categoria <strong>{alerta.categoria}</strong> está{' '}
              <strong className="text-danger">
                +{formatPercent(alerta.gapFrac)}
              </strong>{' '}
              acima dos concorrentes — praticamente o dobro do preço de mercado.
            </>
          ) : null}{' '}
          Fora dela, o portfólio fica muito próximo da paridade, com{' '}
          <strong className="text-success">
            {formatNumber(summary.nLideres)} produtos
          </strong>{' '}
          liderando em preço.
        </p>
      </div>

      {/* Posicionamento por categoria + paridade */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard
          title="Posicionamento por categoria"
          subtitle="Gap médio de preço vs média dos concorrentes. Verde = mais baratos (bom); vermelho = mais caros."
        >
          <CategoryPositioningChart data={byCategory} />
        </ChartCard>
        <ChartCard
          title="Paridade de preços"
          subtitle="Cada ponto é um produto. Acima da linha tracejada = praticamos preço acima da média do mercado."
        >
          <PriceParityScatter data={parity} />
        </ChartCard>
      </div>

      {/* Posição vs concorrente + risco */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard
          title="Posição frente a cada concorrente"
          subtitle="Em quantas comparações somos mais caros (vermelho) ou mais baratos (verde) que cada marketplace."
        >
          <CompetitorPositionChart data={byCompetitor} />
        </ChartCard>
        <ChartCard
          title="Produtos com maior risco de competitividade"
          subtitle="Maior sobrepreço vs o menor concorrente disponível — candidatos prioritários a reprecificação."
        >
          <RiskRankingChart data={risk} />
        </ChartCard>
      </div>
    </Shell>
  );
}
