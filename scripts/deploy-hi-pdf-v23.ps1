# Deploy Love Reality Hindi PDF v23 fixes to VPS
$ErrorActionPreference = "Stop"
$Host = "root@187.127.174.55"
$Base = "d:\Cosmic-Lens-Backend\artifacts\api-server"
$Remote = "/root/Cosmic-Lens-Backend/artifacts/api-server"

$files = @(
    @{ Local = "$Base\milan_pdf.py"; Remote = "$Remote/milan_pdf.py" },
    @{ Local = "$Base\love_reality_pdf.py"; Remote = "$Remote/love_reality_pdf.py" },
    @{ Local = "$Base\love_reality_api.py"; Remote = "$Remote/love_reality_api.py" },
    @{ Local = "$Base\vedic\love_reality\pdf_page1_premium.py"; Remote = "$Remote/vedic/love_reality/pdf_page1_premium.py" },
    @{ Local = "$Base\vedic\love_reality\pdf_toc.py"; Remote = "$Remote/vedic/love_reality/pdf_toc.py" },
    @{ Local = "$Base\scripts\verify_hi_pdf_font.py"; Remote = "$Remote/scripts/verify_hi_pdf_font.py" }
)

foreach ($f in $files) {
    Write-Host "Uploading $($f.Local) ..."
    scp $f.Local "${Host}:$($f.Remote)"
}

Write-Host "Remote restart + cache clear ..."
ssh $Host @"
cd $Remote
rm -rf .cache/reports/* && rm -f .cache/love_polish/*.json
export LOVE_REALITY_PREMIUM_POLISH=1 LOVE_REALITY_FORCE_LLM=1
pm2 restart cosmic-api --update-env
python3 scripts/verify_hi_pdf_font.py
grep LOVE_REALITY_PDF_LAYOUT_VER love_reality_api.py | head -1
"@

Write-Host "Done."
