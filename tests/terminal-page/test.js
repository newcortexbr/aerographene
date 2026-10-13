const sleep = (ms = 30) => new Promise((r) => setTimeout(r, ms));
const results = [];
function check(name, cond, extra = '') { results.push(`${cond ? 'PASS' : 'FAIL'} ${name} ${cond ? '' : extra}`); }
const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
const writes = () => calls.filter((c) => c[0] === 'write');
async function bufText(win) {
  for (const [t, text] of termLog) {
    if (t.element && win.contains(t.element)) {
      return text;
    }
  }
  return '';
}
function key(el, opts) {
  const e = new KeyboardEvent('keydown', {bubbles: true, cancelable: true, ...opts});
  el.dispatchEvent(e);
  return e;
}
const isNew = new URLSearchParams(location.search).get('new') === '1';
try {
  await sleep(300);
  const w1 = $('.win');
  if (isNew) {
    check('titulo t: workspace N (novo)', document.title === 't: workspace 3', document.title);
    check('URL vira ?w=3 (recarregar nao cria outro)', location.search === '?w=3', location.search);
    check('comando ainda nao digitado antes de 0,5 s', performance.now() >= 500 || writes().length === 0);
    await sleep(600);
    const w = writes();
    check('comando digitado uma vez com Enter', w.length === 1 && w[0][1] === 7 && w[0][2] === 'echo oi\r', JSON.stringify(w));
    check('start chamado com 0 (novo)', calls.find((c) => c[0] === 'start')[2] === 0);
  } else {
    check('titulo t: workspace 2', document.title === 't: workspace 2', document.title);
    check('sem comando sem ?new', writes().length === 0);
  }
  check('sem barra superior', !$('header.bar') && !$('#zoom'));
  check('botoes de canto', !!$('#sideToggle.corner') && !!$('#add.corner'));
  check('barra de titulo so com x', w1.querySelector('.win-head').children.length === 1 &&
        w1.querySelector('.win-head').textContent.trim() === '×');
  const t1 = await bufText(w1);
  check('banner: versoes, cpu, gpu, ram, disco', ['aerographene', 'v0.3.0', '141.0.7390.0', 'Fake CPU (8 threads)', 'Fake GPU', '16.0 GiB', 'disco /'].every((s) => t1.includes(s)), t1.slice(0, 400));
  check('banner: gatinho', t1.includes('⣿⣿⣿'));
  check('banner: disco repetido some', !t1.includes('disco /home/u'));
  check('banner antes do prompt', t1.indexOf('aerographene') < t1.lastIndexOf('$'), JSON.stringify(t1.slice(-60)) + JSON.stringify(calls.filter((c) => c[0] !== 'write')));
  // + abre outro
  $('#add').click(); await sleep(100);
  const wins = $$('.win');
  check('+ abre terminal', wins.length === 2);
  const t2 = await bufText(wins[1]);
  check('banner tambem no segundo', t2.includes('Fake GPU'), t2.slice(0, 300));
  // foco: o novo esta focado; Ctrl+C manda ^C para a sessao dele
  const ta2 = wins[1].querySelector('textarea');
  check('novo terminal focado', wins[1].classList.contains('focused') && document.activeElement === ta2);
  const before = writes().length;
  const ec = key(ta2, {key: 'c', code: 'KeyC', ctrlKey: true, keyCode: 67});
  await sleep(30);
  const wc = writes().slice(before);
  check('Ctrl+C vira ^C na sessao focada', wc.length === 1 && wc[0][2] === '\x03' && wc[0][1] === 8, JSON.stringify(wc));
  // Ctrl+Shift+C copia selecao e nao deixa o navegador pegar
  wins[1].__term = null;
  const sel = key(ta2, {key: 'C', code: 'KeyC', ctrlKey: true, shiftKey: true, keyCode: 67});
  check('Ctrl+Shift+C preventDefault', sel.defaultPrevented);
  check('Ctrl+Shift+C nao manda nada ao pty', writes().length === before + 1);
  const pv = key(ta2, {key: 'V', code: 'KeyV', ctrlKey: true, shiftKey: true, keyCode: 86});
  check('Ctrl+Shift+V fica para o evento paste', !pv.defaultPrevented && writes().length === before + 1);
  ta2.dispatchEvent(new ClipboardEvent('paste', {bubbles: true, cancelable: true, clipboardData: (() => { const d = new DataTransfer(); d.setData('text/plain', 'colado'); return d; })()}));
  await sleep(30);
  check('paste vai para a sessao focada', writes().some((c) => c[1] === 8 && c[2].includes('colado')), JSON.stringify(writes()));
  // clicar fora tira o foco
  const board = $('#board');
  board.dispatchEvent(new PointerEvent('pointerdown', {bubbles: true, button: 0, clientX: 900, clientY: 700, pointerId: 1}));
  board.dispatchEvent(new PointerEvent('pointerup', {bubbles: true, button: 0, pointerId: 1}));
  await sleep(30);
  check('clicar no fundo tira o foco', !$('.win.focused') && !document.activeElement?.closest?.('.win'));
  // sidebar
  $('#sideToggle').click(); await sleep(30);
  const items = $$('#sideList button');
  check('sidebar lista os 2', !$('#side').hidden && items.length === 2, items.length);
  items[0].click(); await sleep(30);
  check('sidebar foca o terminal', wins[0].classList.contains('focused') && document.activeElement === wins[0].querySelector('textarea'));
  const r = board.getBoundingClientRect();
  const wr = wins[0].getBoundingClientRect();
  check('sidebar centraliza', Math.abs((wr.left + wr.width / 2) - (r.left + r.width / 2)) < 3 && Math.abs((wr.top + wr.height / 2) - (r.top + r.height / 2)) < 3, `${wr.left},${wr.top}`);
  // arrastar so pela barra de titulo
  const left0 = wins[0].style.left;
  const body = wins[0].querySelector('.win-body');
  body.dispatchEvent(new PointerEvent('pointerdown', {bubbles: true, button: 0, clientX: 300, clientY: 300, pointerId: 2}));
  body.dispatchEvent(new PointerEvent('pointermove', {bubbles: true, clientX: 400, clientY: 300, pointerId: 2}));
  body.dispatchEvent(new PointerEvent('pointerup', {bubbles: true, pointerId: 2}));
  check('conteudo nao arrasta', wins[0].style.left === left0);
  // fechar pelo x
  wins[1].querySelector('.win-close').click(); await sleep(30);
  check('x fecha e manda close', $$('.win').length === 1 && calls.some((c) => c[0] === 'close' && c[1] === 8));
  check('sidebar atualiza ao fechar', $$('#sideList button').length === 1);
} catch (e) {
  results.push('ERRO ' + e.stack);
}
const pre = document.createElement('pre');
pre.id = 'results';
pre.textContent = results.join('\n');
document.body.append(pre);
