@echo off
for /f %%a in ('powershell -Command "[int64]((Get-Date).ToUniversalTime() - (Get-Date "1970-01-01T00:00:00Z")).TotalMilliseconds"') do set timestamp=%%a
git add . -v
git commit -m "update %timestamp%"
git push -u origin main

REM git pull origin main
pause
