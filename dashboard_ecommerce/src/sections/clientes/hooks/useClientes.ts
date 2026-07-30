import { useEffect, useState } from 'react';
import { supabase } from '../../../lib/supabase';

type ClienteRow = {
  id_cliente: string;
  nome_cliente: string;
  estado: string;
  pais: string;
  data_cadastro: string;
};

type VendaRow = {
  id_cliente: string;
  canal_venda: 'ecommerce' | 'loja_fisica';
  quantidade: number;
  preco_unitario: number;
  data_venda: string;
};

export type ClienteMetric = {
  id: string;
  nome: string;
  estado: string;
  receita: number;
  compras: number;
  ticketMedio: number;
  recenciaDias: number;
  canalPreferido: 'ecommerce' | 'loja_fisica';
};

export type EstadoMetric = {
  estado: string;
  receita: number;
  clientes: number;
};

export type CanalMetric = {
  canal: 'ecommerce' | 'loja_fisica';
  receita: number;
  transacoes: number;
};

export type ClientesData = {
  totalClientes: number;
  clientesAtivos: number;
  receitaTotal: number;
  receitaMediaCliente: number;
  ticketMedioGeral: number;
  frequenciaMedia: number;
  shareTop10: number;
  clientes: ClienteMetric[];
  topClientes: ClienteMetric[];
  porEstado: EstadoMetric[];
  porCanal: CanalMetric[];
  clientesPorCanalPreferido: Record<'ecommerce' | 'loja_fisica', number>;
};

const PAGE = 1000;

async function fetchAll<T>(
  table: string,
  columns: string,
): Promise<T[]> {
  const rows: T[] = [];
  for (let from = 0; ; from += PAGE) {
    const { data, error } = await supabase
      .from(table)
      .select(columns)
      .range(from, from + PAGE - 1);
    if (error) throw error;
    if (!data || data.length === 0) break;
    rows.push(...(data as T[]));
    if (data.length < PAGE) break;
  }
  return rows;
}

function aggregate(clientes: ClienteRow[], vendas: VendaRow[]): ClientesData {
  const maxData = vendas.reduce(
    (acc, v) => (v.data_venda > acc ? v.data_venda : acc),
    vendas[0]?.data_venda ?? '',
  );
  const refDia = maxData ? new Date(maxData.slice(0, 10)).getTime() : 0;

  const nomePorId = new Map<string, ClienteRow>();
  clientes.forEach((c) => nomePorId.set(c.id_cliente, c));

  type Acc = {
    receita: number;
    compras: number;
    ultima: string;
    canal: Record<'ecommerce' | 'loja_fisica', number>;
  };
  const porCliente = new Map<string, Acc>();

  const canalTotais: Record<'ecommerce' | 'loja_fisica', CanalMetric> = {
    ecommerce: { canal: 'ecommerce', receita: 0, transacoes: 0 },
    loja_fisica: { canal: 'loja_fisica', receita: 0, transacoes: 0 },
  };

  for (const v of vendas) {
    const valor = v.quantidade * v.preco_unitario;
    let acc = porCliente.get(v.id_cliente);
    if (!acc) {
      acc = { receita: 0, compras: 0, ultima: '', canal: { ecommerce: 0, loja_fisica: 0 } };
      porCliente.set(v.id_cliente, acc);
    }
    acc.receita += valor;
    acc.compras += 1;
    acc.canal[v.canal_venda] += valor;
    if (v.data_venda > acc.ultima) acc.ultima = v.data_venda;

    canalTotais[v.canal_venda].receita += valor;
    canalTotais[v.canal_venda].transacoes += 1;
  }

  const clientesMetric: ClienteMetric[] = [];
  const porCanalPreferido: Record<'ecommerce' | 'loja_fisica', number> = {
    ecommerce: 0,
    loja_fisica: 0,
  };

  porCliente.forEach((acc, id) => {
    const info = nomePorId.get(id);
    const canalPreferido =
      acc.canal.ecommerce >= acc.canal.loja_fisica ? 'ecommerce' : 'loja_fisica';
    porCanalPreferido[canalPreferido] += 1;
    const recenciaDias =
      acc.ultima && refDia
        ? Math.round((refDia - new Date(acc.ultima.slice(0, 10)).getTime()) / 86400000)
        : 0;
    clientesMetric.push({
      id,
      nome: info?.nome_cliente ?? id,
      estado: info?.estado ?? '—',
      receita: acc.receita,
      compras: acc.compras,
      ticketMedio: acc.compras ? acc.receita / acc.compras : 0,
      recenciaDias,
      canalPreferido,
    });
  });

  clientesMetric.sort((a, b) => b.receita - a.receita);

  const receitaTotal = clientesMetric.reduce((s, c) => s + c.receita, 0);
  const receitaTop10 = clientesMetric.slice(0, 10).reduce((s, c) => s + c.receita, 0);
  const ticketMedioGeral =
    clientesMetric.reduce((s, c) => s + c.ticketMedio, 0) / (clientesMetric.length || 1);
  const frequenciaMedia =
    clientesMetric.reduce((s, c) => s + c.compras, 0) / (clientesMetric.length || 1);

  const estadoMap = new Map<string, EstadoMetric>();
  clientesMetric.forEach((c) => {
    let e = estadoMap.get(c.estado);
    if (!e) {
      e = { estado: c.estado, receita: 0, clientes: 0 };
      estadoMap.set(c.estado, e);
    }
    e.receita += c.receita;
    e.clientes += 1;
  });
  const porEstado = Array.from(estadoMap.values()).sort((a, b) => b.receita - a.receita);

  return {
    totalClientes: clientes.length,
    clientesAtivos: porCliente.size,
    receitaTotal,
    receitaMediaCliente: clientes.length ? receitaTotal / clientes.length : 0,
    ticketMedioGeral,
    frequenciaMedia,
    shareTop10: receitaTotal ? receitaTop10 / receitaTotal : 0,
    clientes: clientesMetric,
    topClientes: clientesMetric.slice(0, 10),
    porEstado,
    porCanal: [canalTotais.ecommerce, canalTotais.loja_fisica],
    clientesPorCanalPreferido: porCanalPreferido,
  };
}

export function useClientes() {
  const [data, setData] = useState<ClientesData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancel = false;
    (async () => {
      try {
        setLoading(true);
        setError(null);
        const [clientes, vendas] = await Promise.all([
          fetchAll<ClienteRow>('clientes', 'id_cliente,nome_cliente,estado,pais,data_cadastro'),
          fetchAll<VendaRow>('vendas', 'id_cliente,canal_venda,quantidade,preco_unitario,data_venda'),
        ]);
        if (cancel) return;
        setData(aggregate(clientes, vendas));
      } catch (e) {
        if (!cancel) setError(e instanceof Error ? e.message : 'Erro ao carregar dados');
      } finally {
        if (!cancel) setLoading(false);
      }
    })();
    return () => {
      cancel = true;
    };
  }, []);

  return { data, loading, error };
}
