import { useEffect, useMemo, useState } from 'react';
import { supabase } from '../../../lib/supabase';

interface VendaRow {
  data_venda: string;
  canal_venda: string;
  quantidade: number;
  preco_unitario: number;
  id_cliente: string;
  produtos: { categoria: string | null; nome_produto: string | null } | null;
}

export interface ChannelStat {
  canal: string;
  receita: number;
  vendas: number;
  ticketMedio: number;
  pctReceita: number;
}

export interface RankItem {
  nome: string;
  categoria: string;
  receita: number;
  itens: number;
}

export interface DayPoint {
  dia: string;
  receita: number;
  ecommerce: number;
  loja_fisica: number;
}

export interface VendasData {
  receitaTotal: number;
  ticketMedio: number;
  totalVendas: number;
  itensVendidos: number;
  clientesAtivos: number;
  pctEcommerce: number;
  canais: ChannelStat[];
  serieDiaria: DayPoint[];
  topCategorias: RankItem[];
  topProdutos: RankItem[];
}

const PAGE = 1000;

async function fetchAllVendas(): Promise<VendaRow[]> {
  const rows: VendaRow[] = [];
  for (let from = 0; ; from += PAGE) {
    const { data, error } = await supabase
      .from('vendas')
      .select(
        'data_venda, canal_venda, quantidade, preco_unitario, id_cliente, produtos(categoria, nome_produto)',
      )
      .order('data_venda', { ascending: true })
      .range(from, from + PAGE - 1);
    if (error) throw error;
    const batch = (data ?? []) as unknown as VendaRow[];
    rows.push(...batch);
    if (batch.length < PAGE) break;
  }
  return rows;
}

function aggregate(rows: VendaRow[]): VendasData {
  let receitaTotal = 0;
  let itensVendidos = 0;
  const canalMap = new Map<string, { receita: number; vendas: number }>();
  const catMap = new Map<string, RankItem>();
  const prodMap = new Map<string, RankItem>();
  const diaMap = new Map<string, DayPoint>();
  const clientes = new Set<string>();

  for (const r of rows) {
    const valor = r.quantidade * r.preco_unitario;
    receitaTotal += valor;
    itensVendidos += r.quantidade;
    clientes.add(r.id_cliente);

    const canal = canalMap.get(r.canal_venda) ?? { receita: 0, vendas: 0 };
    canal.receita += valor;
    canal.vendas += 1;
    canalMap.set(r.canal_venda, canal);

    const categoria = r.produtos?.categoria ?? 'Sem categoria';
    const cat = catMap.get(categoria) ?? { nome: categoria, categoria, receita: 0, itens: 0 };
    cat.receita += valor;
    cat.itens += r.quantidade;
    catMap.set(categoria, cat);

    const nome = r.produtos?.nome_produto ?? 'Sem nome';
    const prod = prodMap.get(nome) ?? { nome, categoria, receita: 0, itens: 0 };
    prod.receita += valor;
    prod.itens += r.quantidade;
    prodMap.set(nome, prod);

    const dia = r.data_venda.slice(0, 10);
    const dp = diaMap.get(dia) ?? { dia, receita: 0, ecommerce: 0, loja_fisica: 0 };
    dp.receita += valor;
    if (r.canal_venda === 'ecommerce') dp.ecommerce += valor;
    else if (r.canal_venda === 'loja_fisica') dp.loja_fisica += valor;
    diaMap.set(dia, dp);
  }

  const totalVendas = rows.length;
  const canais: ChannelStat[] = [...canalMap.entries()]
    .map(([canal, v]) => ({
      canal,
      receita: v.receita,
      vendas: v.vendas,
      ticketMedio: v.vendas ? v.receita / v.vendas : 0,
      pctReceita: receitaTotal ? v.receita / receitaTotal : 0,
    }))
    .sort((a, b) => b.receita - a.receita);

  const pctEcommerce =
    canais.find((c) => c.canal === 'ecommerce')?.pctReceita ?? 0;

  return {
    receitaTotal,
    ticketMedio: totalVendas ? receitaTotal / totalVendas : 0,
    totalVendas,
    itensVendidos,
    clientesAtivos: clientes.size,
    pctEcommerce,
    canais,
    serieDiaria: [...diaMap.values()].sort((a, b) => a.dia.localeCompare(b.dia)),
    topCategorias: [...catMap.values()].sort((a, b) => b.receita - a.receita),
    topProdutos: [...prodMap.values()]
      .sort((a, b) => b.receita - a.receita)
      .slice(0, 5),
  };
}

export function useVendas() {
  const [rows, setRows] = useState<VendaRow[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let ativo = true;
    (async () => {
      try {
        setLoading(true);
        setError(null);
        const vendas = await fetchAllVendas();
        if (!ativo) return;
        setRows(vendas);
      } catch (e) {
        if (!ativo) return;
        setError(e instanceof Error ? e.message : 'Erro ao carregar vendas.');
      } finally {
        if (ativo) setLoading(false);
      }
    })();
    return () => {
      ativo = false;
    };
  }, []);

  const data = useMemo<VendasData | null>(
    () => (rows ? aggregate(rows) : null),
    [rows],
  );

  return { data, loading, error };
}
