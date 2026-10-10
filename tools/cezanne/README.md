# aero-top

TUI compacto (Python 3 + curses, só stdlib) para o host `cezanne`: recursos da máquina,
os 3 runners self-hosted do GitHub Actions e as runs recentes. Refresh de 1 s, `q` sai.

```
aero-top            # TUI
aero-top --once --size 80x24   # um frame em texto (teste/diagnóstico)
aero-top --ascii    # bordas e barras ASCII
```

## de onde vem cada dado

- CPU total/por thread: `/proc/stat`; temperatura: hwmon `k10temp` (`temp1_input`).
- RAM: `/proc/meminfo`; zram e swap em disco: `/proc/swaps` (separados por `/dev/zram*`).
- I/O de disco: `/proc/diskstats` (`sd*`, `nvme*n*`, `vd*`; sem loop/zram).
- GPU: `nvidia-smi` se existir; senão "nouveau: sem métricas".
- estado do runner: existe processo `Runner.Worker` com cmdline em `actions-runner-N/` (mesmo critério do cpu-quota-manager); falha = última run do runner terminou `Failed`, até a próxima iniciar.
- núcleos atribuídos: `systemctl show -p CPUQuotaPerSecUSec` da unit (lida de `actions-runner-N/.service`), em segundos de CPU/s = núcleos.
- job/repo/workflow atual: início do `_diag/Worker_*.log` mais recente do runner.
- última linha do log: `_diag/pages/*.log` mais recente (saída das steps, o runner descarrega em blocos; linha final incompleta é ignorada); se estiver parada >5 s e houver container docker montando `actions-runner-N/_work`, usa `docker logs --tail 3`.
- runs recentes: `_diag/Runner_*.log` ("Running job: X" / "Job X completed with result: R"); repo casado com o `Worker_*.log` iniciado logo depois. Não usa `gh` nem rede.
- dados lentos (systemctl, docker, nvidia-smi, parse dos logs) são atualizados a cada 5 s.

Variável `AERO_RUNNERS_DIR` (padrão `/home/dasher`) muda onde procurar `actions-runner-*`.

## instalar

```
sudo install -m755 tools/cezanne/aero-top /usr/local/bin/aero-top
```

Sem serviço nem autologin: é um comando para abrir quando quiser. Rodar como o dono dos
runners (`dasher`) para ler `_diag/` e falar com o docker.

## teste

```
python3 tools/cezanne/test_aero_top.py
```

# aero-poweroff

Encerra os runners com aviso e reinicia o cezanne direto no Windows (só nesse boot; o padrão continua o Ubuntu).

```
aero-poweroff --dry-run     # mostra o que faria
aero-poweroff               # pede confirmação
aero-poweroff --yes --off   # desliga em vez de reiniciar
aero-poweroff --no-reboot   # só encerra os runners
```

1. runners ociosos: `systemctl stop` na unit (saem do pool na hora).
2. runners ocupados: o job é localizado pela API (`runner_name` nos jobs `in_progress` dos repos da org, paginado), recebe um comentário no PR da run (ou no commit, se não houver PR) e a run é cancelada, uma vez por run. O Listener é parado logo em seguida (o `Runner.Worker` sobrevive por `KillMode=process` e conclui o cancelamento), para o runner não pegar job novo. Espera o Worker sair por até `--grace` s (180); depois `force-cancel` e SIGKILL no Worker e filhos. Falha de API vira aviso. Garantia final: antes de reiniciar/desligar (ou retornar em `--no-reboot`) confere de novo; se ainda houver Worker vivo, o script aborta com rc 1 sem reiniciar.
3. containers docker ainda rodando: `docker stop -t 20`.
4. `efibootmgr --bootnext <Windows Boot Manager>` e `systemctl reboot`. `grub-reboot` não serve aqui (`GRUB_DEFAULT=0`).

Roda como root (reexecuta com `sudo`); o `gh` roda como `dasher`, que precisa estar logado (escopos `repo`, `workflow`). Cancelar a run cancela os jobs dela em outros runners também.

```
sudo install -m755 tools/cezanne/aero-poweroff /usr/local/bin/aero-poweroff
```

# runners no Windows (WSL2) a partir do disco do Ubuntu

O Ubuntu ocupa um disco só dele (ProDrive 240GB, `sdc`), então o Windows consegue entregá-lo inteiro ao WSL2 com `wsl --mount`. Uma distro leve `aero-runners` liga `/home/dasher` (runners, `_work`, cache da build) e `/var/lib/docker` do disco e sobe as mesmas units dos runners: mesmos registros, mesmo cache. Só um sistema usa o disco por vez.

Setup único no Windows (PowerShell admin), com o repo clonado:

```
wsl --install -d Ubuntu-24.04 --name aero-runners --no-launch
wsl -d aero-runners -u root -- bash tools/cezanne/wsl/setup.sh   # a partir da pasta do repo
wsl --terminate aero-runners
```

Uso:

```
.\tools\cezanne\wsl\aero-wsl.ps1 up      # monta o disco e sobe docker + runners
.\tools\cezanne\wsl\aero-wsl.ps1 down    # aero-poweroff --no-reboot, desfaz binds, desmonta
```

- rode sempre `down` antes de desligar o Windows; desligar com o disco montado deixa o ext4 sujo (o journal recupera no boot do Ubuntu, mas não conte com isso).
- o WSL2 usa por padrão metade da RAM; para builds, ponha em `%UserProfile%\.wslconfig`: `[wsl2]` com `memory=12GB`, `processors=12`, `swap=16GB`.
- o `cpu-quota-manager` não roda no WSL; os runners ficam sem CPUQuota.
- desempenho menor que o bare metal (virtualização e disco via Hyper-V); não comparar tempos de build entre os dois.
- não testado num Windows real até agora.
