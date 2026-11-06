@echo off
rem Full-screen pulsing heart. Press any key in the window to close it.
start "" wt.exe --fullscreen --title love python "%~dp0pulse_heart.py"
