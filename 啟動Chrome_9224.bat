@echo off
echo 正在啟動 Chrome 瀏覽器（調試模式 port 9224）...
echo.
echo 請在打開的 Chrome 中登入 Glassdoor
echo.

"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9224 --user-data-dir="%USERPROFILE%\selenium\ChromeProfile9224"
