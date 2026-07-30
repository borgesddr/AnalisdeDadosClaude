import { Suspense, lazy } from 'react';
import { NavLink, Navigate, Route, Routes } from 'react-router-dom';

const VendasSection = lazy(() => import('./sections/vendas'));
const PricingSection = lazy(() => import('./sections/pricing'));
const ClientesSection = lazy(() => import('./sections/clientes'));

const NAV = [
  { to: '/vendas', label: 'Vendas & Receita' },
  { to: '/pricing', label: 'Pricing & Margem' },
  { to: '/clientes', label: 'Clientes & Comportamento' },
];

function App() {
  return (
    <div className="min-h-full flex flex-col">
      <header className="bg-brand-navy text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex items-center gap-8">
          <span className="text-lg font-bold tracking-tight">
            Dashboard E-commerce
            <span className="text-brand-cyan-400"> · Keyrus</span>
          </span>
          <nav className="flex gap-1">
            {NAV.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `px-3 py-2 rounded-full text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-brand-cyan text-white'
                      : 'text-white/80 hover:text-white hover:bg-white/10'
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <main className="flex-1">
        <Suspense
          fallback={
            <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 text-text-muted">
              Carregando…
            </div>
          }
        >
          <Routes>
            <Route path="/" element={<Navigate to="/vendas" replace />} />
            <Route path="/vendas" element={<VendasSection />} />
            <Route path="/pricing" element={<PricingSection />} />
            <Route path="/clientes" element={<ClientesSection />} />
            <Route
              path="*"
              element={
                <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
                  Página não encontrada.
                </div>
              }
            />
          </Routes>
        </Suspense>
      </main>
    </div>
  );
}

export default App;
