@echo off
cd /d "%~dp0"
echo Installing Razorpay dependency fix (setuptools with pkg_resources)...
venv\Scripts\pip.exe install "setuptools>=65,<81"
echo.
echo Testing razorpay import...
venv\Scripts\python.exe -c "import pkg_resources; import razorpay; print('OK: razorpay ready')"
pause
