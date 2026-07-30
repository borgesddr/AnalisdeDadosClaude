const brl = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
});
const num = new Intl.NumberFormat('pt-BR');
const pct = new Intl.NumberFormat('pt-BR', {
  style: 'percent',
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

export const formatBRL = (v: number): string => brl.format(v ?? 0);

export const formatNumber = (v: number): string => num.format(v ?? 0);

/** Recebe uma fração (0.15 => "15,0%"). */
export const formatPercent = (v: number): string => pct.format(v ?? 0);

export const formatDate = (d: string | Date): string =>
  new Date(d).toLocaleDateString('pt-BR');
