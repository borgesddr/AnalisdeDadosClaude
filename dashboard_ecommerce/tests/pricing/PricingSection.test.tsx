import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { setMockTables, resetMock, setMockError } from '../helpers/supabaseMock';

vi.mock('../../src/lib/supabase', async () => {
  const mod = await import('../helpers/supabaseMock');
  return { supabase: mod.supabaseMock };
});

import PricingSection from '../../src/sections/pricing';

const PRODUTOS = [
  { id_produto: 'P1', nome_produto: 'Mesa', categoria: 'Casa', marca: 'X', preco_atual: 120 },
  { id_produto: 'P2', nome_produto: 'Camisa', categoria: 'Moda', marca: 'Y', preco_atual: 80 },
];
const PRECOS = [
  { id_produto: 'P1', nome_concorrente: 'CompA', preco_concorrente: 100 },
  { id_produto: 'P2', nome_concorrente: 'CompA', preco_concorrente: 90 },
];

beforeEach(() => resetMock());

describe('PricingSection — renderizacao', () => {
  it('renderiza cabecalho e KPIs apos carregar', async () => {
    setMockTables({ produtos: PRODUTOS, preco_competidores: PRECOS });
    render(<PricingSection />);

    expect(screen.getByText('Pricing & Margem')).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getByText('Gap médio vs mercado')).toBeInTheDocument(),
    );
    expect(screen.getByText('Líderes de preço')).toBeInTheDocument();
  });

  it('caso de borda: sem dados renderiza com fallback de categoria', async () => {
    setMockTables({ produtos: [], preco_competidores: [] });
    render(<PricingSection />);

    await waitFor(() =>
      expect(screen.getByText('Categoria em alerta')).toBeInTheDocument(),
    );
    expect(screen.getByText('—')).toBeInTheDocument();
  });

  it('mostra erro quando o fetch falha', async () => {
    setMockError('sem rede');
    render(<PricingSection />);

    await waitFor(() =>
      expect(
        screen.getByText(/Não foi possível carregar os dados de pricing/i),
      ).toBeInTheDocument(),
    );
  });
});
