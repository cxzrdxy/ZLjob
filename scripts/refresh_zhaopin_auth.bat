@echo off
cd /d %~dp0..
python scripts\refresh_zhaopin_auth.py
pause
