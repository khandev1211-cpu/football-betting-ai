@echo off
echo Starting Football Betting AI Development Environment...
echo.

echo Starting Backend Server...
start "Backend" cmd /k "cd backend && python src/main.py"

echo Waiting for backend to start...
timeout /t 5 /nobreak > nul

echo Starting Frontend Development Server...
start "Frontend" cmd /k "cd frontend && pnpm run dev --host"

echo.
echo Development servers are starting...
echo Backend: http://localhost:5000
echo Frontend: http://localhost:5173
echo.
echo Press any key to exit...
pause > nul
