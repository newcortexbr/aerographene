// Records what the page writes to each xterm.js Terminal (same module
// instance as terminal.js, loaded before it), so the test reads the whole
// buffer and not only the rendered viewport.
import {Terminal} from './xterm.mjs';
window.termLog = new Map();
const write = Terminal.prototype.write;
Terminal.prototype.write = function(data, cb) {
  const s = typeof data === 'string' ? data : new TextDecoder().decode(data);
  window.termLog.set(this, (window.termLog.get(this) || '') + s);
  return write.call(this, data, cb);
};
