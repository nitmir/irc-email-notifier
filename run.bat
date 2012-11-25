@echo off
:loop
%1;
REM Caca pour attendre 5s avant de relancer le script
ping 127.0.0.1 -n 5 > NUL 
goto loop