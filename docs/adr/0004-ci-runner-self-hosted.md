# build em runner self-hosted da org newcortexbr, sem execução de terceiros

O build roda no runner self-hosted "intense" da org `newcortexbr`, no Cezanne (R5 5600G, WSL2 Ubuntu 24.04, ~14 GB de RAM, 200 GB de disco). O repositório fica na org. Como é open-source e o runner executa código na máquina do usuário, só o dono dispara builds: os workflows rodam em `push`/`workflow_dispatch` do dono, nunca em `pull_request` de fork. Contribuições externas por PR ficam fechadas.
