c:
cd c:\server
net start mongodb
set /p mytextfile=< pid.txt
taskkill /F /PID %mytextfile%
venv\Scripts\python.exe main.py True