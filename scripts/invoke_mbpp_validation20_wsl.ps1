param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("qwen3.5:4b", "qwen3.5:9b", "qwen3:0.6b")]
    [string]$Model,

    [Parameter(Mandatory = $true)]
    [ValidateSet(
        "generation-preflight",
        "generation-resume",
        "evalplus-preflight",
        "evalplus-execute",
        "evalplus-resume"
    )]
    [string]$Action
)

$ErrorActionPreference = "Stop"
$repoWin = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$repoWsl = "/mnt/" + ($repoWin.Substring(0, 1).ToLower() + $repoWin.Substring(2).Replace("\", "/"))

switch ($Action) {
    "generation-preflight" {
        $cmd = "cd '$repoWsl' && python3 scripts/preflight_mbpp_validation20_generation_v1.py --model $Model"
    }
    "generation-resume" {
        $cmd = "cd '$repoWsl' && python3 scripts/run_mbpp_validation20_generation_v1.py --model $Model --resume --acknowledgement I_ACKNOWLEDGE_THIS_WILL_CALL_THE_PINNED_VALIDATION20_MODEL"
    }
    "evalplus-preflight" {
        $cmd = "cd '$repoWsl' && python3 scripts/run_mbpp_validation20_evalplus_qualification_v1.py --model $Model --preflight"
    }
    "evalplus-execute" {
        $cmd = "cd '$repoWsl' && python3 scripts/run_mbpp_validation20_evalplus_qualification_v1.py --model $Model --execute --parallel 1 --acknowledgement I_ACKNOWLEDGE_VALIDATION20_EVALPLUS_FORMAL_EXECUTION"
    }
    "evalplus-resume" {
        $cmd = "cd '$repoWsl' && python3 scripts/run_mbpp_validation20_evalplus_qualification_v1.py --model $Model --resume --parallel 1 --acknowledgement I_ACKNOWLEDGE_VALIDATION20_EVALPLUS_FORMAL_EXECUTION"
    }
}

Write-Host "WSL command:"
Write-Host $cmd
wsl.exe -e bash -lc $cmd
exit $LASTEXITCODE
