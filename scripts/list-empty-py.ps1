# Lists zero-byte Python files under api-server (broken copies)
$root = "D:\Cosmic-Lens-Backend\artifacts\api-server"
$out = "D:\Cosmic-Lens-Backend\empty-py-files.txt"
Get-ChildItem $root -Filter "*.py" -File -Recurse -ErrorAction SilentlyContinue |
    Where-Object { $_.Length -eq 0 } |
    ForEach-Object { $_.FullName } |
    Set-Content $out
Write-Host "Wrote $($out)"
Get-Content $out
