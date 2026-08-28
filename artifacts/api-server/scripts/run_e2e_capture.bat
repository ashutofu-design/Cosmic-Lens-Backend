@echo off
set OUT=D:\Cosmic-Lens-Backend\artifacts\api-server\scripts\real_support_e2e.out.txt
echo STARTED %DATE% %TIME%> "%OUT%"
cd /d D:\Cosmic-Lens-Backend\artifacts\api-server
C:\Users\HP\miniconda3\python.exe -u D:\Cosmic-Lens-Backend\artifacts\api-server\scripts\real_support_e2e.py >> "%OUT%" 2>&1
echo EXIT_CODE=%ERRORLEVEL%>> "%OUT%"
