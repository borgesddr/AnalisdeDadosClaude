import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { setMockTables, resetMock, setMockError } from '../helpers/supabaseMock';

vi.mock('../../src/lib/supabase', async () => {
  const mod = await import('../helpers/supabaseMock');
  return { supabase: mod.supabaseMock };
});

import { useVendas } from '../../src/sections/vendas/hooks/useVendas';

// 3 vendas simples com valores calculaveis a mao.
const VENDAS = [
  {
    data_venda: '2025-12-13T10:00:00Z',
    canal_venda: 'ecommerce',
    quantidade: 2,
    preco_unitario: 100,
    id_cliente: 'C1',
    produtos: { categoria: 'Casa', nome_produto: 'Mesa' },
  },
  {
    data_venda: '2025-12-13T12:00:00Z',
    canal_venda: 'ecommerce',
    quantidade: 1,
    preco_unitario: 50,
    id_cliente: 'C2',
    produtos: { categoria: 'Casa', nome_produto: 'Cadeira' },
  },
  {
    data_venda: '2025-12-14T09:00:00Z',
    canal_venda: 'loja_fisica',
    quantidade: 3,
    preco_unitario: 100,
    id_cliente: 'C1',
    produtos: { categoria: 'Moda', nome_produto: 'Camisa' },
  },
];

beforeEach(() => resetMock());

describe('useVendas — agregacao de KPIs', () => {
  it('calcula os KPIs corretamente a partir dos dados', async () => {
    setMockTables({ vendas: VENDAS });
    const { result } = renderHook(() => useVendas());

    await waitFor(() => expect(result.current.loading).toBe(false));

    const d = result.current.data!;
    expect(d).not.toBeNull();
    // 200 + 50 + 300
    expect(d.receitaTotal).toBe(550);
    expect(d.totalVendas).toBe(3);
    expect(d.ticketMedio).toBeCloseTo(550 / 3, 5);
    expect(d.itensVendidos).toBe(6);
    expect(d.clientesAtivos).toBe(2); // C1, C2
    // ecommerce = 250 de 550
    expect(d.pctEcommerce).toBeCloseTo(250 / 550, 5);
  });

  it('ordena categorias e produtos por receita (desc)', async () => {
    setMockTables({ vendas: VENDAS });
    const { result } = renderHook(() => useVendas());
    await waitFor(() => expect(result.current.loading).toBe(false));

    const d = result.current.data!;
    // Moda (300) > Casa (250)
    expect(d.topCategorias.map((c) => c.categoria)).toEqual(['Moda', 'Casa']);
    // Camisa (300) > Mesa (200) > Cadeira (50)
    expect(d.topProdutos.map((p) => p.nome)).toEqual([
      'Camisa',
      'Mesa',
      'Cadeira',
    ]);
    // canais ordenados por receita: loja_fisica (300) > ecommerce (250)
    expect(d.canais[0].canal).toBe('loja_fisica');
    expect(d.canais.find((c) => c.canal === 'ecommerce')!.ticketMedio).toBe(125);
  });

  it('agrupa a serie diaria por dia', async () => {
    setMockTables({ vendas: VENDAS });
    const { result } = renderHook(() => useVendas());
    await waitFor(() => expect(result.current.loading).toBe(false));

    const d = result.current.data!;
    expect(d.serieDiaria).toHaveLength(2); // 13 e 14 de dez
    expect(d.serieDiaria[0].dia).toBe('2025-12-13');
    expect(d.serieDiaria[0].ecommerce).toBe(250);
    expect(d.serieDiaria[1].loja_fisica).toBe(300);
  });

  it('caso de borda: lista vazia nao quebra e zera os KPIs', async () => {
    setMockTables({ vendas: [] });
    const { result } = renderHook(() => useVendas());
    await waitFor(() => expect(result.current.loading).toBe(false));

    const d = result.current.data!;
    expect(d.receitaTotal).toBe(0);
    expect(d.totalVendas).toBe(0);
    expect(d.ticketMedio).toBe(0);
    expect(d.clientesAtivos).toBe(0);
    expect(d.pctEcommerce).toBe(0);
    expect(d.topCategorias).toEqual([]);
    expect(d.topProdutos).toEqual([]);
  });

  it('propaga erro de rede para o estado de erro', async () => {
    setMockError('boom');
    const { result } = renderHook(() => useVendas());
    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBe('boom');
    expect(result.current.data).toBeNull();
  });
});
