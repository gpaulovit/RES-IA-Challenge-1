// Valores compartilhados entre astro.config.mjs, scripts/sync-docs.mjs e os componentes.
export const SITE_URL = 'https://gpaulovit.github.io';
export const BASE = '/RES-IA-Challenge-1';
export const REPO_URL = 'https://github.com/gpaulovit/RES-IA-Challenge-1';

// Paletas em teste: o id casa com src/styles/paletas/<id>.css.
// Com mais de uma, o cabeçalho mostra um seletor; deixe só a escolhida para tirá-lo.
export const PALETAS = [
  { id: 'malachite', nome: 'Malachite & Grape' },
];
export const PALETA_PADRAO = PALETAS[0].id;
