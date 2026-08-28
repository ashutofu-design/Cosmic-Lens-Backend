Set sh = CreateObject("WScript.Shell")
sh.CurrentDirectory = "D:\Cosmic-Lens-Backend\artifacts\api-server"
sh.Run "cmd.exe /c D:\Cosmic-Lens-Backend\artifacts\api-server\scripts\run_e2e_capture.bat", 0, False
