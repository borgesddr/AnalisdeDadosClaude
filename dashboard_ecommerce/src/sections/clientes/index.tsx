import { useClientes } from './hooks/useClientes';
import { formatBRL, formatNumber, formatPercent } from '../../lib/format';
import KpiCard from './components/KpiCard';
import ChartCard from './components/ChartCard';
import GeoChart from './components/GeoChart';
import TopClientsChart from './components/TopClientsChart';
import BehaviorScatter from './components/BehaviorScatter';
import ChannelDonut from './components/ChannelDonut';

function Skeleton() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="bg-surface rounded-2xl border border-border shadow-sm p-6">
          <div className="h-3 w-24 bg-border rounded animate-pulse" />
          <div className="mt-3 h-8 w-32 bg-border rounded animate-pulse" />
        </div>
      ))}
    </div>
  );
}

export default function ClientesSection() {
  const { data, loading, error } = useClientes();

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-text">Clientes &amp; Comportamento</h1>
        <p className="mt-1 text-sm text-text-muted leading-relaxed">
          Quem são, quanto valem e como compram os clientes — período de 13/dez/2025 a 11/jan/2026.
        </p>
      </div>

      {loading && <Skeleton />}

      {error && (
        <div className="bg-surface rounded-2xl border border-border shadow-sm p-6 text-danger">
          Não foi possível carregar os dados de clientes: {error}
        </div>
      )}

      {data && !loading && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <KpiCard
              label="Clientes ativos"
              value={`${formatNumber(data.clientesAtivos)} / ${formatNumber(data.totalClientes)}`}
              hint={`${formatPercent(data.clientesAtivos / (data.totalClientes || 1))} da base comprou no período`}
            />
            <KpiCard
              label="Receita média / cliente"
              value={formatBRL(data.receitaMediaCliente)}
              hint={`Receita total ${formatBRL(data.receitaTotal)}`}
            />
            <KpiCard
              label="Ticket médio"
              value={formatBRL(data.ticketMedioGeral)}
              hint={`Frequência média ${formatNumber(Math.round(data.frequenciaMedia))} compras/cliente`}
            />
            <KpiCard
              label="Concentração Top 10"
              value={formatPercent(data.shareTop10)}
              hint="da receita vem dos 10 maiores clientes"
            />
          </div>

          <div className="bg-surface rounded-2xl border border-border shadow-sm p-6">
            <p className="text-sm text-text leading-relaxed">
              <span className="font-semibold">Insight:</span> a base é pequena e{' '}
              <span className="font-semibold">totalmente ativa</span> — todos os{' '}
              {formatNumber(data.totalClientes)} clientes compraram no período. A receita é{' '}
              <span className="font-semibold">pouco concentrada</span>: os 10 maiores respondem por{' '}
              {formatPercent(data.shareTop10)} do total, sinal de uma base saudável e distribuída.
              O{' '}
              <span className="font-semibold">e-commerce domina</span>:{' '}
              {formatNumber(data.clientesPorCanalPreferido.ecommerce)} dos{' '}
              {formatNumber(data.totalClientes)} clientes têm o canal digital como preferido.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ChartCard
              title="Distribuição geográfica"
              subtitle="Receita por estado (UF). Todos os clientes estão no Brasil."
            >
              <GeoChart data={data.porEstado} />
            </ChartCard>

            <ChartCard
              title="Top 10 clientes por receita"
              subtitle={`Juntos representam ${formatPercent(data.shareTop10)} da receita total.`}
            >
              <TopClientsChart data={data.topClientes} />
            </ChartCard>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ChartCard
              title="Comportamento de compra"
              subtitle="Cada ponto é um cliente: frequência (compras) × ticket médio; o tamanho reflete a receita. Em verde, clientes acima da média nas duas dimensões."
            >
              <BehaviorScatter
                data={data.clientes}
                ticketMedio={data.ticketMedioGeral}
                frequenciaMedia={data.frequenciaMedia}
              />
            </ChartCard>

            <ChartCard
              title="Mix de canal"
              subtitle={`Receita por canal de venda. ${formatNumber(data.clientesPorCanalPreferido.ecommerce)} de ${formatNumber(data.totalClientes)} clientes preferem o e-commerce.`}
            >
              <ChannelDonut data={data.porCanal} />
            </ChartCard>
          </div>
        </>
      )}
    </div>
  );
}
