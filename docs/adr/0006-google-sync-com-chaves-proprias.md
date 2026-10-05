# Google Sync com chaves próprias, como o Thorium

O aerographene terá login e sync da conta Google (histórico, senhas etc.) usando chaves de API próprias do dono (`google_api_key`, `google_default_client_id`, `google_default_client_secret`), embutidas nos builds da mesma forma que o Thorium faz. As chaves vão no `args.gn` e saem em todos os builds públicos: um build único, igual ao Thorium. Alternativas descartadas: sync próprio do Helium (vault criptografado); ficar sem sync; dois builds (pessoal com chaves e público sem), que dobraria o tempo de build; e build sem chaves com as chaves passadas por variável de ambiente só no lançador do dono, que não daria sync a quem baixasse. Confirmado pelo dono em 04/10/2026.

## Consequences

- Os termos do Google não permitem distribuir essas chaves; o Google pode revogá-las e cortar o sync de todos os builds. Risco aceito pelo dono em 04/10/2026.
- As chaves nunca entram no repositório (público): vêm de secrets do GitHub Actions no runner, ou de variáveis de ambiente (`GOOGLE_API_KEY`, `GOOGLE_DEFAULT_CLIENT_ID`, `GOOGLE_DEFAULT_CLIENT_SECRET`).
- O ungoogled-chromium remove parte da integração com contas Google. Antes de prometer o sync, é preciso testar se o login funciona com as chaves sobre essa base, e talvez reverter patches do ungoogled.
- Plano B, se a base impedir: sync próprio do Helium (`patches/helium/core/sync/`).
