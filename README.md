# xi-membrane-fit (CG P1)

CG P1 ξ-membrane fit on Planck SMICA Cold Spot — one-off bundle pushed by Hermes Agent (sandbox).

## Files
- `xi_membrane_fit_v2.py` — main fit code (Python, GPU)
- `download.ps1` — PowerShell: download Planck SMICA from ESA
- `run.ps1` — PowerShell: download + fit launcher

## Win11 usage
```powershell
mkdir C:\CG\xi_membrane
Invoke-WebRequest https://raw.githubusercontent.com/Suk-Builder/xi-membrane-fit/main/xi_membrane_fit_v2.py -OutFile C:\CG\xi_membrane\xi_membrane_fit_v2.py
Invoke-WebRequest https://raw.githubusercontent.com/Suk-Builder/xi-membrane-fit/main/download.ps1 -OutFile C:\CG\xi_membrane\download.ps1
Invoke-WebRequest https://raw.githubusercontent.com/Suk-Builder/xi-membrane-fit/main/run.ps1 -OutFile C:\CG\xi_membrane\run.ps1
powershell -ExecutionPolicy Bypass -File C:\CG\xi_membrane\run.ps1
```

## Result
After fit runs, `C:\CG\xi_membrane\fit.log` has the result. Pull it back via frp WinRM (push to GitHub gist or another repo).
