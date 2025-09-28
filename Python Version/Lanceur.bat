@echo off
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo ====================================================
    echo   [ERREUR] Lancez ce launcher en tant qu'administrateur !
    echo ====================================================
    timeout /t 3 >nul
    exit /b 1
)

pushd "%~dp0"

where py >nul 2>&1
if %errorLevel% EQU 0 (
    py "%~dp0a.py"
) else (
    where python >nul 2>&1
    if %errorLevel% EQU 0 (
        python "%~dp0a.py"
    ) else (
        echo [ERREUR] Python introuvable dans le PATH. Installez Python ou ajoutez-le au PATH.
        popd
        exit /b 1
    )
)

popd
exit /b 0
