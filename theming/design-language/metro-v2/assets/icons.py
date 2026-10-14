# conjunto de ícones metro-v2: grade 20x20, traço 1,3px, cantos retos, sem arredondar.
# cor via currentColor; preenchimento só onde o glifo é sólido (marcado com fill="currentColor").
N = 'fill="none"'
ICONS = {
 # chrome da janela
 'side': f'<rect x="2.5" y="3.5" width="15" height="13" {N}/><path d="M7.5 3.5v13"/>',
 'back': f'<path d="M17 10H3M9 4l-6 6 6 6" {N}/>',
 'fwd': f'<path d="M3 10h14M11 4l6 6-6 6" {N}/>',
 'reload': f'<path d="M16 10a6 6 0 1 1-2-4.5M16 3v4h-4" {N}/>',
 'home': f'<path d="M3 10l7-6.5 7 6.5M5 8.5V17h10V8.5M8.5 17v-5h3v5" {N}/>',
 'stop': f'<path d="M5 5l10 10M15 5L5 15"/>',
 'min': '<path d="M5 10h10"/>',
 'max': f'<rect x="5.5" y="5.5" width="9" height="9" {N}/>',
 'restore': f'<path d="M7.5 7.5v-3h8v8h-3" {N}/><rect x="4.5" y="7.5" width="8" height="8" {N}/>',
 'close': '<path d="M5 5l10 10M15 5L5 15"/>',
 # omnibox e barra
 'search': f'<circle cx="8.5" cy="8.5" r="5" {N}/><path d="M12.2 12.2L17 17"/>',
 'tune': f'<path d="M3 6h9M15 6h2M3 14h2M8 14h9" {N}/><rect x="12" y="4" width="3" height="4" {N}/><rect x="5" y="12" width="3" height="4" {N}/>',
 'link': f'<path d="M8 6H5a4 4 0 0 0 0 8h3M12 6h3a4 4 0 0 1 0 8h-3M7 10h6" {N}/>',
 'lock': f'<rect x="4.5" y="9" width="11" height="8" {N}/><path d="M7 9V6.5a3 3 0 0 1 6 0V9" {N}/>',
 'star': f'<path d="M10 2.5l2.3 4.9 5.2.7-3.8 3.7.9 5.2L10 14.4l-4.6 2.6.9-5.2L2.5 8.1l5.2-.7z" {N}/>',
 'star-fill': '<path d="M10 2.5l2.3 4.9 5.2.7-3.8 3.7.9 5.2L10 14.4l-4.6 2.6.9-5.2L2.5 8.1l5.2-.7z"/>',
 'shield': f'<path d="M10 2l7 3v5c0 4-3 7-7 8-4-1-7-4-7-8V5z" {N}/>',
 'user': f'<circle cx="10" cy="7" r="3.5" {N}/><path d="M3 18c1-4 4-5.5 7-5.5s6 1.5 7 5.5" {N}/>',
 'more': '<circle cx="10" cy="4" r="1"/><circle cx="10" cy="10" r="1"/><circle cx="10" cy="16" r="1"/>',
 'more-h': '<circle cx="4" cy="10" r="1"/><circle cx="10" cy="10" r="1"/><circle cx="16" cy="10" r="1"/>',
 'down': f'<path d="M10 3v10M5 9l5 5 5-5M4 17h12" {N}/>',
 'ext': f'<path d="M4 7h3V5a2 2 0 0 1 4 0v2h3v3h-2a2 2 0 0 0 0 4h2v3H4z" {N}/>',
 # abas e navegação
 'plus': '<path d="M10 4v12M4 10h12"/>',
 'chevron-down': f'<path d="M5 8l5 5 5-5" {N}/>',
 'chevron-right': f'<path d="M8 5l5 5-5 5" {N}/>',
 'pin': f'<path d="M7 3h6M8 3v6l-3 3h10l-3-3V3M10 12v5" {N}/>',
 'speaker': f'<path d="M3 8h3l4-3.5v11L6 12H3zM13 7.5a3.5 3.5 0 0 1 0 5" {N}/>',
 'mute': f'<path d="M3 8h3l4-3.5v11L6 12H3zM13 8l4 4M17 8l-4 4" {N}/>',
 'tabs': f'<rect x="2.5" y="6.5" width="11" height="10" {N}/><path d="M6.5 6.5v-3h11v10h-4" {N}/>',
 'folder': f'<path d="M2.5 5h5l1.5 2h8.5v9.5h-15z" {N}/>',
 'history': f'<path d="M3.5 10a6.5 6.5 0 1 0 2-4.7M3 3v3.5h3.5M10 6.5V10l2.5 2" {N}/>',
 'bookmark': f'<path d="M5.5 2.5h9v15L10 13.5l-4.5 4z" {N}/>',
 'print': f'<path d="M5.5 7V2.5h9V7M5.5 14h-3V7h15v7h-3M5.5 11.5h9v6h-9z" {N}/>',
 'zoom': f'<circle cx="8.5" cy="8.5" r="5" {N}/><path d="M12.2 12.2L17 17M6 8.5h5M8.5 6v5"/>',
 'incognito': f'<path d="M3 11h14M5.5 11l1-6h7l1 6" {N}/><circle cx="6.5" cy="14.5" r="2" {N}/><circle cx="13.5" cy="14.5" r="2" {N}/>',
 # conteúdo / space
 'globe': f'<circle cx="10" cy="10" r="7" {N}/><path d="M3 10h14M10 3c3 3 3 11 0 14M10 3c-3 3-3 11 0 14" {N}/>',
 'doc': f'<path d="M5 2.5h7l3 3v12H5z" {N}/><path d="M7.5 9h5M7.5 12h5"/>',
 'term': f'<rect x="2.5" y="4.5" width="15" height="11" {N}/><path d="M5.5 8l2.5 2-2.5 2M10 12h4" {N}/>',
 'chat': f'<path d="M3 4h14v9H9l-4 3v-3H3z" {N}/>',
 'gear': f'<circle cx="10" cy="10" r="2.5" {N}/><circle cx="10" cy="10" r="6" {N} stroke-dasharray="3 2"/>',
 'edit': f'<path d="M3 17l1-4L14 3l3 3L7 16z M12 5l3 3" {N}/>',
 'trash': f'<path d="M3.5 5.5h13M8 5.5v-2h4v2M5 5.5l1 12h8l1-12M8.5 8.5v6M11.5 8.5v6" {N}/>',
 'check': f'<path d="M4 10.5l4 4L16 6" {N}/>',
 'info': f'<circle cx="10" cy="10" r="7" {N}/><path d="M10 9v5M10 6v1.5"/>',
 'warn': f'<path d="M10 3L18 17H2z" {N}/><path d="M10 8v4M10 14v1.5"/>',
}
def svg(name, color='currentColor', size=20, sw=1.3):
  return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 20 20" '
          f'stroke="{color}" fill="{color}" stroke-width="{sw}">{ICONS[name]}</svg>')
