' 静默启动刷题进度服务器（无控制台窗口）
' 由计划任务「广东公考刷题服务器」在登录时调用；也可以双击运行
Option Explicit

Dim fso, sh, base, pyw, cmd
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh = CreateObject("WScript.Shell")

base = fso.GetParentFolderName(WScript.ScriptFullName)
pyw = "C:\Users\84307\.workbuddy\binaries\python\versions\3.13.12\pythonw.exe"

If Not fso.FileExists(pyw) Then
  ' 兜底：换用系统 Python
  pyw = "C:\Users\84307\AppData\Local\Programs\Python\Python314\pythonw.exe"
End If

sh.CurrentDirectory = base
cmd = """" & pyw & """ """ & base & "\server.py"""
sh.Run cmd, 0, False
