$ErrorActionPreference = 'Stop'

$cases = @(
  '計算 (-2 1/6)+1 2/9-(-1 1/3) 的值。',
  '計算 (-2 3/4)+1 2/7 的值。',
  '計算 | 8×(-2)-5 | ÷ 7×(-3) 的值。',
  '計算 (3/5-7/10)+(-2/3) 的值。',
  '計算 (-4 1/2)÷(1 1/5)+3/10 的值。'
)

$idx = 0
foreach ($txt in $cases) {
  $idx += 1

  $c = @{ text_data = $txt } | ConvertTo-Json -Depth 10
  Set-Content -Path ".\tmp_reg_c_$idx.json" -Value $c -Encoding utf8
  $cres = curl.exe -s -X POST http://127.0.0.1:5000/api/classify -H "Content-Type: application/json" --data-binary "@tmp_reg_c_$idx.json"
  $cj = $cres | ConvertFrom-Json

  $gobj = @{ prompt = $txt; ablation_mode = $false; model_id = 'qwen3-8b'; skill_id = $cj.skill_id }
  $gjson = $gobj | ConvertTo-Json -Depth 10
  Set-Content -Path ".\tmp_reg_g_$idx.json" -Value $gjson -Encoding utf8

  $gres = curl.exe -s -X POST http://127.0.0.1:5000/api/generate_live -H "Content-Type: application/json" --data-binary "@tmp_reg_g_$idx.json"
  Set-Content -Path ".\tmp_reg_resp_$idx.json" -Value $gres -Encoding utf8
  $o = $gres | ConvertFrom-Json

  $hasGenerate = [bool](($o.final_code + '') -match '(?m)^\s*def\s+generate\s*\(')
  $eqRaw = [bool]($o.ab2_result.raw_code -eq $o.raw_code)

  Write-Output "CASE#$idx"
  Write-Output "input=$txt"
  Write-Output "success=$($o.success) route=$($o.route_mode)"
  Write-Output "ab3_error=$($o.error)"
  Write-Output "ab2_error=$($o.ab2_result.error)"
  Write-Output "ab3_has_generate=$hasGenerate"
  Write-Output "eq_raw=$eqRaw"
  Write-Output "ab2_problem=$((($o.ab2_result.problem + '') -replace "`r|`n",' '))"
  Write-Output "ab3_problem=$((($o.problem + '') -replace "`r|`n",' '))"
  Write-Output ""
}
