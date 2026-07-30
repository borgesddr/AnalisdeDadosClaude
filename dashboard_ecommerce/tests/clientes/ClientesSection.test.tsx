import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { setMockTables, resetMock, setMockError } from '../helpers/supabaseMock';

vi.mock('../../src/lib/supabase', async () => {
  const mod = await import('../helpers/supabaseMock');
  return { supabase: mod.supabaseMock };
});

import ClientesSection from '../../src/sections/clientes';

const CLIENTES = [
  { id_cliente: 'C1', nome_cliente: 'Ana', estado: 'SP', pais: 'Brasil', data_cadastro: '2025-01-01T00:00:00Z' },
  { id_cliente: 'C2', nome_cliente: 'Bob', estado: 'RJ', pais: 'Brasil', data_cadastro: '2025-02-01T00:00:00Z' },
];
const VENDAS = [
  { id_cliente: 'C1', canal_venda: 'ecommerce', quantidade: 2, preco_unitario: 100, data_venda: '2026-01-10T10:00:00Z' },
  { id_cliente: 'C2', canal_venda: 'loja_fisica', quantidade: 1, preco_unitario: 50, data_venda: '2026-01-05T10:00:00Z' },
];

beforeEach(() => resetMock());

describe('ClientesSection — renderizacao', () => {
  it('renderiza cabecalho e KPIs apos carregar', async () => {
    setMockTables({ clientes: CLIENTES, vendas: VENDAS });
    render(<ClientesSection />);

    expect(screen.getByText('Clientes & Comportamento')).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getByText('Clientes ativos')).toBeInTheDocument(),
    );
    expect(screen.getByText('Concentração Top 10')).toBeInTheDocument();
  });

  it('caso de borda: sem dados renderiza sem quebrar', async () => {
    setMockTables({ clientes: [], vendas: [] });
    render(<ClientesSection />);

    await waitFor(() =>
      expect(screen.getByText('Clientes ativos')).toBeInTheDocument(),
    );
    // "0 / 0" clientes ativos
    expect(screen.getByText('0 / 0')).toBeInTheDocument();
  });

  it('mostra erro quando o fetch falha', async () => {
    setMockError('sem rede');
    render(<ClientesSection />);

    await waitFor(() =>
      expect(
        screen.getByText(/Não foi possível carregar os dados de clientes/i),
      ).toBeInTheDocument(),
    );
  });
});
