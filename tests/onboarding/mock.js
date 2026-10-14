// Backend falso de chrome://setup atrás de chrome.send, mesmo contrato do
// SetupHandler (aero_setup/setup_handler.h). O estado fica em memória; cada
// chamada é registrada em window.calls. Opções pela query da página:
//   ?failcomplete=1  complete() rejeita
//   ?nodefault=1     o navegador não pode ser definido como padrão aqui
window.calls = [];
const q = new URLSearchParams(location.search);
window.backend = {
  themes: [
    {name: 'default', builtin: true, dark: true},
    {name: 'pixelized', builtin: true, dark: true},
    {name: 'papel', builtin: false, dark: false},
  ],
  theme: 'default',
  engines: [
    {keyword: 'google.com', name: 'Google'},
    {keyword: 'duckduckgo.com', name: 'DuckDuckGo'},
    {keyword: 'bing.com', name: 'Bing'},
  ],
  engine: 'google.com',
  suggest: true,
  vault: '',
  pickResult: {path: '/home/u/notas'},
  isDefault: false,
  canSet: q.get('nodefault') !== '1',
  completed: false,
};
const b = window.backend;
window.chrome = {send(name, args) {
  const [id, ...a] = args;
  window.calls.push([name, ...a]);
  const ok = (v) => setTimeout(() => window.cr.webUIResponse(id, true, v), 0);
  const bad = (v) => setTimeout(() => window.cr.webUIResponse(id, false, v), 0);
  switch (name) {
    case 'getInfo': return ok({version: '0.3.0', platform: 'linux', vault: {path: b.vault}});
    case 'getThemes': return ok({themes: b.themes, active: b.theme});
    case 'setTheme':
      if (!b.themes.some((t) => t.name === a[0])) return ok(false);
      b.theme = a[0]; return ok(true);
    case 'getSearch': return ok({engines: b.engines, current: b.engine, suggest: b.suggest});
    case 'setSearchEngine':
      if (a[0] === 'bing.com' || !b.engines.some((e) => e.keyword === a[0])) return ok(false);
      b.engine = a[0]; return ok(true);
    case 'setSuggest': b.suggest = a[0]; return ok(true);
    case 'pickVault':
      if (b.pickResult) b.vault = b.pickResult.path;
      return ok(b.pickResult ? {path: b.vault} : null);
    case 'getDefaultBrowser': return ok({canSet: b.canSet, isDefault: b.isDefault});
    case 'setDefaultBrowser':
      if (b.canSet) b.isDefault = true;
      return ok({canSet: b.canSet, isDefault: b.isDefault});
    case 'openImport': return ok(true);
    case 'complete':
      if (q.get('failcomplete') === '1') return bad('boom');
      b.completed = true; return ok(true);
  }
  bad('unknown');
}};
