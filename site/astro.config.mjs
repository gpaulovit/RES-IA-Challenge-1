import { readFileSync } from 'node:fs';

import starlight from '@astrojs/starlight';
import { defineConfig } from 'astro/config';
import mermaid from 'astro-mermaid';

import { BASE, PALETA_PADRAO, PALETAS, REPO_URL, SITE_URL } from './site.config.mjs';

// Aplica a paleta antes da pintura (escolha salva no navegador ou a padrão), sem piscar.
const scriptPaleta = `(() => {
  const validas = ${JSON.stringify(PALETAS.map((p) => p.id))};
  let p = null;
  try { p = localStorage.getItem('paleta'); } catch {}
  document.documentElement.dataset.paleta = validas.includes(p) ? p : ${JSON.stringify(PALETA_PADRAO)};
})();`;

// O menu vem de docs/_sidebar.md (o mesmo do Docsify), para não manter dois menus.
// Formato: "- [Rótulo](arquivo.md)" é link; "- Rótulo" sem link abre um grupo; itens indentados entram no grupo.
function lerSidebar() {
  const itens = [];
  let grupo = null;
  for (const linha of readFileSync(new URL('../docs/_sidebar.md', import.meta.url), 'utf8').split('\n')) {
    const m = linha.match(/^(\s*)- (?:\[(.+)\]\((.+)\)|(.+))$/);
    if (!m) continue;
    const [, indent, rotulo, alvo, titulo] = m;
    if (titulo) {
      grupo = { label: titulo.trim(), items: [] };
      itens.push(grupo);
      continue;
    }
    const slug = alvo === '/' ? '' : alvo.replace(/\.md$/, '').replace(/(^|\/)README$/, '');
    const item = { label: rotulo, link: `/${slug ? `${slug}/` : ''}` };
    (indent && grupo ? grupo.items : itens).push(item);
    if (!indent) grupo = null;
  }
  return itens;
}

export default defineConfig({
  site: SITE_URL,
  base: BASE,
  integrations: [
    // precisa vir antes do starlight para pegar os blocos ```mermaid
    mermaid({ autoTheme: true }),
    starlight({
      title: 'ChecaAí',
      description: 'Estimativa da chance de uma notícia política ser falsa a partir de boatos já checados (RES-IA-Challenge-1)',
      defaultLocale: 'root',
      locales: { root: { label: 'Português', lang: 'pt-BR' } },
      social: [{ icon: 'github', label: 'GitHub', href: REPO_URL }],
      sidebar: lerSidebar(),
      customCss: ['./src/styles/tema.css'],
      head: [{ tag: 'script', content: scriptPaleta }],
      components: { ThemeSelect: './src/components/SeletorTema.astro' },
    }),
  ],
});
