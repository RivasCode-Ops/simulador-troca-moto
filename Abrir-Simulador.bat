@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Criando ambiente virtual...
  python -m venv .venv
  call .venv\Scripts\pip install -r requirements.txt
) else (
  call .venv\Scripts\pip install -q -r requirements.txt
)
echo Iniciando Simulador de Troca de Moto...
start "Streamlit" /MIN cmd /c ".venv\Scripts\streamlit run app.py --server.headless true"
echo Aguardando servidor em http://localhost:8501 ...
powershell -NoProfile -Command "$ok=$false; 1..30 | ForEach-Object { try { $r=Invoke-WebRequest -Uri 'http://localhost:8501' -UseBasicParsing -TimeoutSec 2; if ($r.StatusCode -eq 200) { $ok=$true; break } } catch {}; Start-Sleep -Seconds 1 }; if (-not $ok) { Write-Host 'Servidor nao respondeu a tempo. Abra http://localhost:8501 manualmente.'; exit 1 }; Start-Process 'http://localhost:8501'"
if errorlevel 1 pause
exit /b 0
