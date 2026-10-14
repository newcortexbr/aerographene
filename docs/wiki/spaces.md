# spaces (visual e textos)

como o menu do avatar, o seletor (`chrome://profile-picker`) e a criação de um space ficam no visual mono do aerographene, e como o texto "perfil" vira "space". O comportamento é o do Chromium: cada space é um perfil com janela própria ([ADR 0005](../adr/0005-space-e-janela.md)). Esta mudança é só de aparência e de texto.

## o que mudou

- menu do avatar (`profile_menu_view_base.cc`, patch `spaces-menu`): cantos retos; o cabeçalho vai de lado a lado, com um glifo (inicial do nome num quadrado de contorno fino, cor `kColorSysPrimary`) ao lado do nome, e uma linha fina embaixo no lugar do cartão preenchido. Os itens são os mesmos: Passwords and autofill, Customise space, Add space, Open guest window, Manage spaces.
- seletor (patch `spaces-picker`): fundo escuro liso com pontilhado, sem os banners e gradientes do Chromium, cartões retos com borda fina (borda clara no hover), cartão "Add space" tracejado com `+`, título "Which space?". O avatar de cada cartão é o glifo da inicial do nome; a cor do glifo roda por posição do cartão (paleta do mockup).
- criação de space: o passo "Set up your new space" e a página de customização (nome, cor, Done/Delete) seguem o mesmo visual. O avatar é o glifo do nome e o botão que abria o seletor de avatares origami fica oculto.
- textos: `build/strings_space.json` lista, por nome IDS, o texto en e pt-BR final (32 mensagens: menu, seletor, criação, remoção, troca). `build/branding_strings.py` troca o corpo da mensagem no `.grd`/`.grdp`, recalcula o id GRIT e grava o texto pt-BR e en-GB no `.xtb`; os outros idiomas só têm o id renomeado e mantêm a tradução antiga ("perfil"). Não se edita `.grd` à mão.

## o que não mudou

- o avatar escolhido continua gravado no perfil (índice do avatar do Chromium); só deixou de ser mostrado nessas telas. Escolher glifo ou cor de glifo por space exigiria guardar a escolha no perfil: não existe ainda.
- o picker usa paleta fixa escura: ele não carrega `chrome://theme/colors.css`, então `theme.json` não o afeta. A página de customização lê os tokens do tema, com o mesmo mono como reserva.
- moldura da janela do picker ("AEROGRAPHENE ×" do mockup), sombra dura do menu, cor de acento por space e o seletor de cores circular do Chromium (componente compartilhado) ficam como no upstream.
- Sign in, Google services e avisos de conta ainda dizem "profile" em partes fora dessas telas (configurações, diálogos de conta).

## como mudar um texto

1. ache o nome IDS (ex.: `IDS_PROFILE_MENU_ADD_PROFILE`) em `chrome/app/profiles_strings.grdp` ou `chromium_strings.grd`.
2. acrescente ou edite a entrada em `build/strings_space.json`: `{"en": "...", "pt-BR": "..."}`. Placeholders entram como `<ph name="X"/>` nos dois idiomas e precisam existir na mensagem. Evite apóstrofo (ICU).
3. `cd build && python3 test_branding_strings.py` (os testes de `space_body` e do JSON rodam sempre).

## resumo para agentes

- patches: `aerographene/spaces-menu.patch` (C++, `chrome/browser/ui/views/profiles/profile_menu_view_base.cc`: `SpaceGlyphView`, `SpaceGlyphText`, `set_corner_radius(0)`, cabeçalho horizontal) e `aerographene/spaces-picker.patch` (WebUI: `chrome/browser/resources/signin/profile_picker/*` e `profile_customization/*`: CSS e templates; `spaceGlyph()` em `profile_picker_util.ts`; `getGlyph_()` no app de customização). Nenhum arquivo novo, nenhum `BUILD.gn` tocado. Ao fim de `patches/series`.
- textos: `build/strings_space.json` + `branding_strings.py` (`load_space`, `space_body`, `--space`/`--no-space`); o hash da série em `build/inner.sh` inclui o JSON.
- glifo: `[\p{L}\p{N}]` do nome, maiúscula; sem match, "A". Menu em C++ usa `u_isalnum`/`u_toupper`.
- verificado: série aplica com `-F0` numa cópia descartável; `-fsyntax-only` do `.cc` do menu; strings reescritas conferidas nos `.xtb` pt-BR e en-GB num espelho (38 mensagens, 32 nomes). Não verificado: compilação dos recursos WebUI (esbuild/tsc), aparência no navegador (geometria dos cartões, menu), o glifo com nomes não latinos.
