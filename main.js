"use strict";
const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
const $ = (s, r = document) => r.querySelector(s);

/* tiny 3x5 pixel font, used for logo and chart labels */
const F = {
  a:"010101111101101",b:"110101110101110",c:"011100100100011",d:"110101101101110",e:"111100110100111",
  f:"111100110100100",g:"011100101101011",h:"101101111101101",i:"111010010010111",l:"100100100100111",
  m:"101111111101101",n:"110101101101101",o:"010101101101010",p:"110101110100100",r:"110101110101101",
  s:"011100010001110",t:"111010010010010",u:"101101101101111",v:"101101101101010",w:"101101111111101",
  x:"101101010101101",y:"101101010010010",z:"111001010100111",k:"101101110101101",j:"001001001101010",
  q:"010101101110011","0":"111101101101111","1":"010110010010111","2":"110001010100111","3":"110001010001110",
  "4":"101101111001001","5":"111100110001110","6":"011100111101111","7":"111001010010010","8":"111101111101111",
  "9":"111101111001110",".":"000000000000010",",":"000000000010100","-":"000000111000000"," ":"000000000000000",
};
function pxText(ctx, str, x, y, s, color) {
  ctx.fillStyle = color;
  for (const ch of str.toLowerCase()) {
    const g = F[ch] || F[" "];
    for (let i = 0; i < 15; i++) if (g[i] === "1") ctx.fillRect(x + (i % 3) * s, y + Math.floor(i / 3) * s, s, s);
    x += 4 * s;
  }
  return x;
}



/* install tabs */
const U = "https://newcortexbr.github.io/aerographene/<b>install.sh</b>";
const CMDS = {
  curl: `curl -fsSL ${U} | bash`,
  wget: `wget -qO- ${U} | bash`,
  man: 'grab a package from <b>github.com/newcortexbr/aerographene/releases</b>',
};
const setCmd = k => { $("#cmd").innerHTML = CMDS[k]; };
document.querySelectorAll(".tabs button").forEach(b => b.onclick = () => {
  document.querySelectorAll(".tabs button").forEach(o => o.classList.toggle("on", o === b));
  setCmd(b.dataset.k);
});
setCmd("curl");
$("#copy").onclick = () => { navigator.clipboard?.writeText($("#cmd").textContent); $("#copy").textContent = "copied"; setTimeout(() => $("#copy").textContent = "copy", 1200); };

/* themes: themes.json (built by tools/build-gallery.sh) feeds the site picker and the gallery.
   the picker restyles the whole site (data-theme + data-mode on <html>); the gallery only chooses which print is shown. */
const KEY = "aero-theme", root = document.documentElement;
const REAL_PRINTS = true; /* galeria so mostra prints reais do navegador; mockups ficam de fora */
let THEMES = [], G = [], gi = 0, gmode = "dark", userPaused = reduce, hover = false, inView = true, timer;

function applyTheme(id, m, save) {
  const t = THEMES.find(x => x.id === id && x.tokens) || THEMES.find(x => x.id === "default");
  if (!t) return;
  m = t.modes.includes(m) ? m : t.modes[0];
  root.dataset.theme = t.id; root.dataset.mode = m;
  if (save) try { localStorage.setItem(KEY, t.id + "|" + m); } catch (e) {}
  const bg = getComputedStyle(root).getPropertyValue("--bg").trim();
  $('meta[name="theme-color"]').content = bg;
  renderPicker(); dispatchEvent(new Event("themechange"));
}

/* site picker: radiogroup (arrows move + select) and a dark/light switch */
function renderPicker() {
  const box = $("#pk"), cur = root.dataset.theme, m = root.dataset.mode;
  const list = THEMES.filter(t => t.tokens);
  if (!box.children.length) list.forEach(t => {
    const b = document.createElement("button");
    b.type = "button"; b.setAttribute("role", "radio"); b.dataset.id = t.id;
    b.title = t.name;
    b.innerHTML = '<i class="sw"><u></u><u></u><u></u></i><span></span>';
    b.children[1].textContent = t.name;
    b.onclick = () => applyTheme(t.id, root.dataset.mode, true);
    box.append(b);
  });
  list.forEach((t, i) => {
    const b = box.children[i], k = t.tokens[m] || t.tokens[t.modes[0]];
    b.setAttribute("aria-checked", t.id === cur); b.tabIndex = t.id === cur ? 0 : -1;
    const u = b.querySelectorAll("u"); u[0].style.background = k.bg; u[1].style.background = k.text; u[2].style.background = k.accent;
    b.querySelector(".sw").style.borderColor = k.edge;
  });
  const t = list.find(x => x.id === cur);
  document.querySelectorAll("#pkmode button").forEach(b => {
    const ok = t.modes.includes(b.dataset.m);
    b.setAttribute("aria-pressed", b.dataset.m === m); b.disabled = !ok;
    b.title = ok ? "" : t.name + " has no " + b.dataset.m + " mode";
  });
}
$("#pk").addEventListener("keydown", e => {
  const k = { ArrowDown: 1, ArrowRight: 1, ArrowUp: -1, ArrowLeft: -1 }[e.key];
  if (!k) return;
  e.preventDefault();
  const bs = [...$("#pk").children], i = bs.findIndex(b => b.getAttribute("aria-checked") === "true"), n = bs[(i + k + bs.length) % bs.length];
  n.click(); n.focus();
});
document.querySelectorAll("#pkmode button").forEach(b => b.onclick = () => applyTheme(root.dataset.theme, b.dataset.m, true));

/* gallery: folder-tab stack of browser prints. autoplay only changes the selected print, never the site theme */
function galSelect(i, focus) {
  gi = (i + G.length) % G.length;
  const t = G[gi];
  [...$("#galtabs").children].forEach((b, j) => { b.setAttribute("aria-selected", j === gi); b.tabIndex = j === gi ? 0 : -1; if (j === gi && focus) b.focus(); });
  const m = t.print[gmode] ? gmode : (Object.keys(t.print)[0] || t.modes[0]);
  const img = $("#galimg"), soon = $("#galsoon");
  $("#galaddr").textContent = "aerographene://theme/" + t.id;
  $("#galcap").textContent = t.note || "";
  const p = REAL_PRINTS ? t.print[m] : null;
  img.hidden = !p; soon.hidden = !!p;
  if (p) { img.src = p; img.alt = t.name + " theme, " + m + " mode: mockup screenshot of the browser"; }
  $("#galpanel").setAttribute("aria-labelledby", "gt-" + t.id);
  document.querySelectorAll("#galmode button").forEach(b => { b.setAttribute("aria-pressed", b.dataset.m === m); b.disabled = !t.print[b.dataset.m]; });
  const nx = G[(gi + 1) % G.length].print; const f = nx[gmode] || nx[Object.keys(nx)[0]]; if (f) new Image().src = f;
}
function galNext() { let n = 0, i = gi; do { i = (i + 1) % G.length; n++; } while (!Object.keys(G[i].print).length && n < G.length); galSelect(i); }
function galPlay() {
  clearInterval(timer);
  const on = !userPaused && !hover && inView && !document.hidden;
  if (on) timer = setInterval(galNext, 5500);
  const b = $("#galpause"); b.setAttribute("aria-pressed", userPaused); b.textContent = userPaused ? "▶ play" : "❚❚ pause";
  b.setAttribute("aria-label", userPaused ? "start gallery autoplay" : "pause gallery autoplay");
}
function buildGallery() {
  G = THEMES;
  const tabs = $("#galtabs");
  G.forEach((t, i) => {
    const b = document.createElement("button");
    b.type = "button"; b.role = "tab"; b.id = "gt-" + t.id; b.setAttribute("aria-controls", "galpanel");
    b.style.setProperty("--i", i); b.textContent = t.name;
    b.onclick = () => galSelect(i);
    tabs.append(b);
  });
  tabs.addEventListener("keydown", e => {
    const k = { ArrowRight: 1, ArrowLeft: -1 }[e.key];
    if (k) { e.preventDefault(); galSelect(gi + k, true); }
    else if (e.key === "Home") { e.preventDefault(); galSelect(0, true); }
    else if (e.key === "End") { e.preventDefault(); galSelect(G.length - 1, true); }
  });
  $("#galprev").onclick = () => galSelect(gi - 1);
  $("#galnext").onclick = () => galSelect(gi + 1);
  $("#galpause").onclick = () => { userPaused = !userPaused; galPlay(); };
  document.querySelectorAll("#galmode button").forEach(b => b.onclick = () => { gmode = b.dataset.m; galSelect(gi); });
  const g = $("#gal");
  g.addEventListener("mouseenter", () => { hover = true; galPlay(); });
  g.addEventListener("mouseleave", () => { hover = g.matches(":focus-within"); galPlay(); });
  g.addEventListener("focusin", () => { hover = true; galPlay(); });
  g.addEventListener("focusout", () => { hover = g.matches(":hover"); galPlay(); });
  new IntersectionObserver(es => { inView = es[0].isIntersecting; galPlay(); }).observe(g);
  document.addEventListener("visibilitychange", galPlay);
  galSelect(0); galPlay();
}
fetch("themes.json").then(r => r.json()).then(d => {
  THEMES = d.themes;
  applyTheme(root.dataset.theme, root.dataset.mode, false);
  buildGallery();
}).catch(() => { $("#galcap").textContent = "themes could not be loaded."; });


/* t: workspace — two terminals, zoom in/out, drag across and back */
(() => {
  const ws = $("#ws"), grid = $("#wsgrid"), A = $("#tA"), B = $("#tB"), cur = $("#tcur"), side = $("#wside");
  const W = () => ws.clientWidth, H = () => ws.clientHeight;
  let scale = 1;
  const place = (el, x, y) => { el.style.left = x + "px"; el.style.top = y + "px"; };
  const zoom = s => { scale = s; grid.style.transform = `scale(${s})`; };
  // screen position of a grid point (grid scales around its centre)
  const scr = (x, y) => [W() / 2 + (x - W() / 2) * scale, H() / 2 + (y - H() / 2) * scale];
  const mv = (x, y) => { const [sx, sy] = scr(x, y); cur.style.transform = `translate(${sx}px,${sy}px)`; };
  const mvs = (x, y) => { cur.style.transform = `translate(${x}px,${y}px)`; }; // screen coords (corners)
  const left = () => [48, 44], right = () => [W() - 304, H() - 100];
  const steps = [
    () => { zoom(1); A.style.transition = "none"; place(A, ...left()); place(B, W() - 304, 50); mv(W() / 2, H() - 30); requestAnimationFrame(() => A.style.transition = ""); },
    () => { zoom(1.35); mv(W() / 2, H() / 2); },
    () => { zoom(.75); mv(...left().map((v, i) => v + (i ? 6 : 60))); },
    () => { A.classList.add("drag"); },
    () => { place(A, ...right()); mv(right()[0] + 60, right()[1] + 6); },
    () => { A.classList.remove("drag"); zoom(.6); },
    () => { mv(right()[0] + 60, right()[1] + 6); A.classList.add("drag"); },
    () => { place(A, ...left()); mv(left()[0] + 60, left()[1] + 6); },
    () => { A.classList.remove("drag"); zoom(1); mvs(20, 26); },
    () => { side.hidden = false; },
    () => { side.hidden = true; zoom(1.25); mv(W() / 2 + 30, H() / 2 + 20); },
  ];
  const wait = [400, 900, 1000, 300, 900, 900, 400, 900, 900, 1100, 1300];
  let i = 0;
  const run = () => { steps[i](); setTimeout(run, wait[i]); i = (i + 1) % steps.length; };
  if (reduce) { place(A, ...left()); place(B, W() - 304, 50); } else run();
})();

/* o: obsidian-style live preview — markdown typed raw, rendered when the line is done */
(() => {
  const ed = $("#edbody");
  const doc = [
    "## browser",
    "- [ ] port to **windows 11**",
    "- notes read from my [[vault]]",
    "- pixel charts, *thin* type",
    "`t:` next to `o:`",
  ];
  const esc = s => s.replace(/&/g, "&amp;").replace(/</g, "&lt;");
  const inline = s => esc(s)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/`(.+?)`/g, "<code>$1</code>")
    .replace(/\[\[(.+?)\]\]/g, '<span class="wl">$1</span>');
  const render = l => {
    if (l.startsWith("## ")) return `<h5>${inline(l.slice(3))}</h5>`;
    if (l.startsWith("# ")) return `<h4>${inline(l.slice(2))}</h4>`;
    if (l.startsWith("- [ ] ")) return `<div><span class="cb"></span>${inline(l.slice(6))}</div>`;
    if (l.startsWith("- ")) return `<div class="bul">${inline(l.slice(2))}</div>`;
    return `<div>${inline(l)}</div>`;
  };
  const raw = l => `<span class="raw">${esc(l).replace(/(^#+ |^- \[ \] |^- |\*\*|\*|`|\[\[|\]\])/g, '<span class="mk">$1</span>')}</span><span class="blink">▌</span>`;
  const words = s => s.split(/\s+/).filter(Boolean).length;
  const stats = cur => {
    const t = done.concat(cur != null && cur !== "" ? [cur] : []);
    const full = t.join("\n");
    $("#sbw").textContent = words(full) + " palavras";
    $("#sbc").textContent = full.length + " caracteres";
    const last = cur != null ? cur : (done[done.length - 1] || "");
    $("#sbp").textContent = "L" + Math.max(1, t.length || 1) + ":C" + (last.length + 1);
  };
  let li = 0, ci = 0, done = [];
  const paint = cur => {
    stats(cur); ed.innerHTML = done.map(l => `<div class="ln">${render(l)}</div>`).join("") + (cur != null ? `<div class="ln">${raw(cur)}</div>` : ""); };
  function step() {
    if (li >= doc.length) { setTimeout(() => { done = []; li = 0; ci = 0; step(); }, 2200); return; }
    const l = doc[li];
    ci++;
    if (ci > l.length) { done.push(l); li++; ci = 0; paint(""); return setTimeout(step, 380); }
    paint(l.slice(0, ci));
    setTimeout(step, 45 + Math.random() * 70);
  }
  if (reduce) { done = doc; paint(); } else step();
})();

/* rail: highlight the pane in view, j/k to move */
(() => {
  const panes = [...document.querySelectorAll(".pane")], links = [...document.querySelectorAll(".idx a")];
  const mark = id => {
    links.forEach(a => a.classList.toggle("on", a.getAttribute("href") === "#" + id));
    panes.forEach(p => p.classList.toggle("focus", p.id === id));
  };
  const io2 = new IntersectionObserver(es => es.forEach(e => e.isIntersecting && mark(e.target.id)), { rootMargin: "-45% 0px -50% 0px" });
  panes.forEach(p => io2.observe(p));
  addEventListener("keydown", e => {
    if (e.target.closest("input,textarea") || !"jk".includes(e.key)) return;
    const i = links.findIndex(a => a.classList.contains("on"));
    const n = links[Math.max(0, Math.min(links.length - 1, i + (e.key === "j" ? 1 : -1)))];
    document.querySelector(n.getAttribute("href")).scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "center" });
  });
  mark("top");
})();

/* pixel bar charts, data from docs/BASELINE.md (README charts) */
const DATA = {
  startup: [["thorium", 435.9], ["aerographene", 476.4], ["helium", 484.9], ["chrome", 496.3], ["ungoogled", 523.4]],
  tabs: [["thorium", 837.2], ["aerographene", 875.2], ["helium", 898.0], ["chrome", 912.5], ["ungoogled", 1044]],
  pss: [["thorium", 627.5], ["ungoogled", 634.6], ["aerographene", 635.3], ["helium", 662.0], ["chrome", 686.7]],
};
const charts = document.querySelectorAll("canvas.px");
const drawn = new Set();
const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { drawn.add(e.target); draw(e.target); io.unobserve(e.target); } }));
addEventListener("themechange", () => drawn.forEach(c => draw(c, true)));
charts.forEach(c => io.observe(c));
function draw(c, instant) {
  const cs = getComputedStyle(document.documentElement), col = n => cs.getPropertyValue(n).trim();
  const cText = col("--text"), cMuted = col("--muted"), cAcc = col("--accent"), cA = col("--sel"), cB = col("--line");
  const x = c.getContext("2d"), d = DATA[c.dataset.set], max = Math.max(...d.map(r => r[1])), min = Math.min(...d.map(r => r[1])) * .8;
  const S = 3, cell = 4, rowH = 28, x0 = 0, bx = 0, maxCells = Math.floor((c.width - 4) / cell);
  let f = instant ? 1 : 0;
  const frame = () => {
    f = Math.min(1, f + (reduce ? 1 : .05));
    x.clearRect(0, 0, c.width, c.height);
    d.forEach(([n, v], r) => {
      const y = r * rowH, me = n === "aerographene";
      pxText(x, n, x0, y, 2, me ? cText : cMuted);
      const end = pxText(x, "", 0, 0, 1, "#0000");
      const vs = String(v).replace(/\.0$/, "");
      pxText(x, vs, c.width - vs.length * 8, y, 2, me ? cAcc : cMuted);
      const cells = Math.round(maxCells * ((v - min) / (max - min)) * f);
      for (let k = 0; k < cells; k++) {
        x.fillStyle = me ? cAcc : (k % 2 ? cA : cB);
        x.fillRect(bx + k * cell, y + 14, cell - 1, 9);
      }
    });
    if (f < 1) requestAnimationFrame(frame);
  };
  frame();
}

$("#copy2").onclick = () => {
  navigator.clipboard?.writeText("curl -fsSL https://newcortexbr.github.io/aerographene/install.sh | bash");
  const b = $("#copy2"); b.textContent = "✓ copied"; setTimeout(() => b.textContent = "$ copy install command", 1400);
};
