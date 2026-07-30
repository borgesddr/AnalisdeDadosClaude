import '@testing-library/jest-dom';

// jsdom nao implementa ResizeObserver, exigido pelo ResponsiveContainer do Recharts.
class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver =
  globalThis.ResizeObserver ?? (ResizeObserverStub as unknown as typeof ResizeObserver);

// ResponsiveContainer usa medidas do elemento; em jsdom elas sao 0. Damos
// dimensoes fixas para os graficos conseguirem renderizar nos testes.
if (typeof globalThis.HTMLElement !== 'undefined') {
  Object.defineProperty(globalThis.HTMLElement.prototype, 'offsetWidth', {
    configurable: true,
    value: 800,
  });
  Object.defineProperty(globalThis.HTMLElement.prototype, 'offsetHeight', {
    configurable: true,
    value: 300,
  });
}
