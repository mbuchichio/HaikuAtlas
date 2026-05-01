@echo off
setlocal
set "ATLAS_ROOT=%~dp0"
set "PYTHONPATH=%ATLAS_ROOT%src;%PYTHONPATH%"

py -3 -m haiku_atlas.cli.indexer %*
if not errorlevel 9009 exit /b %errorlevel%

python -m haiku_atlas.cli.indexer %*
exit /b %errorlevel%
