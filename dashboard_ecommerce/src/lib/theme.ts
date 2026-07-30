// Tokens de cor em JS para uso nos gráficos Recharts.
// Espelham tailwind.config.js / DESIGN_SYSTEM.md.

export const COLORS = {
  navy: '#0B2265',
  cyan: '#29ABE2',
  cyan400: '#38BDF8',
  orange: '#F5A623',
  success: '#16A34A',
  warning: '#F5A623',
  danger: '#DC2626',
  neutral: '#94A3B8',
  border: '#E4E7EC',
  textMuted: '#667085',
} as const;

// Ordem e mapeamento fixos das 11 categorias de produto.
export const CATEGORY_COLORS: Record<string, string> = {
  Casa: '#0B2265',
  Acessórios: '#29ABE2',
  Moda: '#38BDF8',
  Informática: '#16A34A',
  Cozinha: '#F5A623',
  Esporte: '#DC2626',
  Games: '#7C3AED',
  Áudio: '#EC4899',
  Tênis: '#0EA5A4',
  Eletrônicos: '#F97316',
  Beleza: '#64748B',
};

export const CHANNEL_COLORS: Record<string, string> = {
  ecommerce: '#29ABE2',
  loja_fisica: '#0B2265',
};

// Paleta ordenada para séries genéricas sem categoria fixa.
export const SERIES_PALETTE = Object.values(CATEGORY_COLORS);
