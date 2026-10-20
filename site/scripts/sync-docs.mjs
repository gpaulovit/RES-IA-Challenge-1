// Copia docs/ (fonte única, a mesma do Docsify) para src/content/docs/ no formato do Starlight.
// - o primeiro "# Título" vira o frontmatter `title`
// - README.md vira index.md
// - links para outros .md viram rotas do site; links para arquivos fora de docs/ vão para o GitHub
// - imagens e demais arquivos são copiados como estão (o Astro otimiza as imagens referenciadas)
import { cpSync, mkdirSync, readdirSync, readFileSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { dirname, join, posix, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

import { BASE, REPO_URL } from '../site.config.mjs';

const SITE = dirname(dirname(fileURLToPath(import.meta.url)));
const DOCS = join(SITE, '..', 'docs');
const OUT = join(SITE, 'src', 'content', 'docs');
const IGNORAR = new Set(['index.html', '_sidebar.md']);

const HERO = {
  tagline:
    'Bot no Telegram que confere mensagens sobre as eleições de 2026: busca checagens de agências e, sem checagem parecida, mostra uma faixa de alerta.',
  actions: [
    { text: 'Testar o bot', link: 'https://t.me/checaai_bot', icon: 'right-arrow' },
    { text: 'Ver o código', link: REPO_URL, icon: 'github', variant: 'minimal' },
  ],
};

// docs/foo/README.md -> "foo", docs/bar.md -> "bar", docs/README.md -> ""
function rota(caminhoDocs) {
  const semExt = caminhoDocs.replace(/\.md$/, '');
  return semExt === 'README' ? '' : semExt.replace(/\/README$/, '');
}

function reescreverLinks(texto, arquivoRel) {
  const pasta = posix.dirname(arquivoRel);
  return texto.replace(/(!?)\[([^\]]*)\]\(([^)\s]+)\)/g, (todo, img, rotulo, alvo) => {
    if (img || /^([a-z]+:|#|\/)/i.test(alvo)) return todo;
    const [caminho, ancora] = alvo.split('#');
    const resolvido = posix.normalize(posix.join(pasta, caminho));
    const sufixo = ancora ? `#${ancora}` : '';
    if (resolvido.startsWith('../')) {
      return `[${rotulo}](${REPO_URL}/blob/main/${resolvido.slice(3)}${sufixo})`;
    }
    if (resolvido.endsWith('.md')) {
      const r = rota(resolvido);
      return `[${rotulo}](${BASE}/${r ? `${r}/` : ''}${sufixo})`;
    }
    return todo;
  });
}

function converter(arquivoRel) {
  const bruto = readFileSync(join(DOCS, arquivoRel), 'utf8');
  const h1 = bruto.match(/^# (.+)$/m);
  if (!h1) throw new Error(`${arquivoRel}: sem título "# ..." na primeira seção`);
  const corpo = reescreverLinks(bruto.replace(h1[0], '').trimStart(), arquivoRel);

  const fm = {
    title: h1[1].trim(),
    editUrl: `${REPO_URL}/edit/main/docs/${arquivoRel}`,
    ...(arquivoRel === 'README.md' ? { hero: HERO } : {}),
  };
  // JSON é YAML válido, então dispensa uma lib de YAML
  return `---\n${Object.entries(fm).map(([k, v]) => `${k}: ${JSON.stringify(v)}`).join('\n')}\n---\n\n${corpo}`;
}

function percorrer(pastaRel = '') {
  for (const nome of readdirSync(join(DOCS, pastaRel))) {
    const rel = pastaRel ? `${pastaRel}/${nome}` : nome;
    if (IGNORAR.has(rel)) continue;
    if (statSync(join(DOCS, rel)).isDirectory()) {
      percorrer(rel);
    } else if (nome.endsWith('.md')) {
      const destino = join(OUT, rel.replace(/(^|\/)README\.md$/, '$1index.md'));
      mkdirSync(dirname(destino), { recursive: true });
      writeFileSync(destino, converter(rel));
    } else {
      mkdirSync(dirname(join(OUT, rel)), { recursive: true });
      cpSync(join(DOCS, rel), join(OUT, rel));
    }
  }
}

rmSync(OUT, { recursive: true, force: true });
percorrer();
console.log(`docs/ sincronizado em ${relative(process.cwd(), OUT) || '.'}`);
