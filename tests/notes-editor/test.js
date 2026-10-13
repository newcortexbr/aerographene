const sleep = (ms = 30) => new Promise((r) => setTimeout(r, ms));
const results = [];
function check(name, cond, extra = '') { results.push(`${cond ? 'PASS' : 'FAIL'} ${name} ${cond ? '' : extra}`); }
const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
function key(el, k, opts = {}) { const e = new KeyboardEvent('keydown', {key: k, bubbles: true, cancelable: true, ...opts}); el.dispatchEvent(e); return e; }
function type(ta, text) { ta.dispatchEvent(new InputEvent('beforeinput', {bubbles: true})); ta.value = text; ta.dispatchEvent(new Event('input', {bubbles: true})); }
function clickBtn(label) { const b = $$('button').find((x) => x.textContent.startsWith(label) && !x.closest('[hidden]')); if (!b) throw new Error('btn ' + label); b.click(); }
try {
  await sleep(200);
  check('titulo da aba = vault', document.title === 'o: MeuCofre', document.title);
  const rowA = $$('.node').find((n) => n.dataset.path === 'a.md');
  rowA.click(); await sleep(100);
  check('titulo da aba nao muda ao abrir nota', document.title === 'o: MeuCofre', document.title);
  check('h1 renderizado', !!$('.md.live h1'));
  check('nenhum textarea antes de clicar', !$('textarea'));
  const p = $$('.md.live p').find((x) => x.textContent.includes('forte'));
  p.click(); await sleep(50);
  const ta = $('textarea');
  check('linha ativa crua', !!ta && ta.value === 'texto *forte* aqui', ta && ta.value);
  check('h1 continua renderizado com linha ativa', !!$('.md.live h1'));
  check('lista renderizada', $$('.md.live li').length === 2);
  type(ta, 'texto *forte* aqui!');
  check('estado alterado', $('#noteState').textContent.includes('alterado'));
  check('botao salvar habilitado', !$('#btnSave').disabled);
  // Enter splits
  ta.setSelectionRange(5, 5);
  key(ta, 'Enter'); await sleep(30);
  let ta2 = $('textarea');
  check('Enter divide a linha', ta2 && ta2.value === ' *forte* aqui!', ta2 && ta2.value);
  // Backspace at 0 merges
  ta2.setSelectionRange(0, 0); key(ta2, 'Backspace'); await sleep(30);
  ta2 = $('textarea');
  check('Backspace junta', ta2.value === 'texto *forte* aqui!', ta2.value);
  // undo
  key(ta2, 'z', {ctrlKey: true}); await sleep(30);
  check('Ctrl+Z desfaz a juncao', $('textarea').value === ' *forte* aqui!', $('textarea').value);
  key($('textarea'), 'z', {ctrlKey: true}); await sleep(30);
  check('Ctrl+Z desfaz a divisao', $('textarea').value === 'texto *forte* aqui!', $('textarea').value);
  // arrow down moves
  key($('textarea'), 'ArrowDown'); await sleep(30);
  check('seta baixo ativa a proxima linha (vazia)', $('textarea').value === '');
  // save
  key($('textarea'), 's', {ctrlKey: true}); await sleep(80);
  const w = window.calls.filter((c) => c[0] === 'writeNote').at(-1);
  check('writeNote com mtime aberto', w && w[1] === 'a.md' && w[3] === 1000 && w[2].includes('aqui!'), JSON.stringify(w));
  check('estado salvo', $('#noteState').textContent === 'salvo', $('#noteState').textContent);
  check('arquivo mudou', window.files['a.md'].t.includes('aqui!'));
  // conflict
  window.files['a.md'].m += 500; window.files['a.md'].t = 'EXTERNO';
  type($('textarea'), 'meu texto novo');
  clickBtn('salvar'); await sleep(100);
  check('banner de conflito', !$('#banner').hidden && $('#banner').textContent.includes('mudou no disco'), $('#banner').textContent);
  check('texto do editor preservado', $('textarea').value === 'meu texto novo');
  check('disco intacto no conflito', window.files['a.md'].t === 'EXTERNO');
  clickBtn('salvar como cópia'); await sleep(150);
  const cc = window.calls.filter((c) => c[0] === 'createNote').at(-1);
  check('copia criada com o texto', cc && /^a \(conflito .*\)\.md$/.test(cc[1]) && cc[2].includes('meu texto novo'), JSON.stringify(cc));
  check('titulo da aba segue so a vault', document.title === 'o: MeuCofre');
  check('abriu a copia', $('#noteTitle').textContent.startsWith('a (conflito'), $('#noteTitle').textContent);
  // sobrescrever path
  requestAnimationFrame(() => {});
  // rename
  clickBtn('renomear'); await sleep(30);
  const inp = $('#banner input'); inp.value = 'sub/renomeada.md';
  key(inp, 'Enter'); await sleep(100);
  const rn = window.calls.filter((c) => c[0] === 'renameNote').at(-1);
  check('renameNote enviado', rn && rn[2] === 'sub/renomeada.md', JSON.stringify(rn));
  check('titulo do cabecalho segue o arquivo', $('#noteTitle').textContent === 'renomeada.md', $('#noteTitle').textContent);
  check('titulo da aba intacto apos renomear', document.title === 'o: MeuCofre');
  // delete
  clickBtn('apagar'); await sleep(30);
  check('pede confirmacao antes de apagar', !$('#banner').hidden && $('#banner').textContent.includes('Não vai para a lixeira'));
  $$('#banner button').find((b) => b.textContent === 'apagar').click(); await sleep(100);
  check('deleteNote enviado', window.calls.some((c) => c[0] === 'deleteNote'));
  check('titulo da aba intacto apos apagar', document.title === 'o: MeuCofre');
  // nova nota
  $('#btnNew').click(); await sleep(30);
  $('#banner input').value = 'nova'; 
  key($('#banner input'), 'Enter'); await sleep(120);
  const cn = window.calls.filter((c) => c[0] === 'createNote').at(-1);
  check('nova nota ganha .md', cn[1] === 'nova.md', JSON.stringify(cn));
  check('editor aberto para a nova', !!$('textarea') || $('.md.live'));

  // ---- B5: watcher, busca, imagens ----
  const nCalls = (n) => window.calls.filter((c) => c[0] === n).length;
  check('watchVault chamado ao abrir a vault', nCalls('watchVault') === 1);
  check('sem aviso de watcher quando ativo', !$('#vaultName').classList.contains('nowatch'));
  // arquivo criado fora aparece na arvore
  window.files['fora.md'] = {t: 'criado fora CENOURA', m: 7000};
  window.fire('vaultChanged'); await sleep(400);
  check('arquivo criado fora aparece', $$('.node').some((n) => n.dataset.path === 'fora.md'));
  // nota aberta limpa: edicao externa recarrega
  $$('.node').find((n) => n.dataset.path === 'fora.md').click(); await sleep(100);
  check('abriu fora.md', $('#noteTitle').textContent === 'fora.md');
  window.files['fora.md'].t = 'alterado fora'; window.files['fora.md'].m = 7100;
  window.fire('vaultChanged'); await sleep(500);
  check('nota limpa recarrega do disco', $('.md.live').textContent.includes('alterado fora'), $('.md.live').textContent);
  check('titulo da aba intacto apos evento', document.title === 'o: MeuCofre');
  // sem mudanca de conteudo, so mtime: nao recarrega nem avisa
  window.files['fora.md'].m = 7150;
  const readsBefore = nCalls('readNote');
  window.fire('vaultChanged'); await sleep(500);
  check('so mtime: sem aviso', $('#banner').hidden);
  // nota suja + edicao externa => fluxo de conflito do B4
  $('.md.live p').click(); await sleep(50);
  type($('textarea'), 'meu rascunho'); await sleep(30);
  window.files['fora.md'].t = 'versao externa 2'; window.files['fora.md'].m = 7200;
  window.fire('vaultChanged'); await sleep(500);
  check('conflito externo abre o aviso do B4', !$('#banner').hidden && $('#banner').textContent.includes('mudou no disco'), $('#banner').textContent);
  check('texto local preservado no conflito', $('textarea') && $('textarea').value === 'meu rascunho');
  check('disco intacto no conflito', window.files['fora.md'].t === 'versao externa 2');
  // cancelar: nao pergunta de novo para a mesma versao
  $$('#banner button').find((b) => b.textContent === 'cancelar').click(); await sleep(50);
  window.fire('vaultChanged'); await sleep(500);
  check('nao pergunta de novo para a mesma versao', $('#banner').hidden);
  check('texto local ainda la', $('textarea').value === 'meu rascunho');
  // salvar agora ainda cai no conflito (token antigo)
  clickBtn('salvar'); await sleep(100);
  check('salvar apos cancelar ainda detecta conflito', !$('#banner').hidden && $('#banner').textContent.includes('mudou no disco'));
  $$('#banner button').find((b) => b.textContent.startsWith('recarregar')).click(); await sleep(150);
  check('recarregar traz o disco', $('.md.live').textContent.includes('versao externa 2'));
  // nota apagada fora
  delete window.files['fora.md'];
  window.fire('vaultChanged'); await sleep(500);
  check('nota apagada fora: aviso e editor limpo', !$('#banner').hidden && $('#banner').textContent.includes('apagada') && $('#noteTitle').textContent === 'sem nota aberta', $('#banner').textContent);
  $$('#banner button').find((b) => b.textContent === 'ok').click();
  check('arvore sem o arquivo apagado', !$$('.node').some((n) => n.dataset.path === 'fora.md'));
  // rajada de eventos vira poucas leituras
  const listsBefore = nCalls('listDir');
  for (let i = 0; i < 20; i++) window.fire('vaultChanged');
  await sleep(600);
  check('rajada de eventos coalescida', nCalls('listDir') - listsBefore <= 3, String(nCalls('listDir') - listsBefore));

  // busca
  window.files['busca.md'] = {t: 'linha\nmeu bolo de Cenoura\nfim', m: 8000};
  window.fire('vaultChanged'); await sleep(400);
  const s = $('#search');
  check('busca habilitada com vault', !s.disabled);
  s.value = 'cenoura'; s.dispatchEvent(new Event('input', {bubbles: true})); await sleep(700);
  check('resultados visiveis, arvore escondida', !$('#results').hidden && $('#tree').hidden);
  const hit = $$('.hit').find((h) => h.textContent.includes('busca.md'));
  check('resultado com snippet', hit && hit.textContent.includes('meu bolo de Cenoura'), hit && hit.textContent);
  hit.click(); await sleep(150);
  check('clicar no resultado abre a nota', $('#noteTitle').textContent === 'busca.md');
  s.value = ''; s.dispatchEvent(new Event('input', {bubbles: true})); await sleep(500);
  check('limpar a busca volta a arvore', $('#results').hidden && !$('#tree').hidden);
  s.value = 'a'; s.dispatchEvent(new Event('input', {bubbles: true})); await sleep(500);
  check('consulta curta nao busca', $('#results').hidden);
  s.value = '';

  // imagens
  window.files['img.md'] = {t: 'antes\n\n![foto](pic.png)\n\n![[pic.png|120]]\n\n![remota](https://x.test/a.png)\n\n![abs](/etc/a.png)\n\n![falta](nada.png)\n\n![[outra nota]]\n', m: 9000};
  $('#tree'); window.fire('vaultChanged'); await sleep(400);
  $$('.node').find((n) => n.dataset.path === 'img.md').click(); await sleep(400);
  const imgs = $$('.md.live img');
  check('imagem da vault vira <img> com data:', imgs.length === 2 && imgs.every((i) => i.src.startsWith('data:image/png;base64,')), imgs.map((i) => i.src.slice(0, 30)).join('|'));
  check('largura do embed', imgs[1] && imgs[1].style.width === '120px');
  const txt = $('.md.live').textContent;
  check('remota nao carrega', txt.includes('[imagem: remota]'));
  check('absoluta nao carrega', txt.includes('[imagem: abs]'));
  check('imagem ausente vira texto', txt.includes('[imagem: falta]'));
  check('embed de nota vira texto', txt.includes('[nota embutida: outra nota]'));
  check('so um readImage por imagem repetida', window.calls.filter((c) => c[0] === 'readImage' && c[1] === 'pic.png').length === 1, String(window.calls.filter((c) => c[0] === 'readImage' && c[1] === 'pic.png').length));
  check('readImage nunca recebe URL remota', !window.calls.some((c) => c[0] === 'readImage' && /^(https?:|\/)/.test(c[1])));
  // innerHTML usage
} catch (e) { results.push('ERRO ' + e.stack); }
const pre = document.createElement('pre'); pre.id = 'results'; pre.textContent = results.join('\n'); document.body.append(pre);
