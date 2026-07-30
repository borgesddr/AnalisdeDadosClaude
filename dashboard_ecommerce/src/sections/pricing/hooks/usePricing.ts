import { useEffect, useState } from 'react';
import { supabase } from '../../../lib/supabase';

type Produto = {
  id_produto: string;
  nome_produto: string;
  categoria: string;
  marca: string | null;
  preco_atual: number;
};

type PrecoCompetidor = {
  id_produto: string;
  nome_concorrente: string;
  preco_concorrente: number;
};

export type CategoryPosition = {
  categoria: string;
  gapFrac: number;
  n: number;
  maisCaros: number;
};

export type ParityPoint = {
  id: string;
  nome: string;
  categoria: string;
  preco: number;
  avgComp: number;
};

export type CompetitorPosition = {
  nome: string;
  maisCaros: number;
  maisBaratos: number;
  gapFrac: number;
};

export type RiskProduct = {
  id: string;
  nome: string;
  categoria: string;
  preco: number;
  menorComp: number;
  sobreprecoFrac: number;
};

export type PricingSummary = {
  nProdutos: number;
  gapMedioFrac: number;
  gapMedioReais: number;
  nAcimaMercado: number;
  pctAcimaMercado: number;
  nLideres: number;
  pctLideres: number;
  categoriaAlerta: { categoria: string; gapFrac: number } | null;
  nConcorrentes: number;
};

export type PricingData = {
  summary: PricingSummary;
  byCategory: CategoryPosition[];
  parity: ParityPoint[];
  byCompetitor: CompetitorPosition[];
  risk: RiskProduct[];
};

type State = {
  loading: boolean;
  error: string | null;
  data: PricingData | null;
};

const PAGE = 1000;

async function fetchAll<T>(table: string, columns: string): Promise<T[]> {
  const rows: T[] = [];
  for (let from = 0; ; from += PAGE) {
    const { data, error } = await supabase
      .from(table)
      .select(columns)
      .range(from, from + PAGE - 1);
    if (error) throw error;
    const batch = (data ?? []) as unknown as T[];
    rows.push(...batch);
    if (batch.length < PAGE) break;
  }
  return rows;
}

const mean = (xs: number[]): number =>
  xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : 0;

function build(produtos: Produto[], precos: PrecoCompetidor[]): PricingData {
  const compByProduto = new Map<string, number[]>();
  for (const pc of precos) {
    const price = Number(pc.preco_concorrente);
    if (!Number.isFinite(price) || price <= 0) continue;
    const arr = compByProduto.get(pc.id_produto);
    if (arr) arr.push(price);
    else compByProduto.set(pc.id_produto, [price]);
  }

  const parity: ParityPoint[] = [];
  const risk: RiskProduct[] = [];
  const gapFracs: number[] = [];
  const gapReais: number[] = [];
  let nAcima = 0;
  let nLideres = 0;

  const catAgg = new Map<string, { gaps: number[]; maisCaros: number }>();

  for (const p of produtos) {
    const comps = compByProduto.get(p.id_produto);
    if (!comps || comps.length === 0) continue;
    const preco = Number(p.preco_atual);
    if (!Number.isFinite(preco) || preco <= 0) continue;

    const avgComp = mean(comps);
    const minComp = Math.min(...comps);
    const gapFrac = (preco - avgComp) / avgComp;

    gapFracs.push(gapFrac);
    gapReais.push(preco - avgComp);
    if (preco > avgComp) nAcima += 1;
    if (preco <= minComp) nLideres += 1;

    parity.push({
      id: p.id_produto,
      nome: p.nome_produto,
      categoria: p.categoria,
      preco,
      avgComp,
    });

    if (preco > minComp) {
      risk.push({
        id: p.id_produto,
        nome: p.nome_produto,
        categoria: p.categoria,
        preco,
        menorComp: minComp,
        sobreprecoFrac: (preco - minComp) / minComp,
      });
    }

    const agg = catAgg.get(p.categoria) ?? { gaps: [], maisCaros: 0 };
    agg.gaps.push(gapFrac);
    if (preco > avgComp) agg.maisCaros += 1;
    catAgg.set(p.categoria, agg);
  }

  const byCategory: CategoryPosition[] = [...catAgg.entries()]
    .map(([categoria, a]) => ({
      categoria,
      gapFrac: mean(a.gaps),
      n: a.gaps.length,
      maisCaros: a.maisCaros,
    }))
    .sort((x, y) => y.gapFrac - x.gapFrac);

  // Posição vs cada concorrente (comparação direta produto a produto).
  const precoByProduto = new Map<string, number>();
  for (const p of produtos) precoByProduto.set(p.id_produto, Number(p.preco_atual));

  const compAgg = new Map<
    string,
    { maisCaros: number; maisBaratos: number; gaps: number[] }
  >();
  for (const pc of precos) {
    const nosso = precoByProduto.get(pc.id_produto);
    const comp = Number(pc.preco_concorrente);
    if (nosso == null || !Number.isFinite(nosso) || !Number.isFinite(comp) || comp <= 0)
      continue;
    const agg =
      compAgg.get(pc.nome_concorrente) ?? { maisCaros: 0, maisBaratos: 0, gaps: [] };
    if (nosso > comp) agg.maisCaros += 1;
    else if (nosso < comp) agg.maisBaratos += 1;
    agg.gaps.push((nosso - comp) / comp);
    compAgg.set(pc.nome_concorrente, agg);
  }
  const byCompetitor: CompetitorPosition[] = [...compAgg.entries()]
    .map(([nome, a]) => ({
      nome,
      maisCaros: a.maisCaros,
      maisBaratos: a.maisBaratos,
      gapFrac: mean(a.gaps),
    }))
    .sort((x, y) => y.gapFrac - x.gapFrac);

  risk.sort((a, b) => b.sobreprecoFrac - a.sobreprecoFrac);

  const nProdutos = parity.length;
  const categoriaAlerta = byCategory.length
    ? { categoria: byCategory[0].categoria, gapFrac: byCategory[0].gapFrac }
    : null;

  return {
    summary: {
      nProdutos,
      gapMedioFrac: mean(gapFracs),
      gapMedioReais: mean(gapReais),
      nAcimaMercado: nAcima,
      pctAcimaMercado: nProdutos ? nAcima / nProdutos : 0,
      nLideres,
      pctLideres: nProdutos ? nLideres / nProdutos : 0,
      categoriaAlerta,
      nConcorrentes: compAgg.size,
    },
    byCategory,
    parity,
    byCompetitor,
    risk: risk.slice(0, 10),
  };
}

export function usePricing(): State {
  const [state, setState] = useState<State>({
    loading: true,
    error: null,
    data: null,
  });

  useEffect(() => {
    let active = true;

    (async () => {
      try {
        const [produtos, precos] = await Promise.all([
          fetchAll<Produto>(
            'produtos',
            'id_produto, nome_produto, categoria, marca, preco_atual',
          ),
          fetchAll<PrecoCompetidor>(
            'preco_competidores',
            'id_produto, nome_concorrente, preco_concorrente',
          ),
        ]);

        if (!active) return;

        const data = build(produtos, precos);
        setState({ loading: false, error: null, data });
      } catch (e) {
        if (!active) return;
        setState({
          loading: false,
          error: e instanceof Error ? e.message : 'Erro ao carregar dados de pricing.',
          data: null,
        });
      }
    })();

    return () => {
      active = false;
    };
  }, []);

  return state;
}
