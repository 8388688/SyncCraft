@REM set fp=I:\2020\8388688\ClosedSpace\Misc\File\py_files\myworkspace\Zmp-X\Peeker\history\v1.5.0_Release
set fp=%~dp0
pyinstaller --noconfirm --onefile --windowed --icon "%fp%\assets\icon.ico" --add-data "%fp%\assets;assets/"  "%fp%\SyncCraft.py"
