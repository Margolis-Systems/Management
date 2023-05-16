c:
cd c:\projects\tzomet\management
set /p mytextfile=< pid.txt
taskkill /F /PID %mytextfile%
venv\Scripts\python.exe main.py