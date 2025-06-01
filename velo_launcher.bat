@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title Velo Launcher - Welcome back %username%

:menu
cls
color F
echo.
echo     SELECT GAME MODE
echo.
color %COLOR_MENU%
echo  1. Battle Royale Duos
echo  2. Battle Royale Quads
echo  3. Resurgence Solos
echo  4. Resurgence Duos
echo  5. Resurgence Trios
echo  6. Resurgence Quads
echo  7. Plunder
echo  8. Prop Hunt
echo.
echo  0. Exit
echo.

color %COLOR_INPUT%
choice /c 0123456789 /n /m ""
set /a choice=%errorlevel%-1

color %COLOR_RESET%

goto :option_%choice%

:: Options

:option_1
title Velo Booster - Battle Royale Duos
python bot.py mode=battle-royale-duos
goto :end

:option_2
title Velo Booster - Battle Royale Quads
python bot.py mode=battle-royale-quads
goto :end

:option_3
title Velo Booster - Resurgence Solos
python bot.py mode=resurgence-solos
goto :end

:option_4
title Velo Booster - Resurgence Duos
python bot.py mode=resurgence-duos
goto :end

:option_5
title Velo Booster - Resurgence Trios
python bot.py mode=resurgence-trios
goto :end

:option_6
title Velo Booster - Resurgence Quads
python bot.py mode=resurgence-quads
goto :end

:option_7
title Velo Booster - Plunder
python bot.py mode=plunder
goto :end

:option_8
title Velo Booster - Prop Hunt
python bot.py mode=prop-hunt
goto :end

:option_0
exit /b 0

:end
echo.
echo Press any key to return to menu...
pause >nul
goto :menu
