// Mock reutilizavel do cliente @supabase/supabase-js usado em src/lib/supabase.ts.
//
// Reproduz o "query builder" encadeavel do supabase-js: cada metodo de filtro/
// ordenacao retorna o proprio builder, e o builder e "thenable" (tem .then), de
// modo que `await supabase.from('x').select(...)` e tambem
// `await supabase.from('x').select(...).order(...).range(a, b)` resolvem para
// `{ data, error }`.
//
// Como o vi.mock e "hoisted", o padrao recomendado nos testes e:
//
//   vi.mock('../../src/lib/supabase', async () => {
//     const mod = await import('../helpers/supabaseMock');
//     return { supabase: mod.supabaseMock };
//   });
//
// e configurar os dados por teste com setMockTables({ vendas: rows }) num
// beforeEach (ou setMockError('...') para exercitar o estado de erro).

type Row = Record<string, unknown>;
type TableData = Record<string, Row[]>;

let currentTables: TableData = {};
let currentError: unknown = null;

export function setMockTables(tables: TableData): void {
  currentTables = tables;
  currentError = null;
}

export function setMockError(message = 'Falha de rede simulada'): void {
  currentError = new Error(message);
}

export function resetMock(): void {
  currentTables = {};
  currentError = null;
}

interface BuilderState {
  rangeFrom?: number;
  rangeTo?: number;
  limit?: number;
  filters: Array<(r: Row) => boolean>;
}

function makeBuilder(rows: Row[]) {
  const state: BuilderState = { filters: [] };

  const resolve = () => {
    if (currentError) return { data: null, error: currentError };
    let out = rows.filter((r) => state.filters.every((f) => f(r)));
    if (state.rangeFrom !== undefined && state.rangeTo !== undefined) {
      out = out.slice(state.rangeFrom, state.rangeTo + 1);
    }
    if (state.limit !== undefined) out = out.slice(0, state.limit);
    return { data: out, error: null };
  };

  const builder: Record<string, unknown> = {
    select: () => builder,
    order: () => builder,
    eq: (col: string, val: unknown) => {
      state.filters.push((r) => r[col] === val);
      return builder;
    },
    neq: (col: string, val: unknown) => {
      state.filters.push((r) => r[col] !== val);
      return builder;
    },
    gte: (col: string, val: number | string) => {
      state.filters.push((r) => (r[col] as number) >= (val as number));
      return builder;
    },
    lte: (col: string, val: number | string) => {
      state.filters.push((r) => (r[col] as number) <= (val as number));
      return builder;
    },
    in: (col: string, vals: unknown[]) => {
      state.filters.push((r) => vals.includes(r[col]));
      return builder;
    },
    range: (from: number, to: number) => {
      state.rangeFrom = from;
      state.rangeTo = to;
      return builder;
    },
    limit: (n: number) => {
      state.limit = n;
      return builder;
    },
    single: () =>
      Promise.resolve({
        data: (resolve().data as Row[] | null)?.[0] ?? null,
        error: currentError,
      }),
    maybeSingle: () =>
      Promise.resolve({
        data: (resolve().data as Row[] | null)?.[0] ?? null,
        error: currentError,
      }),
    // torna o builder "thenable" para poder ser aguardado com await
    then: (onFulfilled: (v: unknown) => unknown) =>
      Promise.resolve(resolve()).then(onFulfilled),
  };

  return builder;
}

// Singleton estavel: a referencia nunca muda (importante para o vi.mock), mas
// os dados que ele serve sao controlados via setMockTables/setMockError.
export const supabaseMock = {
  from: (table: string) => makeBuilder(currentTables[table] ?? []),
};
