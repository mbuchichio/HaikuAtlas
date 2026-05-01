@echo off
setlocal
set "ATLAS_ROOT=%~dp0"
set "PYTHONPATH=%ATLAS_ROOT%src;%PYTHONPATH%"

py -3 -m haiku_atlas.cli.query %*
if not errorlevel 9009 exit /b %errorlevel%

python -m haiku_atlas.cli.query %*
exit /b %errorlevel%
