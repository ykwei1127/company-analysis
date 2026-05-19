# Glassdoor Dashboard - Start both backend and frontend
Write-Host "Starting Glassdoor Dashboard..." -ForegroundColor Cyan

# Start backend
Write-Host "  [Backend] FastAPI on http://127.0.0.1:8000" -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

# Start frontend
Write-Host "  [Frontend] Vue 3 on http://localhost:5173" -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; npm run dev"

Write-Host ""
Write-Host "Dashboard ready:" -ForegroundColor Yellow
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "  Backend:  http://127.0.0.1:8000/docs" -ForegroundColor White
