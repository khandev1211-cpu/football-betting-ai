@echo off
echo Setting up Football Betting AI Development Environment...
echo.

echo Checking Backend Dependencies...
cd backend
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing Python dependencies...
pip install -r requirements.txt

echo.
echo Checking Frontend Dependencies...
cd ..\frontend

echo Installing Node.js dependencies...
pnpm install

echo.
echo Setup complete!
echo.
echo To start the development servers, run: start-dev.bat
echo Or manually:
echo   Backend: cd backend ^&^& python src/main.py
echo   Frontend: cd frontend ^&^& pnpm run dev --host
echo.
pause
