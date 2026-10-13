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
  // innerHTML usage
} catch (e) { results.push('ERRO ' + e.stack); }
const pre = document.createElement('pre'); pre.id = 'results'; pre.textContent = results.join('\n'); document.body.append(pre);
