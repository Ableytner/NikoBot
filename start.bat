SET /p DISCORD_TOKEN=< .\dc_token.txt
SET /p MAL_CLIENT_ID=< .\client_id.txt
".\venv\Scripts\python.exe" src/main.py
pause
