import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { setMockTables, resetMock, setMockError } from '../helpers/supabaseMock';

vi.mock('../../src/lib/supabase', async () => {
  const mod = await import('../helpers/supabaseMock');
  return { supabase: mod.supabaseMock };
});

import { usePricing } from '../../src/sections/pricing/hooks/usePricing';

const PRODUTOS = [
  { id_produto: 'P1', nome_produto: 'Mesa', categoria: 'Casa', marca: 'X', preco_atual: 120 },
  { id_produto: 'P2', nome_produto: 'Camisa', categoria: 'Moda', marca: 'Y', preco_atual: 80 },
];
const PRECOS = [
  { id_produto: 'P1', nome_concorrente: 'CompA', preco_concorrente: 100 },
  { id_produto: 'P1', nome_concorrente: 'CompB', preco_concorrente: 100 },
  { id_produto: 'P2', nome_concorrente: 'CompA', preco_concorrente: 90 },
  { id_produto: 'P2', nome_concorrente: 'CompB', preco_concorrente: 110 },
];

beforeEach(() => resetMock());

describe('usePricing — posicionamento competitivo', () => {
  it('calcula gap, líderes e categoria em alerta', async () => {
    setMockTables({ produtos: PRODUTOS, preco_competidores: PRECOS });
    const { result } = renderHook(() => usePricing());
    await waitFor(() => expect(result.current.loading).toBe(false));

    const { summary } = result.current.data!;
    expect(summary.nProdutos).toBe(2);
    // P1: (120-100)/100=+0.2 ; P2: (80-100)/100=-0.2 -> media 0
    expect(summary.gapMedioFrac).toBeCloseTo(0, 5);
    expect(summary.gapMedioReais).toBeCloseTo(0, 5);
    expect(summary.nAcimaMercado).toBe(1); // P1
    expect(summary.pctAcimaMercado).toBeCloseTo(0.5, 5);
    expect(summary.nLideres).toBe(1); // P2 <= minComp
    expect(summary.nConcorrentes).toBe(2);
    // Casa (+0.2) e a categoria mais cara
    expect(summary.categoriaAlerta?.categoria).toBe('Casa');
    expect(summary.categoriaAlerta?.gapFrac).toBeCloseTo(0.2, 5);
  });

  it('classifica produtos em risco (acima do menor concorrente)', async () => {
    setMockTables({ produtos: PRODUTOS, preco_competidores: PRECOS });
    const { result } = renderHook(() => usePricing());
    await waitFor(() => expect(result.current.loading).toBe(false));

    const { risk } = result.current.data!;
    // Só P1 esta acima do menor concorrente
    expect(risk).toHaveLength(1);
    expect(risk[0].id).toBe('P1');
    expect(risk[0].sobreprecoFrac).toBeCloseTo(0.2, 5);
  });

  it('ordena concorrentes por gap (mais caros para nós primeiro)', async () => {
    setMockTables({ produtos: PRODUTOS, preco_competidores: PRECOS });
    const { result } = renderHook(() => usePricing());
    await waitFor(() => expect(result.current.loading).toBe(false));

    const nomes = result.current.data!.byCompetitor.map((c) => c.nome);
    expect(nomes).toEqual(['CompA', 'CompB']);
  });

  it('ignora produtos sem concorrentes e preços inválidos', async () => {
    setMockTables({
      produtos: [
        ...PRODUTOS,
        { id_produto: 'P3', nome_produto: 'Sem comp', categoria: 'Casa', marca: null, preco_atual: 999 },
        { id_produto: 'P4', nome_produto: 'Preco zero', categoria: 'Casa', marca: null, preco_atual: 0 },
      ],
      preco_competidores: [
        ...PRECOS,
        { id_produto: 'P4', nome_concorrente: 'CompA', preco_concorrente: 50 },
      ],
    });
    const { result } = renderHook(() => usePricing());
    await waitFor(() => expect(result.current.loading).toBe(false));

    // P3 (sem comp) e P4 (preco 0) nao entram
    expect(result.current.data!.summary.nProdutos).toBe(2);
  });

  it('caso de borda: sem dados não quebra', async () => {
    setMockTables({ produtos: [], preco_competidores: [] });
    const { result } = renderHook(() => usePricing());
    await waitFor(() => expect(result.current.loading).toBe(false));

    const { summary, byCategory, parity, risk } = result.current.data!;
    expect(summary.nProdutos).toBe(0);
    expect(summary.gapMedioFrac).toBe(0);
    expect(summary.categoriaAlerta).toBeNull();
    expect(byCategory).toEqual([]);
    expect(parity).toEqual([]);
    expect(risk).toEqual([]);
  });

  it('propaga erro de fetch', async () => {
    setMockError('falha pricing');
    const { result } = renderHook(() => usePricing());
    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBe('falha pricing');
    expect(result.current.data).toBeNull();
  });
});
