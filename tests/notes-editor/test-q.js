// B6: página aberta com ?q=forte (command bar "o: forte"): sem documento,
// árvore completa na barra lateral, resultados da busca no centro.
const sleep = (ms = 30) => new Promise((r) => setTimeout(r, ms));
const results = [];
function check(name, cond, extra = '') { results.push(`${cond ? 'PASS' : 'FAIL'} ${name} ${cond ? '' : extra}`); }
const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
try {
  await sleep(700);
  check('q: titulo da aba = vault', document.title === 'o: MeuCofre', document.title);
  check('q: nenhum documento aberto', $('#noteState').textContent === 'sem nota aberta' && !$('textarea') && !$('.md.live'));
  check('q: arvore completa visivel na lateral', !$('#tree').hidden && $$('#tree .node').length > 0);
  check('q: lista de resultados da lateral escondida', $('#results').hidden);
  const hits = $$('.center-results .hit');
  check('q: resultados no centro', hits.some((h) => h.textContent.includes('a.md')), hits.map((h) => h.textContent).join('|'));
  check('q: cabecalho com o termo', $('.center-results .hint').textContent.includes('forte'));
  check('q: campo de busca preenchido', $('#search').value === 'forte');
  check('q: searchVault chamado uma vez com o termo', window.calls.filter((c) => c[0] === 'searchVault' && c[1] === 'forte').length === 1);
  hits.find((h) => h.textContent.includes('a.md')).click(); await sleep(200);
  check('q: clicar abre a nota', $('#noteTitle').textContent === 'a');
  check('q: titulo continua o vault', document.title === 'o: MeuCofre', document.title);
} catch (e) { results.push('ERRO ' + e.stack); }
const pre = document.createElement('pre'); pre.id = 'results'; pre.textContent = results.join('\n'); document.body.append(pre);
