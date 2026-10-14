// F2B: modos da lateral, abas de notas, contagens, status bar, tags, backlinks,
// recentes, ler/editar (janela 1000x600, backend simulado).
const sleep = (ms = 30) => new Promise((r) => setTimeout(r, ms));
const results = [];
function check(name, cond, extra = '') { results.push(`${cond ? 'PASS' : 'FAIL'} ${name} ${cond ? '' : extra}`); }
const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
const row = (p) => $$('.node').find((n) => n.dataset.path === p);
const tab = (p) => $$('.nt').find((n) => n.dataset.path === p);
const type = (ta, text) => { ta.dispatchEvent(new InputEvent('beforeinput', {bubbles: true})); ta.value = text; ta.dispatchEvent(new Event('input', {bubbles: true})); };
const btn = (label) => $$('button').find((x) => x.textContent === label && !x.closest('[hidden]'));
// semeia ANTES de a página ler a vault (getVault responde em setTimeout 0)
localStorage.clear();
localStorage.setItem('aero.notes.recent', JSON.stringify({vault: '/home/u/MeuCofre', items: [{path: 'a.md', ts: 2}, {path: 'sub/b.md', ts: 1}]}));
Object.assign(window.files, {
  'sub/deep/c.md': {t: '# c\ntexto #tag-x aqui', m: 1},
  'link.md': {t: 'ver [[a]] e [[sub/b]]\n\nsegunda linha', m: 1},
  'tagged.md': {t: '---\ntags: [alfa, beta]\n---\ncorpo #gama\n', m: 1},
  'nolink.md': {t: 'fala de [[ab]] e [[a-outra]]', m: 1},
});
try {
  await sleep(700);
  // estado vazio com recentes
  const rec = $$('.empty-state .rec-row');
  check('f2b: recentes no estado vazio', rec.length === 2 && rec[0].dataset.path === 'a.md' && rec[1].textContent.includes('b') && rec[1].textContent.includes('sub'), rec.map((r) => r.textContent).join('|'));
  check('f2b: faixa mostra sem nota aberta', $('#noteState').textContent === 'sem nota aberta' && $$('.nt').length === 0);
  check('f2b: status bar no estado vazio', $('#sbMode').textContent === 'VAULT' && /\d+ notas visíveis/.test($('#noteStats').textContent) && $('#sbWords').hidden);
  check('f2b: crumb raiz', $('#crumbs').textContent.replace(/\s/g, '') === 'vault:(raiz)', $('#crumbs').textContent);
  // desabilitados
  check('f2b: desabilitados visiveis (pasta, trocar vault, mais)', ['#btnNewDir', '#btnSwap', '#btnMore'].every((s) => $(s) && $(s).disabled && getComputedStyle($(s)).display !== 'none'));
  check('f2b: ler/editar sem nota desabilitado', $('#btnRead').disabled);
  // contagens por pasta
  const cnt = (p) => row(p) && row(p).querySelector('.cnt') && row(p).querySelector('.cnt').textContent;
  check('f2b: contagem recursiva da pasta', cnt('sub') === '2', String(cnt('sub')));
  row('sub').click(); await sleep(100);
  check('f2b: contagem da subpasta', cnt('sub/deep') === '1', String(cnt('sub/deep')));
  check('f2b: guias de recuo e triangulo', row('sub/b.md').querySelectorAll('.ind').length === 1 && row('sub').getAttribute('aria-expanded') === 'true' && !!row('sub').querySelector('.g'));
  check('f2b: extensao .md em destaque separado', row('sub/b.md').querySelector('.nm i').textContent === '.md');
  // recolher
  $('#btnCollapse').click(); await sleep(150);
  check('f2b: recolher fecha as pastas', row('sub').getAttribute('aria-expanded') === 'false' && !row('sub/b.md'));
  // ordenar
  const firstFile = () => $$('#tree > .node.file')[0].dataset.path;
  const f0 = firstFile();
  $('#btnSort').click(); await sleep(150);
  check('f2b: ordenar inverte os arquivos', firstFile() !== f0 && firstFile() === 'tagged.md', firstFile());
  check('f2b: ordem guardada', localStorage.getItem('aero.notes.sort') === 'desc');
  $('#btnSort').click(); await sleep(150);
  check('f2b: ordenar volta ao A-Z', firstFile() === f0);
  // modos
  $('#modeSearch').click();
  check('f2b: modo buscar mostra o campo', !$('#searchBox').hidden && $('#tree').hidden && !$('#results').hidden && document.activeElement === $('#search'));
  $('#modeTags').click(); await sleep(600);
  const tagRows = $$('.tag-row').map((r) => r.dataset.tag);
  check('f2b: modo tags lista as tags das notas', ['alfa', 'beta', 'gama', 'tag-x'].every((t) => tagRows.includes(t)), tagRows.join(','));
  check('f2b: tags sem os titulos markdown', !tagRows.includes('Titulo') && !tagRows.includes('c'));
  const alfa = $$('.tag-row').find((r) => r.dataset.tag === 'alfa');
  check('f2b: contagem da tag', alfa.querySelector('.cnt').textContent === '1');
  alfa.click(); await sleep(30);
  const tn = $$('.tag-note').find((n) => n.dataset.path === 'tagged.md');
  check('f2b: tag expande as notas', !!tn);
  tn.click(); await sleep(200);
  check('f2b: abrir pela tag cria a aba', !!tab('tagged.md') && $('#noteTitle').textContent === 'tagged');
  check('f2b: chips de tags no cabecalho', $$('#noteTags .tag').map((t) => t.textContent).join(',') === 'alfa,beta,gama', $$('#noteTags .tag').map((t) => t.textContent).join(','));
  $('#modeFiles').click();
  check('f2b: modo arquivos volta a arvore', !$('#tree').hidden && $('#searchBox').hidden && $('#modeFiles').classList.contains('on'));
  // abas
  row('a.md').click(); await sleep(150);
  row('link.md').click(); await sleep(150);
  check('f2b: tres abas abertas', $$('.nt').length === 3 && tab('link.md').classList.contains('act'));
  check('f2b: so uma aba ativa', $$('.nt.act').length === 1);
  check('f2b: breadcrumb da ativa', $('#crumbs').textContent.replace(/\s/g, '') === 'vault:link.md');
  // edicao + marca de nao salvo por aba
  $('.md.live .piece').click(); await sleep(50);
  type($('textarea'), 'ver [[a]] e [[sub/b]] editado');
  check('f2b: marca de nao salvo na aba', tab('link.md').classList.contains('dirty') && getComputedStyle(tab('link.md').querySelector('.dd')).display !== 'none' && !tab('a.md').classList.contains('dirty'));
  check('f2b: faixa alterado', $('#noteState').textContent === '● alterado');
  tab('a.md').click(); await sleep(150);
  check('f2b: trocar de aba mostra a outra nota', $('.md.live').textContent.includes('Titulo') && $('#noteState').textContent === 'salvo');
  check('f2b: aba suja continua suja', tab('link.md').classList.contains('dirty'));
  check('f2b: breadcrumb e titulo seguem a aba', $('#noteTitle').textContent === 'a' && !$('#docHead').hidden);
  tab('link.md').click(); await sleep(150);
  check('f2b: texto nao salvo volta ao reativar', $('#noteState').textContent === '● alterado' && $('textarea') && $('textarea').value.includes('editado'));
  // fechar suja pede confirmacao
  tab('link.md').querySelector('.x').click(); await sleep(60);
  check('f2b: fechar aba suja pergunta', !$('#banner').hidden && $('#banner').textContent.includes('não salvas'));
  $$('#banner button').find((b) => b.textContent === 'salvar').click(); await sleep(200);
  check('f2b: salvar e fechar grava', window.files['link.md'].t.includes('editado') && !tab('link.md'), String(!!tab('link.md')));
  check('f2b: ao fechar a ativa a vizinha assume', $$('.nt.act').length === 1);
  // status bar
  tab('a.md').click(); await sleep(150);
  check('f2b: selo EDIT e pasta', $('#sbMode').textContent === 'EDIT' && $('#sbPath').textContent === '(raiz)');
  const p3 = $$('.md.live p').find((x) => x.textContent.includes('forte'));
  p3.click(); await sleep(60);
  check('f2b: linha:coluna', $('#sbPos').textContent === 'L3:C19', $('#sbPos').textContent);
  $('textarea').setSelectionRange(5, 5); $('textarea').dispatchEvent(new KeyboardEvent('keyup', {key: 'ArrowLeft', bubbles: true}));
  check('f2b: coluna acompanha o cursor', $('#sbPos').textContent === 'L3:C6', $('#sbPos').textContent);
  check('f2b: palavras, caracteres e codificacao', /^\d+ palavras$/.test($('#sbWords').textContent) && /^\d+ caracteres$/.test($('#sbChars').textContent) && $('#sbEnc').textContent === 'UTF-8 · LF');
  const chars = parseInt($('#sbChars').textContent);
  type($('textarea'), 'texto *forte* aqui!!');
  check('f2b: caracteres atualizam ao digitar', parseInt($('#sbChars').textContent) === chars + 2, $('#sbChars').textContent);
  // ler / editar
  $('#btnRead').click(); await sleep(50);
  check('f2b: modo ler sem textarea', $('#sbMode').textContent === 'LER' && !$('textarea') && $('.md.live').classList.contains('read'));
  $$('.md.live p').find((x) => x.textContent.includes('forte')).click(); await sleep(50);
  check('f2b: clicar no modo ler nao edita', !$('textarea'));
  check('f2b: texto editado preservado no modo ler', $('#noteState').textContent === '● alterado');
  $('#btnRead').click(); await sleep(30);
  $$('.md.live p').find((x) => x.textContent.includes('forte')).click(); await sleep(50);
  check('f2b: editar volta a permitir edicao', $('#sbMode').textContent === 'EDIT' && !!$('textarea'));
  btn('salvar').click(); await sleep(150);
  // backlinks
  tab('a.md').click(); await sleep(50);
  await sleep(500);
  check('f2b: backlinks confirmados por [[link]]', $('#sbBack').textContent === '← 1 backlinks' && !$('#sbBack').disabled, $('#sbBack').textContent);
  $('#sbBack').click(); await sleep(50);
  check('f2b: clicar nos backlinks lista a nota', !$('#results').hidden && $$('.hit').some((h) => h.textContent.includes('link.md')) && !$$('.hit').some((h) => h.textContent.includes('nolink')));
  $('#modeFiles').click();
  // fechar tudo -> recentes
  for (const t of $$('.nt')) { if (t.querySelector('.x')) t.querySelector('.x').click(); await sleep(60); const b = btn('descartar'); if (b) { b.click(); await sleep(60); } }
  check('f2b: todas as abas fechadas', $$('.nt').length === 0 && $('.empty-state'));
  const rec2 = $$('.empty-state .rec-row').map((r) => r.dataset.path);
  check('f2b: recentes incluem o que foi aberto', rec2.includes('link.md') && rec2.includes('tagged.md') && rec2.includes('a.md'), rec2.join(','));
  check('f2b: recentes limitados', rec2.length <= 8);
  $$('.empty-state .rec-row').find((r) => r.dataset.path === 'tagged.md').click(); await sleep(200);
  check('f2b: abrir recente cria aba', !!tab('tagged.md'));
  // layout: faixa de abas e barra de status
  const sb = $('#statusBar').getBoundingClientRect();
  check('f2b: barra de status no rodape da janela', Math.abs(sb.bottom - innerHeight) <= 1 && sb.height === 30, `${sb.bottom} ${sb.height}`);
  check('f2b: faixa de abas com 34px', $('#tabsBar').getBoundingClientRect().height === 34);
  check('f2b: seletor da vault embaixo a esquerda', $('.vsel').getBoundingClientRect().bottom <= innerHeight && $('.vsel').getBoundingClientRect().left < 40);
  check('f2b: pagina nao estoura', document.documentElement.scrollHeight <= innerHeight);
} catch (e) { results.push('ERRO ' + e.stack); }
const pre = document.createElement('pre'); pre.id = 'results'; pre.textContent = results.join('\n'); document.body.append(pre);
