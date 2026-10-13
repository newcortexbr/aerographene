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

/* theme carousel: add a theme = add one entry */
const THEMES = [
  { id: "default", cls: "" },
  { id: "pixelized", cls: "pixelized" },
];
const browser = $("#browser"), segs = $("#segs");
let cur = 0, t0 = performance.now(), paused = false;
const DUR = 1000;
THEMES.forEach((t, i) => {
  const s = document.createElement("div");
  s.className = "seg"; s.title = t.id; s.innerHTML = "<i></i>";
  s.onclick = () => go(i);
  segs.append(s);
});
function go(i) {
  cur = (i + THEMES.length) % THEMES.length; t0 = performance.now();
  THEMES.forEach(t => t.cls && browser.classList.remove(t.cls));
  THEMES[cur].cls && browser.classList.add(THEMES[cur].cls);
  $("#tname").textContent = THEMES[cur].id;
}
browser.parentElement.addEventListener("mouseenter", () => paused = true);
browser.parentElement.addEventListener("mouseleave", () => { paused = false; t0 = performance.now(); });
function tick(now) {
  if (paused) t0 = now - (Number(segs.dataset.p) || 0) * DUR;
  const p = Math.min(1, (now - t0) / DUR);
  segs.dataset.p = p;
  [...segs.children].forEach((s, i) => s.firstChild.style.width = (i < cur ? 100 : i === cur ? p * 100 : 0) + "%");
  if (p >= 1 && !reduce && !window.NOROT) go(cur + 1);
  requestAnimationFrame(tick);
}
go(0); requestAnimationFrame(tick);

/* pixelized: 1-bit bayer 8x8 dither (pixel 2), used for the wallpaper and the active-tab ramp */
const BAYER = (() => { const m = [[0]]; let M = m; for (let n = 1; n < 8; n *= 2) { const R = []; for (let j = 0; j < 2 * n; j++) { R[j] = []; for (let i = 0; i < 2 * n; i++) R[j][i] = 4 * M[j % n][i % n] + [0, 2, 3, 1][(j >= n) * 2 + (i >= n)]; } M = R; } return M; })();
function dither(c, f) {
  const px = c.dataset.px ? +c.dataset.px : 1, w = c.width = Math.max(1, Math.ceil(c.clientWidth / px)), h = c.height = Math.max(1, Math.ceil(c.clientHeight / px));
  const x = c.getContext("2d"), im = x.createImageData(w, h);
  for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) {
    const on = f(i / w, j / h) * 64 > BAYER[j % 8][i % 8] + .5, k = (j * w + i) * 4;
    im.data[k] = im.data[k + 1] = im.data[k + 2] = on ? 240 : 0; im.data[k + 3] = 255;
  }
  x.putImageData(im, 0, 0);
}
(() => {
  const page = $("#dither"), ramp = $("#ramp");
  const g = (u, v, cx, cy, rx, ry) => Math.exp(-(((u - cx) / rx) ** 2 + ((v - cy) / ry) ** 2));
  const draw = () => {
    dither(page, (u, v) => {
      // mid-grey field, bright textured core top-right, dark wedge under the search box
      const core = g(u, v, .72, .3, .16, .26), halo = g(u, v, .7, .35, .4, .55);
      const field = .2 + .1 * Math.sin(u * 9) * Math.sin(v * 7);
      const edge = 1 - .45 * Math.max(0, (u - .9) / .1);
      const wedge = Math.max(0, 1 - Math.abs(u - .46) / (.05 + .1 * Math.max(0, v - .6))) * (v > .62 ? 1 : 0);
      return Math.min(.85, (field + .3 * halo + .55 * core) * edge) * (1 - .95 * wedge);
    });
    dither(ramp, u => u);   // black → white, left to right, like the real active tab
  };
  draw(); addEventListener("resize", draw);
  new MutationObserver(draw).observe($("#browser"), { attributes: true, attributeFilter: ["class"] });
})();

/* cursor wandering over hot items */
const cursor = $("#cursor"), hots = [...browser.querySelectorAll(".hot")];
let last;
function wander() {
  const b = browser.getBoundingClientRect();
  const h = hots[Math.floor(Math.random() * hots.length)];
  const r = h.getBoundingClientRect();
  const x = r.left - b.left + Math.random() * r.width * .8 + 4, y = r.top - b.top + Math.random() * r.height * .6 + 2;
  cursor.style.transform = `translate(${x}px,${y}px)`;
  setTimeout(() => { last?.classList.remove("hover"); h.classList.add("hover"); last = h; }, 260);
  setTimeout(wander, 380 + Math.random() * 520);
}
if (!reduce) wander();

/* t: workspace — two terminals, zoom in/out, drag across and back */
(() => {
  const ws = $("#ws"), grid = $("#wsgrid"), A = $("#tA"), B = $("#tB"), cur = $("#tcur"), z = $("#zoom");
  const W = () => ws.clientWidth, H = () => ws.clientHeight;
  let scale = 1;
  const place = (el, x, y) => { el.style.left = x + "px"; el.style.top = y + "px"; };
  const zoom = s => { scale = s; grid.style.transform = `scale(${s})`; z.textContent = Math.round(s * 100) + "%"; };
  // screen position of a grid point (grid scales around its centre)
  const scr = (x, y) => [W() / 2 + (x - W() / 2) * scale, H() / 2 + (y - H() / 2) * scale];
  const mv = (x, y) => { const [sx, sy] = scr(x, y); cur.style.transform = `translate(${sx}px,${sy}px)`; };
  const left = () => [24, 40], right = () => [W() - 214, H() - 130];
  const steps = [
    () => { zoom(1); A.style.transition = "none"; place(A, ...left()); place(B, W() - 214, 30); mv(W() / 2, H() - 30); requestAnimationFrame(() => A.style.transition = ""); },
    () => { zoom(1.35); mv(W() / 2, H() / 2); },
    () => { zoom(.75); mv(...left().map((v, i) => v + (i ? 6 : 60))); },
    () => { A.classList.add("drag"); },
    () => { place(A, ...right()); mv(right()[0] + 60, right()[1] + 6); },
    () => { A.classList.remove("drag"); zoom(.6); },
    () => { mv(right()[0] + 60, right()[1] + 6); A.classList.add("drag"); },
    () => { place(A, ...left()); mv(left()[0] + 60, left()[1] + 6); },
    () => { A.classList.remove("drag"); zoom(1.25); mv(W() / 2 + 30, H() / 2 + 20); },
  ];
  const wait = [400, 900, 1000, 300, 900, 900, 400, 900, 1300];
  let i = 0;
  const run = () => { steps[i](); setTimeout(run, wait[i]); i = (i + 1) % steps.length; };
  if (reduce) { place(A, ...left()); place(B, W() - 214, 30); } else run();
})();

/* o: obsidian-style live preview — markdown typed raw, rendered when the line is done */
(() => {
  const ed = $("#editor");
  const doc = [
    "# ideas",
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
  let li = 0, ci = 0, done = [];
  const paint = cur => { ed.innerHTML = done.map(l => `<div class="ln">${render(l)}</div>`).join("") + (cur != null ? `<div class="ln">${raw(cur)}</div>` : ""); };
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
const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { draw(e.target); io.unobserve(e.target); } }));
charts.forEach(c => io.observe(c));
function draw(c) {
  const x = c.getContext("2d"), d = DATA[c.dataset.set], max = Math.max(...d.map(r => r[1])), min = Math.min(...d.map(r => r[1])) * .8;
  const S = 3, cell = 4, rowH = 28, x0 = 0, bx = 0, maxCells = Math.floor((c.width - 4) / cell);
  let f = 0;
  const frame = () => {
    f = Math.min(1, f + (reduce ? 1 : .05));
    x.clearRect(0, 0, c.width, c.height);
    d.forEach(([n, v], r) => {
      const y = r * rowH, me = n === "aerographene";
      pxText(x, n, x0, y, 2, me ? "#e6edf8" : "#5e6b82");
      const end = pxText(x, "", 0, 0, 1, "#0000");
      const vs = String(v).replace(/\.0$/, "");
      pxText(x, vs, c.width - vs.length * 8, y, 2, me ? "#6cb6ff" : "#5e6b82");
      const cells = Math.round(maxCells * ((v - min) / (max - min)) * f);
      for (let k = 0; k < cells; k++) {
        x.fillStyle = me ? "#6cb6ff" : (k % 2 ? "#2a3345" : "#3a4559");
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

/* layout switch + folder drawer */
document.querySelectorAll(".lay button").forEach(b => b.onclick = () => {
  document.querySelectorAll(".lay button").forEach(o => o.classList.toggle("on", o === b));
  $("#browser").classList.toggle("top", b.dataset.l === "top");
  dispatchEvent(new Event("resize"));
});
if (!reduce) setInterval(() => $("#browser .folder").classList.toggle("open"), 2600);
