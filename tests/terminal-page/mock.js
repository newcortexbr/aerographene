// fake TerminalHandler behind chrome.send (same message contract)
window.calls = [];
window.copied = [];
let nextSid = 7;
Object.defineProperty(navigator, 'clipboard', {value: {writeText: (t) => { window.copied.push(t); return Promise.resolve(); }}});
window.chrome = {send(name, args) {
  window.calls.push([name, ...args]);
  const reply = (v) => setTimeout(() => window.cr.webUIResponse(args[0], true, v), 0);
  if (name === 'start') {
    return reply({workspace: new URLSearchParams(location.search).get('new') ? 3 : args[1],
      command: new URLSearchParams(location.search).get('new') ? 'echo oi' : null,
      // C6b: "colado" (paste/drop/paste-and-go) never comes with run: true
      run: !new URLSearchParams(location.search).get('pasted'),
      info: {chromium: '141.0.7390.0', aerographene: '0.3.0', cpu: 'Fake CPU', cores: 8, gpu: 'Fake GPU',
             ram: 16 * 1024 ** 3, disks: [{path: '/', total: 1e11, free: 4e10}, {path: '/home/u', total: 1e11, free: 4e10}]}});
  }
  if (name === 'open') {
    const sid = nextSid++;
    reply(sid);
    setTimeout(() => window.cr.webUIListenerCallback('output', sid, btoa('$ ')), 5);
    return;
  }
  if (name === 'foreground') return reply('bash');
}};
