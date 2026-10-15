const sleep = (ms = 30) => new Promise((r) => setTimeout(r, ms));
const results = [];
function check(name, cond, extra = '') { results.push(`${cond ? 'PASS' : 'FAIL'} ${name} ${cond ? '' : extra}`); }
const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
const mode = new URLSearchParams(location.search).get('t') || 'flow';
const writes = () => window.calls.filter((c) => !/^get/.test(c[0])).map((c) => c[0]);
function key(el, k) { const e = new KeyboardEvent('keydown', {key: k, bubbles: true, cancelable: true}); el.dispatchEvent(e); return e; }
async function ready() { for (let i = 0; i < 100 && !window.setupReady; i++) await sleep(20); }
try {
  await ready();
  check('pagina pronta', window.setupReady === true);
  check('oito passos', $$('.pane').length === 8 && $$('#idx a').length === 8);
  check('titulos dos passos', $$('.pane').map((p) => p.dataset.title).join('|') ===
      '00 hello|01 theme|02 defaults|03 o: notes|04 t: terminal|05 command bar|06 privacy|07 import');
  check('tagline', $('h1').innerText.replace(/\s+/g, ' ').trim() === 'light. fast. pretty.');
  check('wordmark do pacote, sem icone', $('.logo').getAttribute('src') === 'wordmark.svg' && !$('svg') && !$('img[src*="icon"]'));
  check('versao e plataforma', $('#ver').textContent === 'first run · v0.3.0 · linux', $('#ver').textContent);

  // nada de rede nem recurso externo
  const urls = [...$$('link[href]').map((e) => e.getAttribute('href')), ...$$('script[src]').map((e) => e.getAttribute('src')), ...$$('img[src]').map((e) => e.getAttribute('src'))];
  check('recursos so relativos', urls.length >= 3 && urls.every((u) => !/^(https?:)?\/\//.test(u)), urls.join(','));
  const ents = performance.getEntriesByType('resource').map((e) => new URL(e.name).origin);
  check('so a origem da pagina carregou', ents.every((o) => o === location.origin), ents.join(','));

  if (mode === 'skip') {
    $('#skip').click(); await sleep(80);
    check('skip so chama complete', writes().join() === 'complete', writes().join());
    check('skip marca concluido', window.backend.completed === true);
    check('skip nao mexe em tema nem buscador', window.backend.theme === 'default' && window.backend.engine === 'google.com' && window.backend.suggest === true && window.backend.vault === '');
    check('botoes travados apos concluir', $('#skip').disabled && $('#finish').disabled);
  } else if (mode === 'failcomplete') {
    $('#finish').click(); await sleep(80);
    check('complete que falha libera os botoes', !$('#finish').disabled && !$('#skip').disabled);
    check('nada concluido', window.backend.completed === false);
  } else if (mode === 'nodefault') {
    const tog = $('#defBrowser');
    check('sem permissao: chave desabilitada', tog.disabled && tog.getAttribute('aria-checked') === 'false');
    check('sem permissao: texto diz usar o sistema', $('#defBrowserNote').textContent.includes('system settings'), $('#defBrowserNote').textContent);
    check('sem permissao: nenhuma escrita', writes().length === 0);
  } else {
    // 01 tema: so os temas que o backend lista
    const cards = $$('#themes .opt');
    check('cartoes = temas do backend', cards.map((c) => c.dataset.name).join() === 'default,pixelized,papel', cards.map((c) => c.dataset.name).join());
    check('nao ha cartao system', !$$('#themes .opt').some((c) => c.dataset.name === 'system'));
    check('tema ativo marcado', cards[0].classList.contains('on') && cards[0].getAttribute('aria-checked') === 'true');
    check('aviso de reinicio escondido', $('#themeNote').hidden === true);
    cards[1].click(); await sleep(60);
    check('setTheme pixelized', window.calls.some((c) => c[0] === 'setTheme' && c[1] === 'pixelized') && window.backend.theme === 'pixelized');
    check('cartao novo ativo', $$('#themes .opt')[1].classList.contains('on') && !$$('#themes .opt')[0].classList.contains('on'));
    check('aviso de reinicio visivel', $('#themeNote').hidden === false);
    const n = window.calls.filter((c) => c[0] === 'setTheme').length;
    $$('#themes .opt')[1].click(); await sleep(40);
    check('clicar no ativo nao reenvia', window.calls.filter((c) => c[0] === 'setTheme').length === n);

    // 02 buscador
    const sel = $('#engine');
    check('buscadores do backend', [...sel.options].map((o) => o.textContent).join() === 'Google,DuckDuckGo,Bing');
    check('buscador atual', sel.value === 'google.com' && !sel.disabled);
    sel.value = 'duckduckgo.com'; sel.dispatchEvent(new Event('change')); await sleep(60);
    check('setSearchEngine duckduckgo', window.backend.engine === 'duckduckgo.com' && sel.value === 'duckduckgo.com');
    sel.value = 'bing.com'; sel.dispatchEvent(new Event('change')); await sleep(60);
    check('buscador recusado volta ao anterior', sel.value === 'duckduckgo.com' && window.backend.engine === 'duckduckgo.com', sel.value);

    // 02 navegador padrao
    const tog = $('#defBrowser');
    check('padrao: chave habilitada e desligada', !tog.disabled && tog.getAttribute('aria-checked') === 'false');
    tog.click(); await sleep(60);
    check('setDefaultBrowser chamado', window.calls.some((c) => c[0] === 'setDefaultBrowser'));
    check('padrao: ligada e travada', tog.getAttribute('aria-checked') === 'true' && tog.disabled);
    check('padrao: texto', $('#defBrowserNote').textContent.includes('already'), $('#defBrowserNote').textContent);

    // 03 notas
    check('vault vazia', $('#vaultPath').textContent === 'none chosen');
    window.backend.pickResult = null;
    $('#vaultPick').click(); await sleep(60);
    check('pick cancelado mantem', $('#vaultPath').textContent === 'none chosen');
    window.backend.pickResult = {path: '/home/u/notas'};
    $('#vaultPick').click(); await sleep(60);
    check('pasta escolhida aparece', $('#vaultPath').textContent === '/home/u/notas', $('#vaultPath').textContent);

    // 04/05: so informativos
    check('terminal e command bar sem controles', $$('#s04 button, #s04 input, #s04 select, #s05 button, #s05 input, #s05 select').length === 0);

    // 06 privacidade: so o que existe
    check('privacidade: so a chave de sugestoes', $$('#s06 [role=switch]').length === 1 && $$('#s06 input').length === 0);
    check('crash reports sem controle, texto informativo', /Crash reports/.test($('#s06').textContent) && /none are sent/.test($('#s06').textContent));
    check('uBlock so informativo', /uBlock Origin, bundled/.test($('#s06').textContent));
    const sug = $('#suggest');
    check('sugestoes refletem a pref', sug.getAttribute('aria-checked') === 'true' && !sug.disabled);
    sug.click(); await sleep(60);
    check('setSuggest false', window.backend.suggest === false && sug.getAttribute('aria-checked') === 'false');

    // 07 importacao
    $('#import').click(); await sleep(40);
    check('import abre a pagina de importacao', window.calls.some((c) => c[0] === 'openImport'));
    check('import nao conclui', window.backend.completed === false && !window.calls.some((c) => c[0] === 'complete'));

    // teclado: j/k/enter e a rail
    $$('.pane')[0].scrollIntoView(); document.activeElement.blur(); await sleep(50);
    key(document.body, 'j'); await sleep(20);
    check('j vai ao passo 01', $$('#idx a')[1].classList.contains('on') && $$('.pane')[1].classList.contains('on'));
    key(document.body, 'Enter'); await sleep(20);
    check('enter vai ao passo 02', $$('#idx a')[2].classList.contains('on'));
    key(document.body, 'k'); await sleep(20);
    check('k volta ao passo 01', $$('#idx a')[1].classList.contains('on'));
    key($('#engine'), 'j'); await sleep(20);
    check('j dentro do select nao navega', $$('#idx a')[1].classList.contains('on'));
    $$('#idx a')[6].click(); await sleep(20);
    check('rail leva ao passo 06', $$('#idx a')[6].classList.contains('on') && $$('#idx a')[6].getAttribute('aria-current') === 'step');
    $('#start').click(); await sleep(20);
    check('start vai ao passo 01', $$('#idx a')[1].classList.contains('on'));

    // concluir
    $('#finish').click(); await sleep(80);
    check('finish chama complete uma vez', window.calls.filter((c) => c[0] === 'complete').length === 1 && window.backend.completed === true);
    $('#finish').click(); $('#skip').click(); await sleep(30);
    check('concluir nao repete', window.calls.filter((c) => c[0] === 'complete').length === 1);
  }
} catch (e) { results.push('ERRO ' + e.stack); }
const pre = document.createElement('pre'); pre.id = 'results'; pre.textContent = results.join('\n'); document.body.append(pre);
