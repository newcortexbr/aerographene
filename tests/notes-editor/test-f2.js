// F2: rolagem por painel e elementos novos da interface (janela 1000x600).
const sleep = (ms = 30) => new Promise((r) => setTimeout(r, ms));
const results = [];
function check(name, cond, extra = '') { results.push(`${cond ? 'PASS' : 'FAIL'} ${name} ${cond ? '' : extra}`); }
const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
const scrolls = (el) => el.scrollHeight > el.clientHeight + 1 && ['auto', 'scroll'].includes(getComputedStyle(el).overflowY);
const shot = location.search.includes('shot');
if (!shot) {
  for (let i = 0; i < 80; i++) window.files[`n${String(i).padStart(2, '0')}.md`] = {t: 'x', m: 1};
}
window.files['longa.md'] = {t: Array.from({length: 120}, (_, i) => `linha ${i} com *forte* e palavras`).join('\n\n'), m: 7};
window.files['sub/b.md'].t = 'b';
try {
  await sleep(500);
  const root = document.documentElement;
  check('f2: pagina nao estoura a janela', root.scrollHeight <= innerHeight && document.querySelector('#app').getBoundingClientRect().height <= innerHeight + 1, `${root.scrollHeight} > ${innerHeight}`);
  check('f2: arvore rola sozinha', scrolls($('#tree')));
  $('#tree').scrollTop = 200;
  check('f2: arvore rolou', $('#tree').scrollTop > 0 && window.scrollY === 0);
  check('f2: cabecalho da vault', $('.vault-head .lbl') && $('#vaultName').textContent === 'MeuCofre');
  check('f2: acoes nova nota/pasta/busca', !$('#btnNew').disabled && !!$('#btnNewDir') && !$('#btnFind').disabled);
  check('f2: atalhos visiveis', ['Ctrl+S', 'Ctrl+N', 'Ctrl+K'].every((k) => $('#vaultFoot').textContent.includes(k)));
  check('f2: estado vazio util', $('.empty-state') && $$('.empty-state kbd').length === 3);
  check('f2: contagem de notas na barra', /\d+ notas visíveis/.test($('#noteStats').textContent), $('#noteStats').textContent);
  // abre nota longa
  $$('.node').find((n) => n.dataset.path === 'sub').click(); await sleep(100);
  $$('.node').find((n) => n.dataset.path === 'longa.md').click(); await sleep(150);
  check('f2: arquivo ativo destacado', $('.node.active') && $('.node.active').dataset.path === 'longa.md');
  check('f2: editor rola sozinho', scrolls($('#editor')));
  $('#editor').scrollTop = 500;
  check('f2: editor rolou sem rolar a pagina', $('#editor').scrollTop > 0 && root.scrollHeight <= innerHeight);
  check('f2: contagem de palavras', /^\d+ palavras · \d+ caracteres$/.test($('#noteStats').textContent) && parseInt($('#noteStats').textContent) > 500, $('#noteStats').textContent);
  check('f2: estado salvo', $('#noteState').textContent === 'salvo');
  $$('.node').find((n) => n.dataset.path === 'sub/b.md').click(); await sleep(150);
  check('f2: breadcrumb com a pasta', $('#crumbs').textContent.replace(/\s/g, '') === 'sub/', $('#crumbs').textContent);
  // atalhos
  const ev = (k, o = {}) => window.dispatchEvent(new KeyboardEvent('keydown', {key: k, bubbles: true, cancelable: true, ...o}));
  ev('k', {ctrlKey: true});
  check('f2: Ctrl+K foca a busca', document.activeElement === $('#search'));
  // busca com muitos resultados rola no seu painel
  search_hits: {
    $('#search').value = 'md';
    $('#search').dispatchEvent(new Event('input', {bubbles: true}));
    await sleep(700);
    check('f2: resultados da busca rolam sozinhos', !$('#results').hidden && scrolls($('#results')), `h=${$('#results').hidden} ${$('#results').scrollHeight}/${$('#results').clientHeight} n=${$('#results').children.length} q=${$('#search').value}`);
    check('f2: pagina continua sem estourar', root.scrollHeight <= innerHeight);
  }
  $('#search').value = ''; $('#search').dispatchEvent(new Event('input', {bubbles: true})); await sleep(400);
  // conflito
  if (!shot) {
  window.files['sub/b.md'].m += 5;
  const ta0 = $('.md.live .piece, .md.live p'); ta0.click(); await sleep(50);
  const ta = $('textarea'); ta.dispatchEvent(new InputEvent('beforeinput', {bubbles: true})); ta.value = 'b!'; ta.dispatchEvent(new Event('input', {bubbles: true}));
  $('#btnSave').click(); await sleep(150);
  check('f2: estado conflito', $('#noteState').textContent.includes('conflito') && $('#noteState').classList.contains('conflict'), $('#noteState').textContent);
  }
} catch (e) { results.push('ERRO ' + e.stack); }
if (shot) {
  // deixa a nota longa aberta para a captura de tela
  $$('.node').find((n) => n.dataset.path === 'longa.md')?.click();
} else {
  const pre = document.createElement('pre'); pre.id = 'results'; pre.textContent = results.join('\n'); document.body.append(pre);
}
