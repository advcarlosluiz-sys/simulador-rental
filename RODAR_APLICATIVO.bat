@echo off
cls
echo ====================================================
echo   INICIANDO RENTAL SMART (ALVES ADVOCACIA)
echo ====================================================
echo.

REM Vai para a pasta onde o arquivo .bat está localizado (com aspas para evitar erro de espaço)
cd /d "%~dp0"

echo Local atual: %cd%
echo.
echo Tentando iniciar o servidor...
echo.

python app.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    echo   ERRO DETECTADO AO INICIAR O PROGRAMA
    echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    echo Por favor, tire uma foto desta tela e me envie.
)
pause
