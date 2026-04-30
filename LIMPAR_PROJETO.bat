@echo off
cls
echo ====================================================
echo   LIMPANDO PASTAS E ARQUIVOS REDUNDANTES (ENXUGAR)
echo ====================================================
echo.

echo Excluindo pastas antigas (backups e repositorios duplicados)...
if exist "landing_page" rmdir /s /q "landing_page"
if exist "rentalsmart" rmdir /s /q "rentalsmart"
if exist "simulador_rental" rmdir /s /q "simulador_rental"

echo Excluindo arquivos desnecessarios (zips e scripts antigos)...
if exist "rentalsmart.zip" del /f /q "rentalsmart.zip"
if exist "zip_maker.py" del /f /q "zip_maker.py"
if exist "tmp_cleanup.py" del /f /q "tmp_cleanup.py"
if exist "passenger_wsgi.py" del /f /q "passenger_wsgi.py"

echo.
echo Limpeza concluida! O projeto agora esta enxuto e pronto para o deploy.
pause
