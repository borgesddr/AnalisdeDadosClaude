import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { setMockTables, resetMock, setMockError } from '../helpers/supabaseMock';

vi.mock('../../src/lib/supabase', async () => {
  const mod = await import('../helpers/supabaseMock');
  return { supabase: mod.supabaseMock };
});

import { useClientes } from '../../src/sections/clientes/hooks/useClientes';

const CLIENTES = [
  { id_cliente: 'C1', nome_cliente: 'Ana', estado: 'SP', pais: 'Brasil', data_cadastro: '2025-01-01T00:00:00Z' },
  { id_cliente: 'C2', nome_cliente: 'Bob', estado: 'RJ', pais: 'Brasil', data_cadastro: '2025-02-01T00:00:00Z' },
  { id_cliente: 'C3', nome_cliente: 'Carol', estado: 'SP', pais: 'Brasil', data_cadastro: '2025-03-01T00:00:00Z' },
];
const VENDAS = [
  { id_cliente: 'C1', canal_venda: 'ecommerce', quantidade: 2, preco_unitario: 100, data_venda: '2026-01-10T10:00:00Z' },
  { id_cliente: 'C1', canal_venda: 'ecommerce', quantidade: 1, preco_unitario: 100, data_venda: '2026-01-11T10:00:00Z' },
  { id_cliente: 'C2', canal_venda: 'loja_fisica', quantidade: 1, preco_unitario: 50, data_venda: '2026-01-05T10:00:00Z' },
];

beforeEach(() => resetMock());

describe('useClientes — metricas de clientes', () => {
  it('calcula ativos, receita e concentração corretamente', async () => {
    setMockTables({ clientes: CLIENTES, vendas: VENDAS });
    const { result } = renderHook(() => useClientes());
    await waitFor(() => expect(result.current.loading).toBe(false));

    const d = result.current.data!;
    expect(d.totalClientes).toBe(3);
    expect(d.clientesAtivos).toBe(2); // C3 nao comprou
    expect(d.receitaTotal).toBe(350); // 300 + 50
    expect(d.receitaMediaCliente).toBeCloseTo(350 / 3, 5);
    // ticketMedio por cliente: C1=150, C2=50 -> media 100
    expect(d.ticketMedioGeral).toBeCloseTo(100, 5);
    expect(d.frequenciaMedia).toBeCloseTo(1.5, 5); // (2 + 1) / 2
    expect(d.shareTop10).toBe(1); // todos entram no top 10
  });

  it('ordena clientes por receita e monta ranking geografico', async () => {
    setMockTables({ clientes: CLIENTES, vendas: VENDAS });
    const { result } = renderHook(() => useClientes());
    await waitFor(() => expect(result.current.loading).toBe(false));

    const d = result.current.data!;
    expect(d.topClientes[0].nome).toBe('Ana'); // C1 maior receita
    expect(d.porEstado[0].estado).toBe('SP'); // SP (300) > RJ (50)
    expect(d.porEstado[0].receita).toBe(300);
  });

  it('determina canal preferido e recência por cliente', async () => {
    setMockTables({ clientes: CLIENTES, vendas: VENDAS });
    const { result } = renderHook(() => useClientes());
    await waitFor(() => expect(result.current.loading).toBe(false));

    const d = result.current.data!;
    const ana = d.clientes.find((c) => c.id === 'C1')!;
    const bob = d.clientes.find((c) => c.id === 'C2')!;
    expect(ana.canalPreferido).toBe('ecommerce');
    expect(ana.recenciaDias).toBe(0); // comprou no dia de referencia (11/01)
    expect(bob.canalPreferido).toBe('loja_fisica');
    expect(bob.recenciaDias).toBe(6); // 11/01 - 05/01
    expect(d.clientesPorCanalPreferido).toEqual({ ecommerce: 1, loja_fisica: 1 });
  });

  it('caso de borda: sem dados não quebra e zera métricas', async () => {
    setMockTables({ clientes: [], vendas: [] });
    const { result } = renderHook(() => useClientes());
    await waitFor(() => expect(result.current.loading).toBe(false));

    const d = result.current.data!;
    expect(d.totalClientes).toBe(0);
    expect(d.clientesAtivos).toBe(0);
    expect(d.receitaTotal).toBe(0);
    expect(d.receitaMediaCliente).toBe(0);
    expect(d.ticketMedioGeral).toBe(0);
    expect(d.shareTop10).toBe(0);
    expect(d.porEstado).toEqual([]);
  });

  it('propaga erro de fetch', async () => {
    setMockError('falha clientes');
    const { result } = renderHook(() => useClientes());
    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBe('falha clientes');
    expect(result.current.data).toBeNull();
  });
});
