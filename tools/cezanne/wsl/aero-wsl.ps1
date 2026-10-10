# aero-wsl.ps1: roda os runners do cezanne no Windows, via WSL2, a partir do disco do Ubuntu bare metal.
# Uso (PowerShell como administrador):
#   .\aero-wsl.ps1 up     # monta o disco do Ubuntu no WSL e sobe docker + runners
#   .\aero-wsl.ps1 down   # encerra os runners (cancela/comenta jobs) e desmonta o disco
#   .\aero-wsl.ps1 status
# Rode SEMPRE "down" antes de desligar o Windows: o disco precisa estar desmontado ao voltar para o Ubuntu.
param([Parameter(Mandatory = $true)][ValidateSet("up", "down", "status")][string]$Action)
$ErrorActionPreference = "Stop"

$Distro = "aero-runners"
$MountName = "aero-sdc"
$DiskModel = "*ProDrive*"   # disco do Ubuntu (ProDrive 240GB); o Windows fica em outros discos
$Partition = 2              # sdc2 = raiz ext4

function Get-UbuntuDisk {
    $d = @(Get-Disk | Where-Object { $_.FriendlyName -like $DiskModel })
    if ($d.Count -ne 1) { throw "esperava 1 disco '$DiskModel', achei $($d.Count). Confira com Get-Disk." }
    if ($d[0].Number -eq (Get-Partition -DriveLetter $env:SystemDrive[0]).DiskNumber) {
        throw "o disco '$DiskModel' é o disco do Windows; abortado"
    }
    return "\\.\PHYSICALDRIVE$($d[0].Number)"
}

switch ($Action) {
    "up" {
        $disk = Get-UbuntuDisk
        Write-Host "montando $disk partição $Partition como $MountName"
        wsl --mount $disk --partition $Partition --type ext4 --name $MountName
        if ($LASTEXITCODE -ne 0) { throw "wsl --mount falhou ($LASTEXITCODE)" }
        wsl -d $Distro -u root -- /opt/aero-wsl/up.sh
        if ($LASTEXITCODE -ne 0) { throw "up.sh falhou ($LASTEXITCODE); rode '.\aero-wsl.ps1 down'" }
        # o WSL encerra a distro sem sessão aberta; um processo oculto a mantém viva
        Start-Process -WindowStyle Hidden wsl.exe -ArgumentList "-d", $Distro, "-u", "root", "--", "sleep", "infinity"
        Write-Host "runners no ar. Antes de desligar o Windows: .\aero-wsl.ps1 down"
    }
    "down" {
        $disk = Get-UbuntuDisk
        wsl -d $Distro -u root -- /opt/aero-wsl/down.sh
        if ($LASTEXITCODE -ne 0) { Write-Warning "down.sh saiu com $LASTEXITCODE; desmontando assim mesmo" }
        wsl --terminate $Distro
        wsl --unmount $disk
        if ($LASTEXITCODE -ne 0) { throw "wsl --unmount $disk falhou ($LASTEXITCODE); NAO volte para o Ubuntu antes de desmontar (wsl --unmount)" }
        Write-Host "disco desmontado; pode desligar ou voltar para o Ubuntu"
    }
    "status" {
        wsl -d $Distro -u root -- /opt/aero-wsl/up.sh --status
    }
}
