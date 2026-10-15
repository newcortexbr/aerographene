// in-memory vault behind chrome.send, same contract as NotesHandler
window.calls = [];
const files = {'a.md': {t: '# Titulo\n\ntexto *forte* aqui\n\n- um\n- dois\n\n```js\nlet x = 1;\n```\nfim', m: 1000}, 'sub/b.md': {t: 'b', m: 2000}};
window.files = files;
window.chrome = {send(name, args) {
  const [id, ...a] = args;
  window.calls.push([name, ...a]);
  const ok = (v) => setTimeout(() => window.cr.webUIResponse(id, true, v), 0);
  const bad = (v) => setTimeout(() => window.cr.webUIResponse(id, false, v), 0);
  const res = (status, mtime = 0) => ok({status, mtime});
  if (name === 'getVault') return ok({path: '/home/u/MeuCofre', name: 'MeuCofre'});
  if (name === 'listDir') {
    const p = a[0] ? a[0] + '/' : '';
    const out = new Map();
    for (const f of Object.keys(files)) {
      if (!f.startsWith(p)) continue;
      const rest = f.slice(p.length);
      const i = rest.indexOf('/');
      if (i < 0) out.set(f, {path: f, dir: false, size: 1});
      else out.set(p + rest.slice(0, i), {path: p + rest.slice(0, i), dir: true, size: 0});
    }
    return ok([...out.values()]);
  }
  if (name === 'readNote') return files[a[0]] ? ok({text: files[a[0]].t, mtime: files[a[0]].m}) : bad('notFound');
  if (name === 'writeNote') {
    const f = files[a[0]];
    if (!f) return res('notFound');
    if (a[2] !== null && a[2] !== f.m) return res('conflict', f.m);
    f.t = a[1]; f.m += 10; return res('ok', f.m);
  }
  if (name === 'createNote') {
    if (files[a[0]]) return res('exists');
    files[a[0]] = {t: a[1], m: 5000}; return res('ok', 5000);
  }
  if (name === 'renameNote') {
    if (!files[a[0]]) return res('notFound');
    if (files[a[1]]) return res('exists');
    files[a[1]] = files[a[0]]; delete files[a[0]]; return res('ok', files[a[1]].m);
  }
  if (name === 'deleteNote') { if (!files[a[0]]) return res('notFound'); delete files[a[0]]; return res('ok'); }
  if (name === 'watchVault') return ok(window.watchOk !== false);
  if (name === 'searchVault') {
    const q = a[0].toLowerCase();
    const hits = [];
    for (const [p, f] of Object.entries(files)) {
      const nm = p.toLowerCase().includes(q);
      const at = f.t.toLowerCase().indexOf(q);
      if (nm || at >= 0) hits.push({path: p, nameMatch: nm, snippet: at >= 0 ? f.t.split('\n').find((l) => l.toLowerCase().includes(q)) : ''});
    }
    return ok({hits, truncated: false});
  }
  if (name === 'readImage') {
    const f = (window.images || {})[a[1] + a[0]] || (window.images || {})[a[0]];
    return f ? ok({mime: 'image/png', data: f}) : bad('notFound');
  }
  bad('unknown');
}};

// 1x1 png
window.images = {'pic.png': 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGNgYGD4DwABBAEAwS2OUAAAAABJRU5ErkJggg=='};
window.fire = (name, ...args) => window.cr.webUIListenerCallback(name, ...args);
