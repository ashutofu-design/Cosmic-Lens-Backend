$ErrorActionPreference = 'Continue'
Set-Location 'D:\Cosmic-Lens-Backend\artifacts\api-server'
$out = 'D:\Cosmic-Lens-Backend\artifacts\cosmic-lens-mobile\_chart_fact_test_results.txt'
"" | Set-Content -Path $out -Encoding utf8
python -m unittest tests.test_needs_llm_chart_answer tests.test_answer_mode tests.test_chart_fact_love_style -v *>&1 | Out-File -FilePath $out -Encoding utf8 -Append
"EC=$LASTEXITCODE" | Add-Content -Path $out
python -c "from chart_fact_answer import is_pure_chart_fact_lookup, _detect_divisional; print('ok', is_pure_chart_fact_lookup('x'), _detect_divisional('D10'))" *>&1 | Out-File -FilePath $out -Encoding utf8 -Append
"IMPORT_EC=$LASTEXITCODE" | Add-Content -Path $out
Get-Content $out
