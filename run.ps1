Set-Location C:\CG\xi_membrane
Write-Host "===== 1. DOWNLOAD ====="
powershell -ExecutionPolicy Bypass -File C:\CG\xi_membrane\download.ps1 2>&1 | Out-File download.log
Get-Content download.log
Write-Host "===== 2. FIT ====="
& 'C:\Users\Administrator\AppData\Local\Programs\Python\Python310\python.exe' xi_membrane_fit_v2.py 2>&1 | Out-File fit.log
Get-Content fit.log
Write-Host "===== DONE ====="
