# spaces (visual e textos)

como o menu do avatar, o seletor (`chrome://profile-picker`) e a criação de um space ficam no visual mono do aerographene, e como o texto "perfil" vira "space". O comportamento é o do Chromium: cada space é um perfil com janela própria ([ADR 0005](../adr/0005-space-e-janela.md)). Esta mudança é só de aparência e de texto.

## o que mudou

- menu do avatar (`profile_menu_view_base.cc`, patch `spaces-menu`): cantos retos; o cabeçalho vai de lado a lado, com um glifo (inicial do nome num quadrado de contorno fino, cor `kColorSysPrimary`) ao lado do nome, e uma linha fina embaixo no lugar do cartão preenchido. Os itens são os mesmos: Passwords and autofill, Customise space, Add space, Open guest window, Manage spaces.
- seletor (patch `spaces-picker`): fundo escuro liso com pontilhado, sem os banners e gradientes do Chromium, cartões retos com borda fina (borda clara no hover), cartão "Add space" tracejado com `+`, título "Which space?". O avatar de cada cartão é o glifo da inicial do nome; a cor do glifo roda por posição do cartão (paleta do mockup).
- criação de space ("novo space", mockup `02-criar-perfil` aprovado): o passo `profile_type_choice` mostra o título "New space", o texto "A space keeps its own history, passwords, pinned tabs and notes folder, and opens in its own window. No account, nothing leaves this machine." e um único botão, "Create space →" (o "não agora" do Chromium, que segue para o nome e a cor). O botão de login fica oculto por CSS: space é perfil local, sem conta; o login não é oferecido nessa tela. A página seguinte (nome, cor, Done/Delete) repete o texto sobre o campo de nome (também fora do modo "refreshed") e o seletor de cores tem o rótulo "Colour of the space". O avatar é o glifo da inicial do nome, na cor do tema; o seletor de avatares origami fica oculto; o cursor do campo usa a cor de acento.
- textos: `build/strings_space.json` lista, por nome IDS, o texto en e pt-BR final (37 mensagens: menu, seletor, criação, remoção, troca). `build/branding_strings.py` troca o corpo da mensagem no `.grd`/`.grdp`, recalcula o id GRIT e grava o texto pt-BR e en-GB no `.xtb`; os outros idiomas só têm o id renomeado e mantêm a tradução antiga ("perfil"). Não se edita `.grd` à mão.

## o que não mudou

- o avatar escolhido continua gravado no perfil (índice do avatar do Chromium); só deixou de ser mostrado nessas telas. Escolher glifo ou cor de glifo por space exigiria guardar a escolha no perfil: não existe ainda.
- o picker usa paleta fixa escura: ele não carrega `chrome://theme/colors.css`, então `theme.json` não o afeta. A página de customização lê os tokens do tema, com o mesmo mono como reserva.
- moldura da janela do picker ("AEROGRAPHENE ×" do mockup), sombra dura do menu, cor de acento por space e o seletor de cores circular do Chromium (componente compartilhado) ficam como no upstream.
- do mockup 02 ficam de fora: indicador de passos "00 space / 01 setup / 02 done" (exigiria strings novas no `.grdp`), escolha de glifo, prévia "work space 02" e a cor tingindo a borda da toolbar (a cor escolhida já muda o tema e o glifo; a borda não foi tocada). O botão final da página de nome continua "Done" (o rótulo é compartilhado com a customização de um space existente).
- Sign in, Google services e avisos de conta ainda dizem "profile" em partes fora dessas telas (configurações, diálogos de conta).

## como mudar um texto

1. ache o nome IDS (ex.: `IDS_PROFILE_MENU_ADD_PROFILE`) em `chrome/app/profiles_strings.grdp` ou `chromium_strings.grd`.
2. acrescente ou edite a entrada em `build/strings_space.json`: `{"en": "...", "pt-BR": "..."}`. Placeholders entram como `<ph name="X"/>` nos dois idiomas e precisam existir na mensagem. Evite apóstrofo (ICU).
3. `cd build && python3 test_branding_strings.py` (os testes de `space_body` e do JSON rodam sempre).

## resumo para agentes

- patches: `aerographene/spaces-menu.patch` (C++, `chrome/browser/ui/views/profiles/profile_menu_view_base.cc`: `SpaceGlyphView`, `SpaceGlyphText`, `set_corner_radius(0)`, cabeçalho horizontal) e `aerographene/spaces-picker.patch` (WebUI: `chrome/browser/resources/signin/profile_picker/*` e `profile_customization/*`: CSS e templates; `spaceGlyph()` em `profile_picker_util.ts`; `getGlyph_()` no app de customização). Nenhum arquivo novo, nenhum `BUILD.gn` tocado. Ao fim de `patches/series`.
- textos: `build/strings_space.json` + `branding_strings.py` (`load_space`, `space_body`, `--space`/`--no-space`); o hash da série em `build/inner.sh` inclui o JSON.
- glifo: `[\p{L}\p{N}]` do nome, maiúscula; sem match, "A". Menu em C++ usa `u_isalnum`/`u_toupper`.
- CSS do patch: aspas simples e sem seletores duplicados (stylelint do Chromium); mescladas as duplicatas antigas de `profile_card`, `profile_card_menu`, `profile_switch` e `profile_picker_main_view`.
- verificado: patch `spaces-picker` reaplica com `-F0` sobre o upstream espelhado (57 hunks conferidos); série aplica com `-F0` numa cópia descartável; `-fsyntax-only` do `.cc` do menu; strings reescritas conferidas nos `.xtb` pt-BR e en-GB num espelho (38 mensagens, 32 nomes). Não verificado: compilação dos recursos WebUI (esbuild/tsc), aparência no navegador (geometria dos cartões, menu), o glifo com nomes não latinos.
