import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { setMockTables, resetMock, setMockError } from '../helpers/supabaseMock';

vi.mock('../../src/lib/supabase', async () => {
  const mod = await import('../helpers/supabaseMock');
  return { supabase: mod.supabaseMock };
});

import VendasSection from '../../src/sections/vendas';

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
    data_venda: '2025-12-14T09:00:00Z',
    canal_venda: 'loja_fisica',
    quantidade: 3,
    preco_unitario: 100,
    id_cliente: 'C2',
    produtos: { categoria: 'Moda', nome_produto: 'Camisa' },
  },
];

beforeEach(() => resetMock());

describe('VendasSection — renderizacao', () => {
  it('renderiza o cabecalho e os KPIs apos carregar', async () => {
    setMockTables({ vendas: VENDAS });
    render(<VendasSection />);

    expect(screen.getByText('Vendas & Receita')).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getByText('Receita total')).toBeInTheDocument(),
    );
    // receita total = 200 + 300 = 500
    expect(screen.getByText('R$ 500,00')).toBeInTheDocument();
    expect(screen.getAllByText('Ticket médio').length).toBeGreaterThan(0);
  });

  it('caso de borda: sem dados renderiza sem quebrar', async () => {
    setMockTables({ vendas: [] });
    render(<VendasSection />);

    await waitFor(() =>
      expect(screen.getByText('Receita total')).toBeInTheDocument(),
    );
    // categoria lider sem dados usa fallback
    expect(screen.getByText('—')).toBeInTheDocument();
  });

  it('mostra mensagem de erro quando o fetch falha', async () => {
    setMockError('sem rede');
    render(<VendasSection />);

    await waitFor(() =>
      expect(
        screen.getByText(/Não foi possível carregar os dados de vendas/i),
      ).toBeInTheDocument(),
    );
  });
});
