# aerographene é uma série de patches própria sobre o ungoogled-chromium

O aerographene é construído como série de patches sobre o ungoogled-chromium, na camada `//chrome`, e não como fork do Helium nem como navegador próprio sobre `//content`. O ungoogled já entrega os cortes de serviços Google (telemetria, variations, Safe Browsing), que ajudam a abertura e a RAM. Partir do Helium seria herdar um produto pronto, o que o usuário não quer. Partir do `//content` perderia extensões, perfis, senhas e histórico, que moram em `//chrome`. Patches do Helium e flags do Thorium entram um por um, cada um com justificativa.

## Consequences

- O login Google com sync não funciona: o Google restringe as APIs de sync a builds que não são Chrome, e o ungoogled remove essa integração.
