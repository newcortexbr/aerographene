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
