$url = "http://pla.esac.esa.int/pla/aio/product-action?MAP.MAP_ID=COM_CMB_IQU-smica_2048_R3.00_full.fits"
$out = "C:\CG\xi_membrane\COM_CMB_IQU-smica.fits"
if (Test-Path $out) {
    Write-Host "Already:" (Get-Item $out).Length
} else {
    Write-Host "Downloading from ESA Planck..."
    Invoke-WebRequest -Uri $url -OutFile $out -UseBasicParsing
    Write-Host "Done:" (Get-Item $out).Length "bytes"
}
