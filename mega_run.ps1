Set-Location C:\CG\xi_membrane
$python = 'C:\Users\Administrator\AppData\Local\Programs\Python\Python310\python.exe'

Write-Host "===== STEP 1: 检查 Python 环境 ====="
& $python -c "import sys, numpy, healpy; print('Python:', sys.version.split()[0]); print('numpy:', numpy.__version__); print('healpy:', healpy.__version__)" 2>&1

Write-Host "===== STEP 2: 下载 Planck SMICA ====="
if (Test-Path 'C:\CG\xi_membrane\COM_CMB_IQU-smica.fits') {
    Write-Host "Already exists:" (Get-Item 'C:\CG\xi_membrane\COM_CMB_IQU-smica.fits').Length "bytes"
} else {
    Write-Host "Downloading from ESA..."
    Invoke-WebRequest -Uri 'http://pla.esac.esa.int/pla/aio/product-action?MAP.MAP_ID=COM_CMB_IQU-smica_2048_R3.00_full.fits' -OutFile 'C:\CG\xi_membrane\COM_CMB_IQU-smica.fits' -UseBasicParsing -TimeoutSec 600
    Write-Host "Download done:" (Get-Item 'C:\CG\xi_membrane\COM_CMB_IQU-smica.fits').Length "bytes"
}

Write-Host "===== STEP 3: 跑 ξ-membrane fit ====="
& $python C:\CG\xi_membrane\xi_membrane_fit_v2.py 2>&1

Write-Host "===== ALL DONE ====="
