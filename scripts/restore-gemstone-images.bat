@echo off
python -m pip install Pillow -q
python "%~dp0restore-gemstone-images.py"
if errorlevel 1 exit /b 1
echo OK
exit /b 0
