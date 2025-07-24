# type: ignore

# The decky plugin module is located at decky-loader/plugin
# For easy intellisense checkout the decky-loader code repo
# and add the `decky-loader/plugin/imports` path to `python.analysis.extraPaths` in `.vscode/settings.json`
import decky
import asyncio
import os
import sys
# import time
import subprocess
import math
import re
import keyboard
import winreg
import mmap
import struct
import platform
import sys
import copy
decky.logger.info(f"Platform: {platform.architecture()}")
decky.logger.info(f"Platform: {platform.python_implementation()}")
decky.logger.info(f"Version: {sys.version}")
# decky.logger.info(f"Path: {sys.path}")

import ADLXPybind as ADLX
# Begin additional setup for pywin32, similar to pywin32.pth
if os.path.join(decky.DECKY_PLUGIN_DIR, "py_modules", "win32") not in sys.path:
    sys.path.append(os.path.join(decky.DECKY_PLUGIN_DIR, "py_modules", "win32"))
if os.path.join(decky.DECKY_PLUGIN_DIR, "py_modules", "win32", "lib") not in sys.path:
    sys.path.append(os.path.join(decky.DECKY_PLUGIN_DIR, "py_modules", "win32", "lib"))
if os.path.join(decky.DECKY_PLUGIN_DIR, "py_modules", "Pythonwin") not in sys.path:
    sys.path.append(os.path.join(decky.DECKY_PLUGIN_DIR, "py_modules", "Pythonwin"))
import pywin32_bootstrap
# End additional setup for pywin32

import screen_brightness_control as sbc
import win32api
import win32con
import pywintypes
import psutil
import win32gui
import win32process
from psutil import NoSuchProcess
from collections import defaultdict
from datetime import datetime
from ctypes import *
from ctypes.wintypes import *
from shutil import copyfile
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import xml2.etree.ElementTree as ET
from enum import Enum
# from overlay_editor_client import OverlayEditorClient

ryzenadj_lib_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(ryzenadj_lib_path)

if sys.platform == 'win32' or sys.platform == 'cygwin':
    try:
        os.add_dll_directory(ryzenadj_lib_path)
    except AttributeError:
        pass #not needed for old python version

    winring0_driver_file_path = os.path.join(os.path.dirname(os.path.abspath(sys.executable)), 'WinRing0x64.sys')
    if not os.path.isfile(winring0_driver_file_path):
        copyfile(os.path.join(ryzenadj_lib_path, "bin", "ryzenadj", 'WinRing0x64.sys'), winring0_driver_file_path)

    ryzenadj_lib = cdll.LoadLibrary(os.path.join("bin", "ryzenadj", "libryzenadj"))
else:
    ryzenadj_lib = cdll.LoadLibrary(os.path.join("bin", "ryzenadj", "libryzenadj.so"))

# define ctype mappings for types which can not be mapped automatically
ryzenadj_lib.init_ryzenadj.restype = c_void_p
ryzenadj_lib.refresh_table.argtypes = [c_void_p]
ryzenadj_lib.get_fast_limit.restype = c_float
ryzenadj_lib.get_fast_limit.argtypes = [c_void_p]

ry = ryzenadj_lib.init_ryzenadj()

if not ry:
    decky.logger.error("RyzenAdj could not get initialized")

#ryzenadj_lib.refresh_table(ry)

error_messages = {
    -1: "{:s} is not supported on this family\n",
    -3: "{:s} is not supported on this SMU\n",
    -4: "{:s} is rejected by SMU\n"
}

# RTSS SHARED MEMORY
last_dwTime0s = defaultdict(int)

def adjust(field, value):
    if not ry:
        decky.logger.error(f"Can't adjust {field} because not an AMD CPU")
        return
    function_name = "set_" + field
    adjust_func = ryzenadj_lib.__getattr__(function_name)
    adjust_func.argtypes = [c_void_p, c_ulong]
    res = adjust_func(ry, value)
    if res:
        decky.logger.error(f"Adjust {field} using {function_name} failed: {res}")

def determine(field):
    if not ry:
        decky.logger.error(f"Can't determine {field} because not an AMD CPU")
        return 10
    # First, refresh the table to ensure we have the latest values
    ryzenadj_lib.refresh_table(ry)
    function_name = "get_" + field
    determine_func = ryzenadj_lib.__getattr__(function_name)
    determine_func.argtypes = [c_void_p]
    determine_func.restype = c_float
    res = determine_func(ry)
    # decky.logger.info(f"Determined {field}: {res}")
    if math.isnan(res):
        return 10
    return res

def enable(field):
    if not ry:
        decky.logger.error(f"Can't enable {field} because not an AMD CPU")
        return
    function_name = "set_" + field
    adjust_func = ryzenadj_lib.__getattr__(function_name)
    adjust_func.argtypes = [c_void_p]
    res = adjust_func(ry)
    if res:
        error = error_messages.get(res, "{:s} did fail with {:d}\n")
        sys.stderr.write(error.format(function_name, res))

def kill_process(process_name):
    for proc in psutil.process_iter():
        if proc.name() == process_name:
            proc.kill()
            return True
    return False

def restart_process(process_name):
    process_path = ""
    for proc in psutil.process_iter():
        if proc.name().lower() == f"{process_name}".lower():
            process_path = proc.exe()
            proc.kill()
            decky.logger.info(f"Killed process {process_name}")
        # else:
        #     decky.logger.info(f"Process {proc.name()} not {process_name}, skip")
    if len(process_path) == 0:
        decky.logger.info(f"Can't find process {process_name}")
        return False
    else:
        try:
            decky.logger.info(f"Restarting process {process_name} at {process_path}")
            subprocess.run([process_path], check=True, timeout=15, shell=True)
        except subprocess.CalledProcessError as e:
            decky.logger.info(f"Can't restart process at {process_path}")
            return False
        except FileNotFoundError:
            decky.logger.info(f"Executable at {process_path} not found")
            return False
        finally:
            decky.logger.info(f"Process {process_name} at {process_path} restarted")
        return True

def is_process_running(process_name):
    return process_name in (p.name() for p in psutil.process_iter())

def find_process_by_name(process_name) -> psutil.Process | None:
    for proc in psutil.process_iter():
        if proc.name().lower() == process_name.lower():
            return proc
    return None

def get_active_window():
    hwnd = win32gui.GetForegroundWindow()
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    if pid >= 0:
        try:
            proc = psutil.Process(pid)
            name = proc.name()
            exe = proc.exe()
            title = win32gui.GetWindowText(hwnd)
            # decky.logger.info(f"HWND: {hwnd}, PID: {pid}, Name: {name}, Path: {exe}, Title: {title}")
            return hwnd, pid, name, exe, title
        except NoSuchProcess:
            return 0, pid, "Not Found", "Not Found", "Not Found"
    else:
        return 0, 0, "Unknown", "Unknown", "Unknown"

def setup_hwinfo():
    decky.logger.info("[HWiNFO] Setting up")
    hwinfo_sensors_key_path = r"Software\HWiNFO64\Sensors"
    hwinfo_sensors_f_key_path = r"Software\HWiNFO64\Sensors\F000CCCC_0"
    hwinfo_sensors_custom_key_path = hwinfo_sensors_key_path + r"\Custom"
    hwinfo_sensors_custom_decky_key_path = hwinfo_sensors_custom_key_path + r"\Decky Windows Tools"
    hwinfo_sensors_custom_other0_path = hwinfo_sensors_custom_decky_key_path + r"\Other0"
    hwinfo_sensors_f_other0_path = hwinfo_sensors_f_key_path + r"\Other0"
    hwinfo_sensors_custom_other1_path = hwinfo_sensors_custom_decky_key_path + r"\Other1"
    hwinfo_sensors_f_other1_path = hwinfo_sensors_f_key_path + r"\Other1"
    hwinfo_sensors_custom_other2_path = hwinfo_sensors_custom_decky_key_path + r"\Other2"
    hwinfo_sensors_f_other2_path = hwinfo_sensors_f_key_path + r"\Other2"
    hwinfo_sensors_custom_other3_path = hwinfo_sensors_custom_decky_key_path + r"\Other3"
    hwinfo_sensors_f_other3_path = hwinfo_sensors_f_key_path + r"\Other3"
    hwinfo_sensors_custom_other4_path = hwinfo_sensors_custom_decky_key_path + r"\Other4"
    hwinfo_sensors_f_other4_path = hwinfo_sensors_f_key_path + r"\Other4"
    hwinfo_sensors_custom_other5_path = hwinfo_sensors_custom_decky_key_path + r"\Other5"
    hwinfo_sensors_f_other5_path = hwinfo_sensors_f_key_path + r"\Other5"
    hwinfo_sensors_custom_other6_path = hwinfo_sensors_custom_decky_key_path + r"\Other6"
    hwinfo_sensors_f_other6_path = hwinfo_sensors_f_key_path + r"\Other6"

    try:
        hwinfo_sensors_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, hwinfo_sensors_key_path, 0, winreg.KEY_READ | winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY)
    except FileNotFoundError:
        decky.logger.error("[HWInfo] Not installed")
        return
    
    restart_hwinfo = False
    try:
        enable_vsb, _ = winreg.QueryValueEx(hwinfo_sensors_key, "EnableVSB")
    except FileNotFoundError:
        winreg.SetValueEx(hwinfo_sensors_key, "EnableVSB", 0, winreg.REG_DWORD, 1)
        decky.logger.info("[HWInfo] Add and eanble VSB")
        enable_vsb = 1
        restart_hwinfo = True
    
    if enable_vsb != 1:
        winreg.SetValueEx(hwinfo_sensors_key, "EnableVSB", 0, winreg.REG_DWORD, 1)
        decky.logger.info("[HWInfo] Enable VSB")
        restart_hwinfo = True
    else:
        decky.logger.info("[HWInfo] VSB is already enabled")
    
    try:
        hwinfo_sensors_custom_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, hwinfo_sensors_custom_key_path, 0, winreg.KEY_READ | winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY)
    except FileNotFoundError:
        restart_hwinfo = True
        decky.logger.info("[HWInfo] Create custom sensors")
        hwinfo_sensors_custom_key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, hwinfo_sensors_custom_key_path, 0, winreg.KEY_READ | winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY)
    
    try:
        hwinfo_sensors_f_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, hwinfo_sensors_f_key_path, 0, winreg.KEY_READ | winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY)
    except FileNotFoundError:
        restart_hwinfo = True
        decky.logger.info("[HWInfo] Create custom F000CCCC_0 sensors")
        hwinfo_sensors_f_key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, hwinfo_sensors_f_key_path, 0, winreg.KEY_READ | winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY)

    # hwinfo_sensors_custom_decky_key
    try:
        hwinfo_sensors_custom_decky_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, hwinfo_sensors_custom_decky_key_path, 0, winreg.KEY_READ | winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY)
    except FileNotFoundError:
        restart_hwinfo = True
        decky.logger.info("[HWInfo] Create custom sensors for Decky Windows Tools")
        hwinfo_sensors_custom_decky_key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, hwinfo_sensors_custom_decky_key_path, 0, winreg.KEY_READ | winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY)
    
    try:
        hwinfo_sensors_custom_other0_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, hwinfo_sensors_custom_other0_path, 0, winreg.KEY_READ | winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY)
    except FileNotFoundError:
        restart_hwinfo = True
        decky.logger.info("[HWInfo] Add custom sensor 0 for Decky Windows Tools")
        hwinfo_sensors_custom_other0_key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, hwinfo_sensors_custom_other0_path, 0, winreg.KEY_READ | winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY)
        winreg.SetValueEx(hwinfo_sensors_custom_other0_key, "Name", 0, winreg.REG_SZ, "CPU Clock")
        winreg.SetValueEx(hwinfo_sensors_custom_other0_key, "Value", 0, winreg.REG_SZ, "\"Core Ratios\" * 100")
        winreg.SetValueEx(hwinfo_sensors_custom_other0_key, "Unit", 0, winreg.REG_SZ, "Mhz")
    
    try:
        hwinfo_sensors_f_other0_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, hwinfo_sensors_f_other0_path, 0, winreg.KEY_READ | winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY)
    except FileNotFoundError:
        restart_hwinfo = True
        decky.logger.info("[HWInfo] Add F000CCC0 0 for Decky Windows Tools")
        hwinfo_sensors_f_other0_key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, hwinfo_sensors_f_other0_path, 0, winreg.KEY_READ | winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY)
        winreg.SetValueEx(hwinfo_sensors_f_other0_key, "DecimalDigits", 0, winreg.REG_DWORD, 0)
        winreg.SetValueEx(hwinfo_sensors_f_other0_key, "ThousandsSep", 0, winreg.REG_DWORD, 0)
        winreg.SetValueEx(hwinfo_sensors_f_other0_key, "Color", 0, winreg.REG_DWORD, 0)
        winreg.SetValueEx(hwinfo_sensors_f_other0_key, "InVSB", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(hwinfo_sensors_f_other0_key, "VSBidx", 0, winreg.REG_DWORD, 0)
    
    try:
        hwinfo_sensors_custom_other1_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, hwinfo_sensors_custom_other1_path, 0, winreg.KEY_READ | winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY)
    except FileNotFoundError:
        restart_hwinfo = True
        decky.logger.info("[HWInfo] Add custom sensor 1 for Decky Windows Tools")
        hwinfo_sensors_custom_other1_key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, hwinfo_sensors_custom_other1_path, 0, winreg.KEY_READ | winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY)
        winreg.SetValueEx(hwinfo_sensors_custom_other1_key, "Name", 0, winreg.REG_SZ, "CPU Effective Clock")
        winreg.SetValueEx(hwinfo_sensors_custom_other1_key, "Value", 0, winreg.REG_SZ, "max(\"Zen5 Core 0 T0 Effective Clock\",\"Zen5 Core 1 T0 Effective Clock\",\"Zen5 Core 2 T0 Effective Clock\",\"Zen5 Core 3 T0 Effective Clock\",\"Zen5 Core 4 T0 Effective Clock\",\"Zen5 Core 5 T0 Effective Clock\",\"Zen5 Core 6 T0 Effective Clock\",\"Zen5 Core 7 T0 Effective Clock\")")
        winreg.SetValueEx(hwinfo_sensors_custom_other1_key, "Unit", 0, winreg.REG_SZ, "Mhz")

    try:
        hwinfo_sensors_f_other1_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, hwinfo_sensors_f_other1_path, 0, winreg.KEY_READ | winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY)
    except FileNotFoundError:
        restart_hwinfo = True
        decky.logger.info("[HWInfo] Add F000CCC0 1 for Decky Windows Tools")
        hwinfo_sensors_f_other1_key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, hwinfo_sensors_f_other1_path, 0, winreg.KEY_READ | winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY)
        winreg.SetValueEx(hwinfo_sensors_f_other1_key, "DecimalDigits", 0, winreg.REG_DWORD, 0)
        winreg.SetValueEx(hwinfo_sensors_f_other1_key, "ThousandsSep", 0, winreg.REG_DWORD, 0)
        winreg.SetValueEx(hwinfo_sensors_f_other1_key, "Color", 0, winreg.REG_DWORD, 0)
        winreg.SetValueEx(hwinfo_sensors_f_other1_key, "InVSB", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(hwinfo_sensors_f_other1_key, "VSBidx", 0, winreg.REG_DWORD, 1)

    try:
        hwinfo_sensors_custom_other2_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, hwinfo_sensors_custom_other2_path, 0, winreg.KEY_READ | winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY)
    except FileNotFoundError:
        restart_hwinfo = True
        decky.logger.info("[HWInfo] Add custom sensor 2 for Decky Windows Tools")
        hwinfo_sensors_custom_other2_key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, hwinfo_sensors_custom_other2_path, 0, winreg.KEY_READ | winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY)
        winreg.SetValueEx(hwinfo_sensors_custom_other2_key, "Name", 0, winreg.REG_SZ, "CPU Usage")
        winreg.SetValueEx(hwinfo_sensors_custom_other2_key, "Value", 0, winreg.REG_SZ, "\"Max CPU/Thread Usage\"")
        winreg.SetValueEx(hwinfo_sensors_custom_other2_key, "Unit", 0, winreg.REG_SZ, "%")

    try:
        hwinfo_sensors_f_other2_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, hwinfo_sensors_f_other2_path, 0, winreg.KEY_READ | winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY)
    except FileNotFoundError:
        restart_hwinfo = True
        decky.logger.info("[HWInfo] Add F000CCC0 2 for Decky Windows Tools")
        hwinfo_sensors_f_other2_key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, hwinfo_sensors_f_other2_path, 0, winreg.KEY_READ | winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY)
        winreg.SetValueEx(hwinfo_sensors_f_other2_key, "DecimalDigits", 0, winreg.REG_DWORD, 0)
        winreg.SetValueEx(hwinfo_sensors_f_other2_key, "ThousandsSep", 0, winreg.REG_DWORD, 0)
        winreg.SetValueEx(hwinfo_sensors_f_other2_key, "Color", 0, winreg.REG_DWORD, 0)
        winreg.SetValueEx(hwinfo_sensors_f_other2_key, "InVSB", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(hwinfo_sensors_f_other2_key, "VSBidx", 0, winreg.REG_DWORD, 2)

    try:
        hwinfo_sensors_custom_other3_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, hwinfo_sensors_custom_other3_path, 0, winreg.KEY_READ | winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY)
    except FileNotFoundError:
        restart_hwinfo = True
        decky.logger.info("[HWInfo] Add custom sensor 3 for Decky Windows Tools")
        hwinfo_sensors_custom_other3_key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, hwinfo_sensors_custom_other3_path, 0, winreg.KEY_READ | winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY)
        winreg.SetValueEx(hwinfo_sensors_custom_other3_key, "Name", 0, winreg.REG_SZ, "GPU Clock")
        winreg.SetValueEx(hwinfo_sensors_custom_other3_key, "Value", 0, winreg.REG_SZ, "\"GPU Clock\"")
        winreg.SetValueEx(hwinfo_sensors_custom_other3_key, "Unit", 0, winreg.REG_SZ, "Mhz")
    
    try:
        hwinfo_sensors_f_other3_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, hwinfo_sensors_f_other3_path, 0, winreg.KEY_READ | winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY)
    except FileNotFoundError:
        restart_hwinfo = True
        decky.logger.info("[HWInfo] Add F000CCC0 3 for Decky Windows Tools")
        hwinfo_sensors_f_other3_key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, hwinfo_sensors_f_other3_path, 0, winreg.KEY_READ | winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY)
        winreg.SetValueEx(hwinfo_sensors_f_other3_key, "DecimalDigits", 0, winreg.REG_DWORD, 0)
        winreg.SetValueEx(hwinfo_sensors_f_other3_key, "ThousandsSep", 0, winreg.REG_DWORD, 0)
        winreg.SetValueEx(hwinfo_sensors_f_other3_key, "Color", 0, winreg.REG_DWORD, 0)
        winreg.SetValueEx(hwinfo_sensors_f_other3_key, "InVSB", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(hwinfo_sensors_f_other3_key, "VSBidx", 0, winreg.REG_DWORD, 3)

    try:
        hwinfo_sensors_custom_other4_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, hwinfo_sensors_custom_other4_path, 0, winreg.KEY_READ | winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY)
    except FileNotFoundError:
        restart_hwinfo = True
        decky.logger.info("[HWInfo] Add custom sensor 4 for Decky Windows Tools")
        hwinfo_sensors_custom_other4_key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, hwinfo_sensors_custom_other4_path, 0, winreg.KEY_READ | winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY)
        winreg.SetValueEx(hwinfo_sensors_custom_other4_key, "Name", 0, winreg.REG_SZ, "GPU Effective Clock")
        winreg.SetValueEx(hwinfo_sensors_custom_other4_key, "Value", 0, winreg.REG_SZ, "\"GPU Clock (Effective)\"")
        winreg.SetValueEx(hwinfo_sensors_custom_other4_key, "Unit", 0, winreg.REG_SZ, "Mhz")

    try:
        hwinfo_sensors_f_other4_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, hwinfo_sensors_f_other4_path, 0, winreg.KEY_READ | winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY)
    except FileNotFoundError:
        restart_hwinfo = True
        decky.logger.info("[HWInfo] Add F000CCC0 4 for Decky Windows Tools")
        hwinfo_sensors_f_other4_key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, hwinfo_sensors_f_other4_path, 0, winreg.KEY_READ | winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY)
        winreg.SetValueEx(hwinfo_sensors_f_other4_key, "DecimalDigits", 0, winreg.REG_DWORD, 0)
        winreg.SetValueEx(hwinfo_sensors_f_other4_key, "ThousandsSep", 0, winreg.REG_DWORD, 0)
        winreg.SetValueEx(hwinfo_sensors_f_other4_key, "Color", 0, winreg.REG_DWORD, 0)
        winreg.SetValueEx(hwinfo_sensors_f_other4_key, "InVSB", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(hwinfo_sensors_f_other4_key, "VSBidx", 0, winreg.REG_DWORD, 4)

    try:
        hwinfo_sensors_custom_other5_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, hwinfo_sensors_custom_other5_path, 0, winreg.KEY_READ | winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY)
    except FileNotFoundError:
        restart_hwinfo = True
        decky.logger.info("[HWInfo] Add custom sensor 5 for Decky Windows Tools")
        hwinfo_sensors_custom_other5_key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, hwinfo_sensors_custom_other5_path, 0, winreg.KEY_READ | winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY)
        winreg.SetValueEx(hwinfo_sensors_custom_other5_key, "Name", 0, winreg.REG_SZ, "GPU Usage")
        winreg.SetValueEx(hwinfo_sensors_custom_other5_key, "Value", 0, winreg.REG_SZ, "\"GPU D3D Usage\"")
        winreg.SetValueEx(hwinfo_sensors_custom_other5_key, "Unit", 0, winreg.REG_SZ, "%")
    
    try:
        hwinfo_sensors_f_other5_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, hwinfo_sensors_f_other5_path, 0, winreg.KEY_READ | winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY)
    except FileNotFoundError:
        restart_hwinfo = True
        decky.logger.info("[HWInfo] Add F000CCC0 5 for Decky Windows Tools")
        hwinfo_sensors_f_other5_key= winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, hwinfo_sensors_f_other5_path, 0, winreg.KEY_READ | winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY)
        winreg.SetValueEx(hwinfo_sensors_f_other5_key, "DecimalDigits", 0, winreg.REG_DWORD, 0)
        winreg.SetValueEx(hwinfo_sensors_f_other5_key, "ThousandsSep", 0, winreg.REG_DWORD, 0)
        winreg.SetValueEx(hwinfo_sensors_f_other5_key, "Color", 0, winreg.REG_DWORD, 0)
        winreg.SetValueEx(hwinfo_sensors_f_other5_key, "InVSB", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(hwinfo_sensors_f_other5_key, "VSBidx", 0, winreg.REG_DWORD, 5)
    
    hwinfo_sensors_custom_other0_key.Close()
    hwinfo_sensors_custom_other1_key.Close()
    hwinfo_sensors_custom_other2_key.Close()
    hwinfo_sensors_custom_other3_key.Close()
    hwinfo_sensors_custom_other4_key.Close()
    hwinfo_sensors_custom_other5_key.Close()
    hwinfo_sensors_custom_decky_key.Close()
    hwinfo_sensors_custom_key.Close()
    hwinfo_sensors_key.Close()
    hwinfo_sensors_f_key.Close()
    hwinfo_sensors_f_other0_key.Close()
    hwinfo_sensors_f_other1_key.Close()
    hwinfo_sensors_f_other2_key.Close()
    hwinfo_sensors_f_other3_key.Close()
    hwinfo_sensors_f_other4_key.Close()
    hwinfo_sensors_f_other5_key.Close()

    is_hwinfo_running = is_process_running("HWiNFO64.EXE")

    if restart_hwinfo and is_hwinfo_running:
        restart_process("HWiNFO64.EXE")
    else:
        if is_hwinfo_running:
            decky.logger.info("[HWInfo] Correctly configred, no need to restart. It's running already")
        else:
            try:
                decky.logger.info("[HWInfo] Correctly configred, no need to restart. But it's not running. Trying to start it.")
                subprocess.run(["C:\Program Files\HWiNFO64\HWiNFO64.EXE"], check=True, timeout=15, shell=True)
                decky.logger.info("[HWInfo] HWiNFO started.")
            except subprocess.CalledProcessError as e:
                decky.logger.info("[HWInfo] Can't start HWiNFO. Make sure it's installed.")
            except FileNotFoundError:
                decky.logger.info("[HWInfo] HWiNFO not found at C:\Program Files\HWiNFO64\HWiNFO64.EXE. Make sure it's installed.")

# This is for determining game name based on the path.
unlikely_game_names = ["bin", "x64", "binaries", "win64"]

def find_game_name_from_path(game_path: str):
    steam_game_folder = "steamapps\\common\\"
    slash = "\\"
    # something like "D:\SteamLibrary\steamapps\common\BlackMythWukong\b1.exe"
    if steam_game_folder in game_path:
        start_index = game_path.index(steam_game_folder) + len(steam_game_folder)
        end_index = game_path.index(slash, start_index)
        return game_path[start_index:end_index]
    
    max_depth = 20
    path = game_path
    if path.lower().endswith(".exe"):
        path = os.path.dirname(game_path)
    game_name: str = ""
    while max_depth >= 0:
        game_name = os.path.basename(path)
        if game_name not in unlikely_game_names:
            return game_name
    return "Unknown Game"

lossless_scaling_modes = {
    "Auto": 0,
    "Custom": 1
}

lossless_scaling_fitmodes = {
    "AspectRatio": 0,
    "Fullscreen": 1
}

lossless_scaling_framegens = {
    "Off": 0,
    "LSFG3": 1,
    "LSFG2": 2,
    "LSFG1": 3
}

lossless_scaling_types = {
    "Off": 0,
    "LS1": 1,
    "FSR": 2,
    "NIS": 3,
    "SGSR": 4,
    "BCAS": 5,
    "Anime4K": 6,
    "xBR": 7,
    "SharpBilinear": 8,
    "Integer": 9,
    "NearestNeighbor": 10
}

lossless_scaling_lsfg3_mode1s = {
    "FIXED": 0,
    "ADAPTIVE": 1,
}

lossless_scaling_lsfg2_modes = {
    "X2": 0,
    "X3": 1,
    "X4": 1,
}

class TDP:
    tdp: int
    fps: list[int]

    def __init__(self, tdp: int, fps: int):
        self.tdp = tdp
        self.fps = list()
        self.fps.append(fps)

class Plugin:
    auto_tdp: bool = False
    tdps: list[TDP] = []
    target_fps: int = 60

    # FPS values
    UNKNOWN: int = -1
    BEST_RATIO: float = 1.0 # best FPS should equal to current refresh rate
    GOOD_RATIO: float = 11.0 / 12.0 # good FPS should be no less than current refresh rate times 11/12. For example, on a 60Hz screen, good FPS should be 55 or higher.
    BAD_RATIO: float = 10.0 / 12.0 # bad FPS is less than current refresh rate minus times 10/12. For example, on a 60Hz screen, bad FPS is 50 or lower.
    STABLE_NUM_RECORDED_FPS: int = 5

    # TDP values
    MIN_TDP: int = 4
    MAX_TDP: int = 32
    AVERAGE_TDP: int = 18

    # Misc
    SYSTEM_LOOP: int = 0
    NO_FPS_COUNT: int = 0
    IDLE_NO_FPS_NUM: int = 3

    # RTSS
    rtss_lib: CDLL
    rtss_overlay_lib: CDLL
    rtss_osd_visible_flag: int
    rtss_overlay_config_path: str
    # overlay_client: OverlayEditorClient

    # ADLX
    adlxHelper: ADLX.ADLXHelper = None
    adlxStatus: ADLX.ADLX_RESULT

    # Lossless Scaling
    LOSSLESS_SCALING_PATH: str = b"C:\Program Files (x86)\Steam\steamapps\common\Lossless Scaling\LosslessScaling.exe"
    LOSSLESS_SCALING_NAME: str = "LosslessScaling.exe"
    current_game_name: str = ""
    current_game_path: str = ""
    LOSSLESS_SCALING_SETTINGS_PATH: str = os.path.join(os.path.expandvars(r'%LOCALAPPDATA%'), "Lossless Scaling", "Settings.xml")

    def setup_rtss(self):
        # RTSS
        rtss_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Unwinder\RTSS", 0, winreg.KEY_READ)
        rtss_install_dir, _ = winreg.QueryValueEx(rtss_key, "InstallDir")
        winreg.CloseKey(rtss_key)
        self.rtss_lib = cdll.LoadLibrary(os.path.join(rtss_install_dir, "RTSSHooks64.dll"))
        self.rtss_osd_visible_flag = 1
        self.rtss_overlay_config_path = os.path.join(rtss_install_dir, "Plugins", "Client", "OverlayEditor.cfg")
        rtss_hotkey_config_path = os.path.join(rtss_install_dir, "Plugins", "Client", "HotkeyHandler.cfg")
        with open(rtss_hotkey_config_path) as f:
            lines = f.readlines()
        rtss_overlay_path = os.path.join(rtss_install_dir, "Plugins", "Client", "Overlays")
        for idx in range(1, 5):
            ovl_file = f"level_{idx}.ovl"
            ovl_target_path = os.path.join(rtss_overlay_path, ovl_file)
            if not os.path.exists(ovl_target_path):
                copyfile(os.path.join(decky.DECKY_PLUGIN_DIR, "bin", "overlays", ovl_file), ovl_target_path)
            
            # OVM1Hotkey
            hotkey_key_prefix = f"OVM{idx}Hotkey"
            hotkey_key_setting = f"OVM{idx}Hotkey=0003007{idx-1}"
            for line_idx, line in enumerate(lines):
                if line.startswith(hotkey_key_prefix):
                    lines[line_idx] = hotkey_key_setting + '\n'
                    break
            else:
                # not found
                lines.append(hotkey_key_setting + '\n')
            
            # OVM1Message
            hotkey_message_prefix = f"OVM{idx}Message"
            hotkey_message_setting = f"OVM{idx}Message=Load"
            for line_idx, line in enumerate(lines):
                if line.startswith(hotkey_message_prefix):
                    lines[line_idx] = hotkey_message_setting + '\n'
                    break
            else:
                # not found
                lines.append(hotkey_message_setting + '\n')
            
            # OVM1Params
            hotkey_params_prefix = f"OVM{idx}Params"
            hotkey_params_setting = f"OVM{idx}Params=level_{idx}.ovl"
            for line_idx, line in enumerate(lines):
                if line.startswith(hotkey_params_prefix):
                    lines[line_idx] = hotkey_params_setting + '\n'
                    break
            else:
                # not found
                lines.append(hotkey_params_setting + '\n')
            
            # OVM1Desc
            hotkey_desc_prefix = f"OVM{idx}Desc"
            hotkey_desc_setting = f"OVM{idx}Desc=Load overlay"
            for line_idx, line in enumerate(lines):
                if line.startswith(hotkey_desc_prefix):
                    lines[line_idx] = hotkey_desc_setting + '\n'
                    break
            else:
                # not found
                lines.append(hotkey_desc_setting + '\n')
        
        with open(rtss_hotkey_config_path, 'w') as f:
            f.writelines(lines)

        # self.overlay_client = OverlayEditorClient()
        # self.overlay_client.post_overlay_message("Load", "", "level_1.ovl")
        if not is_process_running("RTSS.exe"):
            try:
                subprocess.run([os.path.join(rtss_install_dir, "RTSS.exe")], check=True, timeout=10, shell=True)
            except subprocess.TimeoutExpired as e:
                decky.logger.info(f"RTSS startup timed out: {e}")
            except FileNotFoundError:
                decky.logger.info("RTSS executable not found. Please ensure RTSS is installed correctly.")  
            except subprocess.CalledProcessError as e:
                decky.logger.info(f"Error: Command '{e.cmd}' returned non-zero exit status {e.returncode}.")
        # else:
        #     restart_process("RTSS.exe")

    def get_flags(self):
        rtss_get_flags_func = self.rtss_lib.__getattr__("GetFlags")
        rtss_get_flags_func.argtypes = []
        rtss_get_flags_func.restype = c_ulong
        return rtss_get_flags_func()

    def set_flags(self, flag, value):
        rtss_set_flags_func = self.rtss_lib.__getattr__("SetFlags")
        rtss_set_flags_func.argtypes = [c_ulong, c_ulong]
        rtss_set_flags_func(~flag, value)
        # rtss_post_message_func = rtss_lib.__getattr__("PostMessage")
        # rtss_post_message_func.argtypes = [c_ulong, WPARAM, LPARAM]
        # rtss_post_message_func(0, WPARAM(0), LPARAM(0))

    def get_property(self, property_name):
        rtss_load_profile_func = self.rtss_lib.__getattr__("LoadProfile")
        rtss_load_profile_func.argtypes = [c_char_p]
        rtss_load_profile_func(b"")

        rtss_get_property_func = self.rtss_lib.__getattr__("GetProfileProperty")
        rtss_get_property_func.argtypes = [LPCSTR, c_void_p, DWORD]
        rtss_get_property_func.restype = BOOL
        
        dw_value = DWORD()
        dw_size = DWORD(sizeof(dw_value))
        success = rtss_get_property_func(property_name, byref(dw_value), dw_size)
        # if success:
        #     decky.logger.info(f"Property '{property_name.decode()}' = {dw_value.value}")
        # else:
        #     decky.logger.info(f"Failed to get property '{property_name.decode()}'")
        
        return dw_value.value if success else 0

    def set_property(self, property_name, value):
        rtss_load_profile_func = self.rtss_lib.__getattr__("LoadProfile")
        rtss_load_profile_func.argtypes = [c_char_p]
        rtss_load_profile_func(b"")

        rtss_set_property_func = self.rtss_lib.__getattr__("SetProfileProperty")
        rtss_set_property_func.argtypes = [LPCSTR, c_void_p, DWORD]
        rtss_set_property_func.restype = BOOL

        dw_value = DWORD(value)
        dw_size = DWORD(sizeof(dw_value))
        success = rtss_set_property_func(property_name, byref(dw_value), dw_size)

        rtss_save_profile_func = self.rtss_lib.__getattr__("SaveProfile")
        rtss_save_profile_func.argtypes = [c_char_p]
        rtss_save_profile_func(b"")

        rtss_update_profile_func = self.rtss_lib.__getattr__("UpdateProfiles")
        rtss_update_profile_func.argtypes = []
        rtss_update_profile_func()

    async def is_lossless_scaling_running(self):
        lossless_scaling_process = find_process_by_name(self.LOSSLESS_SCALING_NAME)
        if lossless_scaling_process is None:
            # decky.logger.info("Lossless Scaling is not running")
            return False
        else:
            # decky.logger.info("Lossless Scaling is running")
            return True
        
    async def find_lossless_scaling_profile_name(self, game_path: str):
        decky.logger.info(f"Find {game_path} in Lossless Scaling")
        tree = ET.parse(self.LOSSLESS_SCALING_SETTINGS_PATH)
        root = tree.getroot()
        game_profiles = root.find("GameProfiles")
        for element in game_profiles.iter("Profile"):
            path_element = element.find("Path")
            if path_element is None:
                continue
            if path_element.text.lower() == game_path.lower():
                decky.logger.info(f"Game at path {game_path} has profile in Lossless Scaling")
                return element.find("Title").text
        decky.logger.info(f"Game at path {game_path} doesn't have profile in Lossless Scaling")
        return ""

    async def get_lossless_scaling_profile_names(self):
        tree = ET.parse(self.LOSSLESS_SCALING_SETTINGS_PATH)
        root = tree.getroot()
        game_profiles = root.find("GameProfiles")
        config_names = []
        for element in game_profiles.iter("Profile"):
            config_names.append(element.find("Title").text)
        return config_names
    
    async def get_lossless_scaling_profile_by_name(self, game_name: str):
        tree = ET.parse(self.LOSSLESS_SCALING_SETTINGS_PATH)
        root = tree.getroot()
        game_profiles = root.find("GameProfiles")
        game_profile: ET.Element = None
        for element in game_profiles.iter("Profile"):
            if element.find("Title").text.lower() == game_name.lower():
                game_profile = element
                break
        if game_profile is None:
            decky.logger.info(f"Lossless Scaling profile for {game_name} not found")
            return False, 0, 0, 0, 0, 0
        auto_scale = True if game_profile.find("AutoScale").text.lower() == "true" else False
        scaling_mode_text = game_profile.find("ScalingMode").text
        try:
            scaling_mode = lossless_scaling_modes[scaling_mode_text]
        except KeyError:
            print(f"'{scaling_mode_text}' is not a valid Lossless Scaling mode?")
            scaling_mode = 0
        scaling_fit_mode_text = game_profile.find("ScalingFitMode").text
        try:
            scaling_fit_mode = lossless_scaling_fitmodes[scaling_fit_mode_text]
        except KeyError:
            print(f"'{scaling_fit_mode_text}' is not a valid Lossless Scaling fit mode?")
            scaling_fit_mode = 0
        frame_gen_text = game_profile.find("FrameGeneration").text
        try:
            frame_gen = lossless_scaling_framegens[frame_gen_text]
        except KeyError:
            print(f"'{frame_gen_text}' is not a valid Lossless Scaling frame gen?")
            frame_gen = 0
        
        auto_scale_delay_text = game_profile.find("AutoScaleDelay").text
        try:
            auto_scale_delay = int(auto_scale_delay_text)
        except ValueError:
            print(f"'{auto_scale_delay_text}' is not a valid integer for AutoScaleDelay")
            auto_scale_delay = 3
        
        lsfg3_mode1_text = game_profile.find("LSFG3Mode1").text
        try:
            lsfg3_mode1 = lossless_scaling_lsfg3_mode1s[lsfg3_mode1_text]
        except ValueError:
            print(f"'{lsfg3_mode1_text}' is not a valid integer for LSFG3Mode1")
            lsfg3_mode1 = 0

        lsfg2_mode_text = game_profile.find("LSFG2Mode").text
        try:
            lsfg2_mode = lossless_scaling_lsfg2_modes[lsfg2_mode_text]
        except ValueError:
            print(f"'{lsfg2_mode_text}' is not a valid integer for LSFG2Mode")
            lsfg2_mode = 0

        lsgf3_multiplier_text = game_profile.find("LSFG3Multiplier").text
        try:
            lsgf3_multiplier = int(lsgf3_multiplier_text)
        except ValueError:
            print(f"'{lsgf3_multiplier_text}' is not a valid integer for LSFG3Multiplier")
            lsgf3_multiplier = 2

        lsgf3_target_text = game_profile.find("LSFG3Target").text
        try:
            lsgf3_target = int(lsgf3_target_text)
        except ValueError:
            print(f"'{lsgf3_target_text}' is not a valid integer for LSFG3Target")
            lsgf3_target = 60

        lsfg_flow_scale_text = game_profile.find("LSFGFlowScale").text
        try:
            lsfg_flow_scale = int(lsfg_flow_scale_text)
        except ValueError:
            print(f"'{lsfg_flow_scale_text}' is not a valid integer for LSFGFlowScale")
            lsfg_flow_scale = 75

        lsfg_performance = True if game_profile.find("LSFGSize").text.lower() == "performance" else False
        
        # decky.logger.info(f"Lossless Scaling config for {game_name} is: auto_scale=\"{auto_scale}\" auto_scale_delay=\"{auto_scale_delay}\" frame_gen=\"{frame_gen}\"")
        draw_fps = True if game_profile.find("DrawFps").text.lower() == "true" else False
        return auto_scale, auto_scale_delay, scaling_mode, scaling_fit_mode, frame_gen, draw_fps, lsfg3_mode1, lsfg2_mode, lsgf3_multiplier, lsgf3_target, lsfg_flow_scale, lsfg_performance

    async def set_lossless_scaling_profile_by_name(self, game_name: str, config_name: str, config_value: str):
        tree = ET.parse(self.LOSSLESS_SCALING_SETTINGS_PATH)
        root = tree.getroot()
        game_profiles = root.find("GameProfiles")
        game_profile: ET.Element = None
        for element in game_profiles.iter("Profile"):
            if element.find("Title").text.lower() == game_name.lower():
                game_profile = element
                break
        if game_profile is None:
            decky.logger.info(f"Lossless Scaling profile for {game_name} not found")
            return
        game_profile.find(config_name).text = config_value
        tree.write(self.LOSSLESS_SCALING_SETTINGS_PATH, encoding='utf-8', xml_declaration=True)
        decky.logger.info(f"Set Lossless Scaling config for {game_name} {config_name} to {config_value}")

    async def add_lossless_scaling_profile(self, game_name: str, game_path: str):
        tree = ET.parse(self.LOSSLESS_SCALING_SETTINGS_PATH)
        root = tree.getroot()
        game_profiles: ET.Element = root.find("GameProfiles")
        default_profile: ET.Element = None
        for element in game_profiles.iter("Profile"):
            if element.find("Title").text.lower() == "default":
                default_profile = element
        if default_profile is None:
            decky.logger.info("No Default profile???")
            return False
        new_game_profile = copy.deepcopy(default_profile)
        if new_game_profile is None:
            decky.logger.info(f"Can't add profile {game_name}")
            return False
        new_game_profile.find("Title").text = game_name
        path_element = ET.Element("Path")
        path_element.text = game_path
        new_game_profile.insert(1, path_element)
        game_profiles.append(new_game_profile)
        ET.indent(tree, '  ')
        tree.write(self.LOSSLESS_SCALING_SETTINGS_PATH, encoding='utf-8', xml_declaration=True)
        decky.logger.info(f"Add Lossless Scaling profile for {game_name} at {game_path}")
        return True
    
    async def restart_lossless_scaling(self):
        lossless_scaling_running_process = find_process_by_name(self.LOSSLESS_SCALING_NAME)
        if lossless_scaling_running_process is not None:
            decky.logger.info("Lossless Scaling is running, restarting it")
            lossless_scaling_running_process.kill()
            await asyncio.sleep(1)
        decky.logger.info("Starting Lossless Scaling")
        try:
            subprocess.run([self.LOSSLESS_SCALING_PATH], check=True, timeout=1, shell=True)
            decky.logger.info("Lossless Scaling started successfully")
        except subprocess.TimeoutExpired as e:
            decky.logger.info(f"Lossless Scaling startup timed out: {e}")
        except FileNotFoundError:
            decky.logger.info("Lossless Scaling executable not found. Please ensure Lossless Scaling is installed correctly.")
        except subprocess.CalledProcessError as e:
            decky.logger.info(f"Error: Command '{e.cmd}' returned non-zero exit status {e.returncode}.")
        
        lossless_scaling_startup_timer = 0
        while lossless_scaling_startup_timer < 5:
            lossless_scaling_running_process = find_process_by_name(self.LOSSLESS_SCALING_NAME)
            if lossless_scaling_running_process is not None:
                decky.logger.info("Lossless Scaling started successfully")
                break
            else:
                decky.logger.info("Waiting for Lossless Scaling to start")
                await asyncio.sleep(0.5)
                lossless_scaling_startup_timer += 0.5
        lossless_scaling_close_window_timer = 0
        while lossless_scaling_close_window_timer < 5:
            window_handle = win32gui.FindWindow(None, "Lossless Scaling")
            if window_handle != 0:  # Check if the window was found
                win32gui.PostMessage(window_handle, win32con.WM_CLOSE, 0, 0)
                decky.logger.info("Lossless Scaling window closed")
                break
            else:
                decky.logger.info("Waiting for Lossless Scaling window")
                await asyncio.sleep(0.5)
                lossless_scaling_close_window_timer += 0.5
    
    async def get_current_game_info(self):
        # decky.logger.info(f"Get game: {self.current_game_name} at {self.current_game_path}")
        return self.current_game_name, self.current_game_path
    
    async def init_adlx(self, location: str):
        # Get ADLXHelp and ADLX initialization
        initialization_text = "initialized"
        if self.adlxHelper is not None:
            initialization_text = "re-initialized"
            self.adlxHelper.Terminate()
        self.adlxHelper = ADLX.ADLXHelper()
        self.adlxStatus = self.adlxHelper.Initialize()
        if self.adlxStatus == ADLX.ADLX_RESULT.ADLX_OK:
            decky.logger.info(f"ADLX {initialization_text} successfully from {location}")
        else:
            decky.logger.info(f"ADLX {initialization_text} failed from {location} with status: {self.adlxStatus}")
    
    async def deinit_adlx(self):
        # Terminate ADLX
        ret = self.adlxHelper.Terminate()
        decky.logger.info("ADLX Terminate ret is: {}".format(ret))

    def display_demo(self):
        if self.adlxStatus == ADLX.ADLX_RESULT.ADLX_OK:
            # Get system services
            system = self.adlxHelper.GetSystemServices()

            if system is not None:
                # Get display services
                displayService = system.GetDisplaysServices()

                if displayService is not None:
                    # Iterate through the display list
                    count = displayService.GetNumberOfDisplays()
                    decky.logger.info("display count: {}".format(count))
                    disList = displayService.GetDisplays()
                    if disList is not None:
                        for index, display in enumerate(disList):
                            if display is not None:
                                name = display.name()
                                type = display.type()
                                connectType = display.connectType()
                                mid = display.ManufacturerID()
                                edid = display.EDID()
                                h,v = display.resolution()
                                refreshRate = display.RefreshRate()
                                pclock = display.PixelClock()
                                scanType = display.ScanType()
                                id = display.UniqueId()
                                decky.logger.info("\nThe display [{}]:".format(index))
                                decky.logger.info("\tName: {}".format(name))
                                decky.logger.info("\tType: {}".format(type))
                                decky.logger.info("\tConnector type: {}".format(connectType))
                                decky.logger.info("\tManufacturer id: {}".format(mid))
                                decky.logger.info("\tEDID: {}".format(edid))
                                decky.logger.info("\tResolution:  h: {}  v: {}".format(h,v))
                                decky.logger.info("\tRefresh rate: {}".format(refreshRate))
                                decky.logger.info("\tPixel clock: {}".format(pclock))
                                decky.logger.info("\tScan type: {}".format(scanType))
                                decky.logger.info("\tUnique id: {}".format(id))
                                # Release display interface
                                del display

                        # Release displayList interface
                        del disList

                    # Release displayService interface
                    del displayService
    
    async def get_radeon_super_resolution(self):
        system = self.adlxHelper.GetSystemServices()
        threeDSettingsServices = system.Get3DSettingsServices()
        radeonSuperResolution = threeDSettingsServices.GetRadeonSuperResolution()
        # radeonSuperResolutionSupported = radeonSuperResolution.IsSupported()
        enabled = radeonSuperResolution.IsEnabled()
        decky.logger.info(f"Get Radeon Super Resolution: {enabled}")
        return enabled
    
    async def set_radeon_super_resolution(self, enabled: bool):
        system = self.adlxHelper.GetSystemServices()
        threeDSettingsServices = system.Get3DSettingsServices()
        radeonSuperResolution = threeDSettingsServices.GetRadeonSuperResolution()
        radeonSuperResolution.SetEnabled(enabled)
        decky.logger.info(f"Set Radeon Super Resolution: {enabled}")

    async def get_radeon_super_resolution_sharpness(self):
        system = self.adlxHelper.GetSystemServices()
        threeDSettingsServices = system.Get3DSettingsServices()
        radeonSuperResolution = threeDSettingsServices.GetRadeonSuperResolution()
        # radeonSuperResolutionSupported = radeonSuperResolution.IsSupported()
        sharpness = radeonSuperResolution.GetSharpness()
        decky.logger.info(f"Get Radeon Super Resolution Sharpness: {sharpness}")
        return sharpness
    
    async def set_radeon_super_resolution_sharpness(self, sharpness: int):
        system = self.adlxHelper.GetSystemServices()
        threeDSettingsServices = system.Get3DSettingsServices()
        radeonSuperResolution = threeDSettingsServices.GetRadeonSuperResolution()
        radeonSuperResolution.SetSharpness(sharpness)
        decky.logger.info(f"Set Radeon Super Resolution Sharpness: {sharpness}")

    async def get_amd_fluid_motion_frame(self):
        system = self.adlxHelper.GetSystemServices()
        threeDSettingsServices1 = system.Get3DSettingsServices1()
        amdFluidMotionFrame = threeDSettingsServices1.GetAMDFluidMotionFrame()
        # radeonSuperResolutionSupported = radeonSuperResolution.IsSupported()
        enabled = amdFluidMotionFrame.IsEnabled()
        decky.logger.info(f"Get AMD Fluid Motion Frame: {enabled}")
        return enabled
    
    async def set_amd_fluid_motion_frame(self, enabled: bool):
        system = self.adlxHelper.GetSystemServices()
        threeDSettingsServices1 = system.Get3DSettingsServices1()
        amdFluidMotionFrame = threeDSettingsServices1.GetAMDFluidMotionFrame()
        amdFluidMotionFrame.SetEnabled(enabled)
        decky.logger.info(f"Set AMD Fluid Motion Frame: {enabled}")

    async def get_radeon_anti_lag(self):
        system = self.adlxHelper.GetSystemServices()
        displayService = system.GetDisplaysServices()
        disList = displayService.GetDisplays()
        if disList is None:
            decky.logger.info("No displays found")
            return False
        gpu = disList[0].GetGPU()
        if gpu is None:
            decky.logger.info("No GPU found for the first display")
            return False
        threeDSettingsServices = system.Get3DSettingsServices()
        antiLag = threeDSettingsServices.GetAntiLag(gpu)
        enabled = antiLag.IsEnabled()
        decky.logger.info(f"Get Radeon Anti Lag: {enabled}")
        return enabled
    
    async def set_radeon_anti_lag(self, enabled: bool):
        system = self.adlxHelper.GetSystemServices()
        displayService = system.GetDisplaysServices()
        disList = displayService.GetDisplays()
        if disList is None:
            decky.logger.info("No displays found")
            return False
        gpu = disList[0].GetGPU()
        if gpu is None:
            decky.logger.info("No GPU found for the first display")
            return False
        threeDSettingsServices = system.Get3DSettingsServices()
        antiLag = threeDSettingsServices.GetAntiLag(gpu)
        antiLag.SetEnabled(enabled)
        decky.logger.info(f"Set Radeon Anti Lag: {enabled}")

    async def get_radeon_boost(self):
        system = self.adlxHelper.GetSystemServices()
        displayService = system.GetDisplaysServices()
        disList = displayService.GetDisplays()
        if disList is None:
            decky.logger.info("No displays found")
            return False
        gpu = disList[0].GetGPU()
        if gpu is None:
            decky.logger.info("No GPU found for the first display")
            return False
        threeDSettingsServices = system.Get3DSettingsServices()
        boost = threeDSettingsServices.GetBoost(gpu)
        enabled = boost.IsEnabled()
        decky.logger.info(f"Get Radeon Boost: {enabled}")
        return enabled
    
    async def set_radeon_boost(self, enabled: bool):
        system = self.adlxHelper.GetSystemServices()
        displayService = system.GetDisplaysServices()
        disList = displayService.GetDisplays()
        if disList is None:
            decky.logger.info("No displays found")
            return False
        gpu = disList[0].GetGPU()
        if gpu is None:
            decky.logger.info("No GPU found for the first display")
            return False
        threeDSettingsServices = system.Get3DSettingsServices()
        boost = threeDSettingsServices.GetBoost(gpu)
        boost.SetEnabled(enabled)
        decky.logger.info(f"Set Radeon Boost: {enabled}")

    async def get_radeon_chill(self):
        system = self.adlxHelper.GetSystemServices()
        displayService = system.GetDisplaysServices()
        disList = displayService.GetDisplays()
        if disList is None:
            decky.logger.info("No displays found")
            return False
        gpu = disList[0].GetGPU()
        if gpu is None:
            decky.logger.info("No GPU found for the first display")
            return False
        threeDSettingsServices = system.Get3DSettingsServices()
        chill = threeDSettingsServices.GetChill(gpu)
        enabled = chill.IsEnabled()
        decky.logger.info(f"Get Radeon Chill: {enabled}")
        return enabled
    
    async def set_radeon_chill(self, enabled: bool):
        system = self.adlxHelper.GetSystemServices()
        displayService = system.GetDisplaysServices()
        disList = displayService.GetDisplays()
        if disList is None:
            decky.logger.info("No displays found")
            return False
        gpu = disList[0].GetGPU()
        if gpu is None:
            decky.logger.info("No GPU found for the first display")
            return False
        threeDSettingsServices = system.Get3DSettingsServices()
        chill = threeDSettingsServices.GetChill(gpu)
        chill.SetEnabled(enabled)
        decky.logger.info(f"Set Radeon Chill: {enabled}")

    async def get_radeon_chill_min_fps(self):
        system = self.adlxHelper.GetSystemServices()
        displayService = system.GetDisplaysServices()
        disList = displayService.GetDisplays()
        if disList is None:
            decky.logger.info("No displays found")
            return False
        gpu = disList[0].GetGPU()
        if gpu is None:
            decky.logger.info("No GPU found for the first display")
            return False
        threeDSettingsServices = system.Get3DSettingsServices()
        chill = threeDSettingsServices.GetChill(gpu)
        min_fps = chill.GetMinFPS()
        decky.logger.info(f"Get Radeon Chill Min FPS: {min_fps}")
        return min_fps
    
    async def set_radeon_chill_min_fps(self, min_fps: int):
        system = self.adlxHelper.GetSystemServices()
        displayService = system.GetDisplaysServices()
        disList = displayService.GetDisplays()
        if disList is None:
            decky.logger.info("No displays found")
            return False
        gpu = disList[0].GetGPU()
        if gpu is None:
            decky.logger.info("No GPU found for the first display")
            return False
        threeDSettingsServices = system.Get3DSettingsServices()
        chill = threeDSettingsServices.GetChill(gpu)
        chill.SetMinFPS(min_fps)
        decky.logger.info(f"Set Radeon Chill Min FPS: {min_fps}")
    
    async def get_radeon_chill_max_fps(self):
        system = self.adlxHelper.GetSystemServices()
        displayService = system.GetDisplaysServices()
        disList = displayService.GetDisplays()
        if disList is None:
            decky.logger.info("No displays found")
            return False
        gpu = disList[0].GetGPU()
        if gpu is None:
            decky.logger.info("No GPU found for the first display")
            return False
        threeDSettingsServices = system.Get3DSettingsServices()
        chill = threeDSettingsServices.GetChill(gpu)
        max_fps = chill.GetMaxFPS()
        decky.logger.info(f"Get Radeon Chill Max FPS: {max_fps}")
        return max_fps
    
    async def set_radeon_chill_max_fps(self, max_fps: int):
        system = self.adlxHelper.GetSystemServices()
        displayService = system.GetDisplaysServices()
        disList = displayService.GetDisplays()
        if disList is None:
            decky.logger.info("No displays found")
            return False
        gpu = disList[0].GetGPU()
        if gpu is None:
            decky.logger.info("No GPU found for the first display")
            return False
        threeDSettingsServices = system.Get3DSettingsServices()
        chill = threeDSettingsServices.GetChill(gpu)
        chill.SetMaxFPS(max_fps)
        decky.logger.info(f"Set Radeon Chill Max FPS: {max_fps}")

    async def get_gpu_scaling(self):
        system = self.adlxHelper.GetSystemServices()
        displayService = system.GetDisplaysServices()
        disList = displayService.GetDisplays()
        if disList is None:
            decky.logger.info("Get GPU Scaling: No displays found")
            return False
        display = disList[0]
        if display is None:
            decky.logger.info("Get GPU Scaling: No display found???")
            return False
        gpuScaling = displayService.GetGPUScaling(display)
        enabled = gpuScaling.IsEnabled()
        decky.logger.info(f"Get GPU Scaling: {enabled}")
        return enabled
    
    async def set_gpu_scaling(self, enabled: bool):
        system = self.adlxHelper.GetSystemServices()
        displayService = system.GetDisplaysServices()
        disList = displayService.GetDisplays()
        if disList is None:
            decky.logger.info("Set GPU Scaling: No displays found")
            return False
        display = disList[0]
        if display is None:
            decky.logger.info("Set GPU Scaling: No display found???")
            return False
        gpuScaling = displayService.GetGPUScaling(display)
        decky.logger.info(f"Set GPU Scaling: {enabled}")
        gpuScaling.SetEnabled(enabled)
    
    async def get_scaling_mode(self):
        system = self.adlxHelper.GetSystemServices()
        displayService = system.GetDisplaysServices()
        disList = displayService.GetDisplays()
        if disList is None:
            decky.logger.info("No displays found")
            return False
        display = disList[0]
        if display is None:
            decky.logger.info("No display found???")
            return False
        scalingMode = displayService.GetScalingMode(display)
        mode = scalingMode.GetMode()
        decky.logger.info("Current scaling mode: {}".format(mode))
        if mode == ADLX.ADLX_SCALE_MODE.PRESERVE_ASPECT_RATIO:
            return 0
        elif mode == ADLX.ADLX_SCALE_MODE.FULL_PANEL:
            return 1
        elif mode == ADLX.ADLX_SCALE_MODE.CENTERED:
            return 2
        else:
            decky.logger.info("Unknown scaling mode: {}".format(mode))
            return 0
    
    async def set_scaling_mode(self, mode: int):
        system = self.adlxHelper.GetSystemServices()
        displayService = system.GetDisplaysServices()
        disList = displayService.GetDisplays()
        if disList is None:
            decky.logger.info("No displays found")
            return False
        display = disList[0]
        if display is None:
            decky.logger.info("No display found???")
            return False
        scalingMode = displayService.GetScalingMode(display)
        if mode == 0:
            decky.logger.info("Set Scaling Mode: PRESERVE_ASPECT_RATIO")
            scalingMode.SetMode(ADLX.ADLX_SCALE_MODE.PRESERVE_ASPECT_RATIO)
        elif mode == 1:
            decky.logger.info("Set Scaling Mode: FULL_PANEL")
            scalingMode.SetMode(ADLX.ADLX_SCALE_MODE.FULL_PANEL)
        elif mode == 2:
            decky.logger.info("Set Scaling Mode: CENTERED")
            scalingMode.SetMode(ADLX.ADLX_SCALE_MODE.CENTERED)
        else:
            decky.logger.info("Set Scaling Mode: Unknown mode \"{}\"".format(mode))
    
    async def get_integer_scaling(self):
        system = self.adlxHelper.GetSystemServices()
        displayService = system.GetDisplaysServices()
        disList = displayService.GetDisplays()
        if disList is None:
            decky.logger.info("No displays found")
            return False
        display = disList[0]
        if display is None:
            decky.logger.info("No display found???")
            return False
        integerScaling = displayService.GetIntegerScaling(display)
        enabled = integerScaling.IsEnabled()
        decky.logger.info(f"Get Integer Scaling: {enabled}")
        return enabled
    
    async def set_integer_scaling(self, enabled: bool):
        system = self.adlxHelper.GetSystemServices()
        displayService = system.GetDisplaysServices()
        disList = displayService.GetDisplays()
        if disList is None:
            decky.logger.info("No displays found")
            return False
        display = disList[0]
        if display is None:
            decky.logger.info("No display found???")
            return False
        integerScaling = displayService.GetIntegerScaling(display)
        integerScaling.SetEnabled(enabled)
        decky.logger.info(f"Set Integer Scaling: {enabled}")

    def record_fps(self, current_tdp, fps):
        if len(self.tdps) == 0:
            self.tdps.append(TDP(current_tdp, fps))
            return
        else:
            added = False
            for idx, tdp in enumerate(self.tdps):
                if tdp.tdp == current_tdp:
                    if len(self.tdps[idx].fps) >= self.STABLE_NUM_RECORDED_FPS:
                        self.tdps[idx].fps.pop(0)
                    self.tdps[idx].fps.append(fps)
                    added = True
                    break
                else:
                    if tdp.tdp < current_tdp:
                        self.tdps.insert(idx, TDP(current_tdp, fps))
                        added = True
                        break
            if not added:
                self.tdps.append(TDP(current_tdp, fps))
        
        tdps_debug = ""
        for idx, tdp in enumerate(self.tdps):
            fps_debug = ""
            for idx2, fps in enumerate(tdp.fps):
                fps_debug = f"{fps}" if idx2 == 0 else f"{fps_debug}, {fps}"
            tdps_debug = f"{tdp.tdp}=[{fps_debug}]" if idx == 0 else f"{tdps_debug}, {tdp.tdp}=[{fps_debug}]"
        decky.logger.info(f"FPSes: [{tdps_debug}]")

    def find_recorded_fps(self, current_tdp):
        for tdp in self.tdps:
            if tdp.tdp == current_tdp:
                return sum(tdp.fps) / len(tdp.fps) if len(tdp.fps) >= self.STABLE_NUM_RECORDED_FPS else self.UNKNOWN
        return self.UNKNOWN
    
    def clear_lower_tdp(self, current_tdp):
        indices_to_remove = []
        for idx, tdp in enumerate(self.tdps):
            if tdp.tdp < current_tdp:
                indices_to_remove.append(idx)
        indices_to_remove = sorted(indices_to_remove, key=int, reverse=True)
        for index_to_remove in indices_to_remove:
            self.tdps.pop(index_to_remove)
    
    def find_recorded_fps_count(self, current_tdp):
        for tdp in self.tdps:
            if tdp.tdp == current_tdp:
                return len(tdp.fps)
        return 0
    
    def num_recorded_fps(self):
        return len(self.tdps)
        
    def clear_fps(self):
        self.tdps.clear()

    async def get_min_tdp(self):
        return self.MIN_TDP
    
    async def get_max_tdp(self):
        return self.MAX_TDP

    async def get_auto_tdp(self):
        return self.auto_tdp
    
    async def set_auto_tdp(self, enable_auto_tdp):
        self.auto_tdp = enable_auto_tdp

    async def get_fps(self, process_id):
        black_list_apps = ["rustdesk"]
        global last_dwTime0
        # Map shared memory
        mmap_size = 4485160
        mm = mmap.mmap(0, mmap_size, 'RTSSSharedMemoryV2')
        
        # Read header (first 36 bytes)
        hdr = mm[0:36]
        (dwSignature, dwVersion, dwAppEntrySize, dwAppArrOffset,
        dwAppArrSize, dwOSDEntrySize, dwOSDArrOffset,
        dwOSDArrSize, dwOSDFrame) = struct.unpack('4sLLLLLLLL', hdr)
        
        # Adjust mmap size if needed
        required = dwAppArrOffset + dwAppArrSize * dwAppEntrySize# + 4000
        if mmap_size < required:
            # decky.logger.info(f'Adjusting RTSS mm size: {mmap_size} -> {required}')
            mm = mmap.mmap(0, required, 'RTSSSharedMemoryV2')
        
        # Validate signature & version
        if dwSignature[::-1] not in (b'RTSS', b'SSTR') or dwVersion < 0x00020000:
            decky.logger.info(f'Invalid RTSS signature/version: {dwSignature} / {dwVersion:x}')
            return None
        
        # decky.logger.info(f'RTSS Shared Memory: Signature={dwSignature} Version={dwVersion:x} AppEntrySize={dwAppEntrySize} AppArrOffset={dwAppArrOffset} AppArrSize={dwAppArrSize} OSDEntrySize={dwOSDEntrySize} OSDArrOffset={dwOSDArrOffset} OSDArrSize={dwOSDArrSize} OSDFrame={dwOSDFrame}')
    
        found_fps = 0
        found_app_name = ""
        highest_fps = 0
        highest_app_process_id = 0
        highest_app_name = ""
        
        # --- FPS loop (existing code) ---
        for dwEntry in range(dwAppArrSize):
            off = dwAppArrOffset + dwEntry * dwAppEntrySize
            stump = mm[off:off + 6*4 + 260]
            if len(stump) < struct.calcsize('L260sLLLLL'):
                continue
            pid, raw_name, flags, t0, t1, frames, ft = struct.unpack('L260sLLLLL', stump)
            if pid == 0:
                continue
            # decky.logger.info(f'[FPS] Pid={pid} RawName={raw_name[:60]} flags={flags:x} t0={t0} t1={t1} frames={frames} ft={ft}')
            if t0 > 0 and t1 > 0 and frames > 0:
                last_t0 = last_dwTime0s.get(pid)
                if t0 != last_t0:
                    app_fps = 1000 * frames / (t1 - t0)
                    raw_app_name = raw_name.decode('utf-8').rstrip('\x00')
                    black_listed = [black_list_app for black_list_app in black_list_apps if black_list_app.lower() in raw_app_name.lower()]
                    if len(black_listed):
                        #decky.logger.info(f'Ignore {raw_app_name} ({pid}): {app_fps:.1f}')
                        continue
                    if pid == process_id:
                        found_fps = app_fps
                        found_app_name = raw_app_name
                    if app_fps > highest_fps:
                        highest_fps = app_fps
                        highest_app_process_id = pid
                        highest_app_name = raw_app_name
                    decky.logger.info(f'[FPS] {raw_app_name} ({pid}): {app_fps:.1f}')
                    last_dwTime0s[pid] = t0
    
        # --- GPU clock from OSD entries ---
        # for i in range(dwOSDArrSize):
        #     off = dwOSDArrOffset + i * dwOSDEntrySize
        #     stump = mm[off:off + 256 + 256 + 4096]
        #     if len(stump) < struct.calcsize('256s256s4096s'):
        #         decky.logger.info(f'[GPU] OSD entry {i} too short: {len(stump)} bytes')
        #         continue
        #     osd, osdOwner, osdEx = struct.unpack('256s256s4096s', stump)
            
        #     decky.logger.info(f'[GPU] OSD entry: osd="{osd}" osdOwner={osdOwner} osdEx="{osdEx[:60]}"')
        
        # decky.logger.info(f"Get FPS: {fps} from {app_name} in {dwAppArrSize} apps")
        if found_fps > 0:
            return round(found_fps), process_id, found_app_name
        else:
            return round(highest_fps), highest_app_process_id, highest_app_name
    
    # async def get_cpu_clock_old(self):
    #     mmap_size = 44
    #     mm = mmap.mmap(0, mmap_size, 'Global\\HWiNFO_SENS_SM2')
        
    #     # Read header (first 44 bytes)
    #     hdr = mm[0:40]
    #     (macgic, version, version2, last_update,
    #     sensor_section_offset, sensor_element_size, sensor_element_count,
    #     entry_section_offset, entry_element_size, entry_element_count) = struct.unpack('4sLLLLLLLLL', hdr)
    #     decky.logger.info(f'HWiNFO Shared Memory: Magic={macgic} Version={version:x} Version2={version2:x} LastUpdate={last_update} SensorSectionOffset={sensor_section_offset} SensorElementSize={sensor_element_size} SensorElementCount={sensor_element_count} EntrySectionOffset={entry_section_offset} EntryElementSize={entry_element_size} EntryElementCount={entry_element_count}')
    #     # total_max_size = mmap_size + sensor_section_offset + sensor_element_size * sensor_element_count
    #     # total_max_size = mmap_size + entry_section_offset + entry_element_size * entry_element_count
    #     sensor_size = sensor_section_offset + sensor_element_size * sensor_element_count
    #     sentry_size = entry_section_offset + entry_element_size * entry_element_count
    #     total_max_size = mmap_size + sensor_size + sentry_size
        
    #     if total_max_size > mm.size():
    #         decky.logger.info(f'Adjusting HWiNFO mm size: {mm.size()} -> {total_max_size}')
    #         mm = mmap.mmap(0, total_max_size, 'Global\\HWiNFO_SENS_SM2')
    #     # for sensor_element in range(sensor_element_count):
    #     #     off = sensor_section_offset + sensor_element * sensor_element_size
    #     #     stump = mm[off:off + 4 + 4 + 128 + 128]
    #     #     if len(stump) < struct.calcsize('LL128s128s'):
    #     #         continue
    #     #     id, instance, name_original, name_user = struct.unpack('LL128s128s', stump)
    #     #     name_original = name_original.decode('utf-8', errors='ignore')
    #     #     name_user = name_user.decode('utf-8', errors='ignore')
    #     #     decky.logger.info(f'[CPU] Sensor Element {sensor_element}: ID={id} Instance={instance} NameOriginal="{name_original}" NameUser="{name_user}"')
        
    #     for entry_element_index in range(entry_element_count):
    #         decky.logger.info(f'[CPU] Entry Element {entry_element_index}')
    #         if entry_element_index <= 7:
    #             entry_element_size2 = 4 + 4 + 4 + 128 + 128
    #             entry_element_format = '<LLL128s128s'
    #         else:
    #             entry_element_size2 = 4 + 4 + 4 + 128 + 16 + 8 + 8 + 8 + 8 + 128
    #             entry_element_format = '<LLL128s16sdddd128s'
    #         off = entry_section_offset + entry_element_index * entry_element_size2
    #         stump = mm[off:off + entry_element_size2]
    #         if len(stump) < struct.calcsize(entry_element_format):
    #             decky.logger.info(f'[CPU] Entry Element {entry_element_index} too short: {len(stump)} bytes, need {struct.calcsize(entry_element_format)} bytes')
    #             continue
    #         if entry_element_index <= 7:
    #             type, sensor_index, id2, name_original2, name_user2 = struct.unpack(entry_element_format, stump)
    #             unit = b'None'
    #             value = -1
    #             value_min = -1
    #             value_max = -1
    #             value_avg = -1
    #         else:
    #             type, sensor_index, id2, unit, name_original2, value, value_min, value_max, value_avg, name_user2 = struct.unpack(entry_element_format, stump)
    #             value_min = 1
    #             value_max = 1
    #             value_avg = 1
    #         name_original2 = name_original2.decode('utf-8', errors='ignore')
    #         name_user2 = name_user2.decode('utf-8', errors='ignore')
    #         unit = unit.decode('mbcs', errors='ignore')
    #         decky.logger.info(f'[CPU] Type={type} SensorIndex={sensor_index} ID2={id2}\nNameOriginal="{name_original2}"\nNameUser="{name_user2}"\nUnit="{unit}"\nValue={value}')

    #     return 1000
    async def get_hwinfo_sensors(self):
        cpu_clock = 1000
        cpu_effective_clock = 500
        cpu_usage = 50
        gpu_clock = 800
        gpu_effective_clock = 200
        gpu_usage = 50
        hwinfo_vsb_key_path = r"Software\HWiNFO64\VSB"
        try:
            hwinfo_vsb_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, hwinfo_vsb_key_path, 0, winreg.KEY_READ | winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY)
        except FileNotFoundError:
            decky.logger.info("[HWInfo] Not installed or running")
            return cpu_clock, cpu_effective_clock, cpu_usage, gpu_clock, gpu_effective_clock, gpu_usage
        
        try:
            value0, _ = winreg.QueryValueEx(hwinfo_vsb_key, "Value0")
            cpu_clock_str = str(value0)
            cpu_clock_str = cpu_clock_str.replace(" Mhz", "")
            try:
                cpu_clock = int(cpu_clock_str)
                # decky.logger.info(f"Get CPU clock: {cpu_clock}")
            except ValueError:
                decky.logger.info(f"Get CPU clock: Can't convert {cpu_clock_str} to int")
        except FileNotFoundError:
            decky.logger.info("[HWInfo] VSB Value0 for CPU Clock not configured")
        
        try:
            value1, _ = winreg.QueryValueEx(hwinfo_vsb_key, "Value1")
            cpu_effective_clock_str = str(value1)
            cpu_effective_clock_str = cpu_effective_clock_str.replace(" Mhz", "")
            try:
                cpu_effective_clock = int(cpu_effective_clock_str)
                # decky.logger.info(f"Get CPU effective clock: {cpu_effective_clock}")
            except ValueError:
                decky.logger.info(f"Get CPU effective clock: Can't convert {cpu_effective_clock_str} to int")
        except FileNotFoundError:
            decky.logger.info("[HWInfo] VSB Value1 for CPU Effective Clock not configured")

        try:
            value2, _ = winreg.QueryValueEx(hwinfo_vsb_key, "Value2")
            cpu_usage_str = str(value2)
            cpu_usage_str = cpu_usage_str.replace(" %", "")
            try:
                cpu_usage = int(cpu_usage_str)
                # decky.logger.info(f"Get CPU usage: {cpu_usage}")
            except ValueError:
                decky.logger.info(f"Get CPU usage: Can't convert {cpu_usage_str} to int")
        except FileNotFoundError:
            decky.logger.info("[HWInfo] VSB Value2 for CPU usage not configured")
        
        try:
            value3, _ = winreg.QueryValueEx(hwinfo_vsb_key, "Value3")
            gpu_clock_str = str(value3)
            gpu_clock_str = gpu_clock_str.replace(" Mhz", "")
            try:
                gpu_clock = int(gpu_clock_str)
                # decky.logger.info(f"Get GPU clock: {gpu_clock}")
            except ValueError:
                decky.logger.info(f"Get GPU clock: Can't convert {gpu_clock_str} to int")
        except FileNotFoundError:
            decky.logger.info("[HWInfo] VSB Value3 for GPU Clock not configured")
        
        try:
            value4, _ = winreg.QueryValueEx(hwinfo_vsb_key, "Value4")
            gpu_effective_clock_str = str(value4)
            gpu_effective_clock_str = gpu_effective_clock_str.replace(" Mhz", "")
            try:
                gpu_effective_clock = int(gpu_effective_clock_str)
                # decky.logger.info(f"Get GPU effective clock: {gpu_effective_clock}")
            except ValueError:
                decky.logger.info(f"Get GPU effective clock: Can't convert {gpu_effective_clock_str} to int")
        except FileNotFoundError:
            decky.logger.info("[HWInfo] VSB Value4 for GPU Effective Clock not configured")

        try:
            value5, _ = winreg.QueryValueEx(hwinfo_vsb_key, "Value5")
            gpu_usage_str = str(value5)
            gpu_usage_str = gpu_usage_str.replace(" %", "")
            try:
                gpu_usage = int(gpu_usage_str)
                # decky.logger.info(f"Get GPU usage: {gpu_usage}")
            except ValueError:
                decky.logger.info(f"Get GPU usage: Can't convert {gpu_usage_str} to int")
        except FileNotFoundError:
            decky.logger.info("[HWInfo] VSB Value5 for GPU usage not configured")

        return cpu_clock, cpu_effective_clock, cpu_usage, gpu_clock, gpu_effective_clock, gpu_usage
    
    # A normal method. It can be called from the TypeScript side using @decky/api.
    async def add(self, left: int, right: int) -> int:
        return left + right

    async def sync_ryzen(self):
        await asyncio.sleep(15)
        # Passing through a bunch of random data, just as an example
        max_tdp = determine("slow_limit")
        decky.logger.info(f"Sync TDP: {max_tdp} W")
        await decky.emit("tdp_event", "max_tdp", max_tdp)

    # Asyncio-compatible long-running code, executed in a task when the plugin is loaded
    async def _main(self):
        self.loop = asyncio.get_event_loop()
        setup_hwinfo()
        self.setup_rtss()
        await self.init_adlx("_main")
        # self.display_demo()

    # Function called first during the unload process, utilize this to handle your plugin being stopped, but not
    # completely removed
    async def _unload(self):
        decky.logger.info("Goodnight World!")
        await self.deinit_adlx()
        pass

    # Function called after `_unload` during uninstall, utilize this to clean up processes and other remnants of your
    # plugin that may remain on the system
    async def _uninstall(self):
        decky.logger.info("Goodbye World!")
        pass

    async def start_syncing_ryzen(self):
        self.loop.create_task(self.sync_ryzen())

    # def subprocess_run_hidden(command, **kwargs):
    #     if os.name == 'nt':
    #         startupinfo = subprocess.STARTUPINFO()
    #         startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    #         startupinfo.wShowWindow = subprocess.SW_HIDE
    #         kwargs['startupinfo'] = startupinfo
    #     else:
    #         decky.logger.warning("Subprocess run hidden is only implemented for Windows.")
    #     return subprocess.run(command, **kwargs)

    async def get_volume(self):
        speaker_devices = AudioUtilities.GetSpeakers()
        speaker_interface = speaker_devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume_info = speaker_interface.QueryInterface(IAudioEndpointVolume)
        volume = round(volume_info.GetMasterVolumeLevelScalar() * 100)
        #decky.logger.info(f"Get GetMute: {volume_info.GetMute()}")
        decky.logger.info(f"Get volume: {volume}")
        return volume

    async def set_volume(self, volume: int):
        speaker_devices = AudioUtilities.GetSpeakers()
        speaker_interface = speaker_devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume_info = speaker_interface.QueryInterface(IAudioEndpointVolume)
        volume_info.SetMasterVolumeLevelScalar(volume / 100.0, None)

        decky.logger.info(f"Set volumne: {volume}")

    async def get_muted(self):
        speaker_devices = AudioUtilities.GetSpeakers()
        speaker_interface = speaker_devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume_info = speaker_interface.QueryInterface(IAudioEndpointVolume)
        mute = volume_info.GetMute()
        decky.logger.info(f"Get mute: {mute}")
        return mute
    
    async def set_muted(self, mute: bool):
        speaker_devices = AudioUtilities.GetSpeakers()
        speaker_interface = speaker_devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume_info = speaker_interface.QueryInterface(IAudioEndpointVolume)
        volume_info.SetMute(mute, None)

        decky.logger.info(f"Set mute: {mute}")

    async def get_brightness(self):
        try:
            brightness = sbc.get_brightness(display=0)[0]
        except Exception as e:
            brightness = 100
            decky.logger.info(f"Can't get brightness {e}")

        decky.logger.info(f"Get brightness: {brightness}")
        return brightness

    async def set_brightness(self, brightness: int):
        try:
            sbc.set_brightness(brightness, display=0)
        except Exception as e:
            decky.logger.info(f"Can't set brightness {e}")

        decky.logger.info(f"Set brightness to {brightness}")

    async def get_osd(self):
        flags = self.get_flags()
        overlay_enabled = flags & self.rtss_osd_visible_flag
        if overlay_enabled == 0:
            osd = 0
        else:
            if not os.path.exists(self.rtss_overlay_config_path):
                decky.logger.info("OverlayEditor.cfg not found at:", self.rtss_overlay_config_path)
                osd = 1
            else:
                try:
                    found = False
                    with open(self.rtss_overlay_config_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            match = re.match(r"\s*Layout=level_(\d+)\.ovl", line)
                            if match:
                                found = True
                                osd = int(match.group(1))
                                break
                    if not found:
                        decky.logger.info("Layout line not found in OverlayEditor.cfg, defaulting to 1")
                        osd = 1
                except Exception as e:
                    decky.logger.info("Error reading config file:", e)
                    osd = 1
        
        decky.logger.info(f"Get osd: {osd} ({overlay_enabled})")

        return osd
    
    async def set_osd(self, value: int):
        enabled = 0 if value == 0 else 1
        self.set_flags(self.rtss_osd_visible_flag, enabled)
        if value == 1:
            keyboard.send('ctrl+shift+f1')
        elif value == 2:
            keyboard.send('ctrl+shift+f2')
        elif value == 3:
            keyboard.send('ctrl+shift+f3')
        elif value == 4:
            keyboard.send('ctrl+shift+f4')
        # self.overlay_client.post_overlay_message("Load", "", f"level_{value}.ovl")
        
        # Update the overlay configuration file
        if not os.path.exists(self.rtss_overlay_config_path):
            decky.logger.info("OverlayEditor.cfg not found at:", self.rtss_overlay_config_path)
            with open(self.rtss_overlay_config_path, 'w') as f:
                pass  # creates an empty file
        
        try:
            # Read all lines from the config file
            with open(self.rtss_overlay_config_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Replace the Layout line
            updated_lines = []
            layout_found = False
            for line in lines:
                if line.strip().startswith("Layout="):
                    updated_lines.append(f"Layout=level_{value}.ovl\n")
                    layout_found = True
                else:
                    updated_lines.append(line)

            # If Layout line was not found, optionally add it
            if not layout_found:
                updated_lines.append(f"Layout=level_{value}.ovl\n")

            # Write back the updated content
            with open(self.rtss_overlay_config_path, 'w', encoding='utf-8') as f:
                f.writelines(updated_lines)
        except Exception as e:
            decky.logger.info("Error updating config file:", e)
        decky.logger.info(f"Set osd: {value}")

    async def get_osd_size(self):
        osd_size = self.get_property(b"ZoomRatio")
        
        decky.logger.info(f"Get osd size: {osd_size}")
        return osd_size
    
    async def set_osd_size(self, value: int):
        self.set_property(b"ZoomRatio", value)

        decky.logger.info(f"Set osd size: {value}")

    async def get_tdp_limit(self, print_log: bool):
        max_tdp = determine("slow_limit")
        if print_log:
            decky.logger.info(f"Get max tdp: {max_tdp} W")
        return max_tdp

    async def set_tdp_limit(self, value: int):
        adjust("stapm_limit", value * 1000)
        adjust("fast_limit", value * 1000)
        adjust("slow_limit", value * 1000)
        adjust("apu_slow_limit", value * 1000)
        decky.logger.info(f"Set TDP limit: {value * 1000} mW")

    async def get_gpu_clock_limit(self):
        gpu_clock = determine("gfx_clk")
        decky.logger.info(f"Get gpu clock: {gpu_clock} MHz")
        if gpu_clock < 800:
            return 800
        return gpu_clock

    async def set_gpu_clock_limit(self, value: int):
        adjust("gfx_clk", value)
        decky.logger.info(f"Set gpu clock: {value} MHz")

    async def get_refresh_rates(self):
        try:
            # Get primary display device
            dev = win32api.EnumDisplayDevices(None, 0)
            dev_name = dev.DeviceName

            rates = set()
            mode_num = 0
            common_refresh_rates = [40, 45, 60, 75, 90, 120, 144, 165, 240, 300]

            while True:
                try:
                    dm = win32api.EnumDisplaySettings(dev_name, mode_num)
                except Exception:
                    break
                freq = dm.DisplayFrequency
                if freq in common_refresh_rates:
                    rates.add(freq)
                mode_num += 1
            
            decky.logger.info(f"Found {len(rates)} supported refresh rates of the screen")
            return sorted(rates)
        except Exception as e:
            decky.logger.info(f"Can't get available refresh rates {e}")
            return [60]

    async def get_refresh_rate(self):
        try:
            dev = win32api.EnumDisplayDevices(None, 0)
            dev_name = dev.DeviceName
            dm = win32api.EnumDisplaySettings(dev_name, win32con.ENUM_CURRENT_SETTINGS)

            decky.logger.info(f"Get refresh rate: {dm.DisplayFrequency}")
            return dm.DisplayFrequency
        except Exception as e:
            decky.logger.info(f"Can't get refresh rate {e}")
            return 60

    async def set_refresh_rate(self, value: int):
        try:
            # Get the current display settings
            dev = win32api.EnumDisplayDevices(None, 0)
            dev_name = dev.DeviceName
            devmode = win32api.EnumDisplaySettings(dev_name, win32con.ENUM_CURRENT_SETTINGS)

            # Set the new refresh rate
            devmode.DisplayFrequency = value

            # Specify that the refresh rate field is being modified
            devmode.Fields = win32con.DM_DISPLAYFREQUENCY

            # Apply the changes
            change_result = win32api.ChangeDisplaySettings(devmode, 0)

            if change_result == win32con.DISP_CHANGE_SUCCESSFUL:
                decky.logger.info(f"Set refresh rate: {value} Hz")
                self.target_fps = value
            elif change_result == win32con.DISP_CHANGE_RESTART:
                decky.logger.info(f"Set refresh rate: {value} Hz, but a restart is required.")
            else:
                decky.logger.info(f"Set refresh rate: Failed to set to {value} Hz. Error code: {change_result}")
        except pywintypes.error as e:
            decky.logger.error(f"Can't set refresh rate {e}")
        
    async def get_target_fps(self):
        return self.target_fps
    
    async def set_target_fps(self, value: int):        
        self.target_fps = value
        decky.logger.info(f"Set target fps: {value}")

    async def get_turbo_boost(self):
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        # powercfg /QH SCHEME_CURRENT SUB_PROCESSOR PERFBOOSTMODE
        result = subprocess.run(
            ["powercfg", "/QH", "SCHEME_CURRENT", "SUB_PROCESSOR", "PERFBOOSTMODE"],
            capture_output=True,
            text=True,
            startupinfo=si
        )
        lines = result.stdout.splitlines()
        line_21 = lines[20].strip()
        value = line_21.split(":")[-1].strip()
        enabled = False if value == "0x00000000" else True

        decky.logger.info(f"Get turbo boost: {value} enabled: {enabled}")

        return enabled
    
    async def set_turbo_boost(self, value: bool):
        si = subprocess.STARTUPINFO()
        boost_value = "2" if value else "0"
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        # powercfg /SETACVALUEINDEX SCHEME_CURRENT SUB_PROCESSOR PERFBOOSTMODE 0
        result1 = subprocess.run(
            ["powercfg", "/SETACVALUEINDEX", "SCHEME_CURRENT", "SUB_PROCESSOR", "PERFBOOSTMODE", boost_value],
            capture_output=True,
            text=True,
            startupinfo=si
        )
        result2 = subprocess.run(
            ["powercfg", "/SETDCVALUEINDEX", "SCHEME_CURRENT", "SUB_PROCESSOR", "PERFBOOSTMODE", boost_value],
            capture_output=True,
            text=True,
            startupinfo=si
        )

        decky.logger.info(f"Set turbo boost: {boost_value}")

    async def get_epp(self):
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        # powercfg /QH SCHEME_CURRENT SUB_PROCESSOR PERFBOOSTMODE
        result = subprocess.run(
            ["powercfg", "/QH", "SCHEME_CURRENT", "SUB_PROCESSOR", "PERFEPP"],
            capture_output=True,
            text=True,
            startupinfo=si
        )
        lines = result.stdout.splitlines()
        line_11 = lines[10].strip()
        value = line_11.split(":")[-1].strip()
        try:
            decimal_value = int(value, 16)
            decky.logger.info(f"Decimal value: {decimal_value}")
        except ValueError:
            decimal_value = 80
            decky.logger.info(f"Invalid hexadecimal string: {value}")

        decky.logger.info(f"Get epp: {value} decimal: {decimal_value}")

        return decimal_value

    async def set_epp(self, value: bool):
        si = subprocess.STARTUPINFO()
        hex_str = f"0x{value:08X}"
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        # powercfg /SETACVALUEINDEX SCHEME_CURRENT SUB_PROCESSOR PERFEPP 0x00000051
        result1 = subprocess.run(
            ["powercfg", "/SETACVALUEINDEX", "SCHEME_CURRENT", "SUB_PROCESSOR", "PERFEPP", hex_str],
            capture_output=True,
            text=True,
            startupinfo=si
        )
        result2 = subprocess.run(
            ["powercfg", "/SETDCVALUEINDEX", "SCHEME_CURRENT", "SUB_PROCESSOR", "PERFEPP", hex_str],
            capture_output=True,
            text=True,
            startupinfo=si
        )

        decky.logger.info(f"Set epp: {hex_str}")

    async def get_cpu_clock_limit(self):
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        # powercfg /QH SCHEME_CURRENT SUB_PROCESSOR PROCFREQMAX
        result = subprocess.run(
            ["powercfg", "/QH", "SCHEME_CURRENT", "SUB_PROCESSOR", "PROCFREQMAX"],
            capture_output=True,
            text=True,
            startupinfo=si
        )
        lines = result.stdout.splitlines()
        line_11 = lines[10].strip()
        value = line_11.split(":")[-1].strip()
        try:
            decimal_value = int(value, 16)
            decky.logger.info(f"Decimal value: {decimal_value}")
        except ValueError:
            decimal_value = 0
            decky.logger.info(f"Invalid hexadecimal string: {value}")

        decky.logger.info(f"Get cpu clock limit: {value} decimal: {decimal_value}")

        return decimal_value

    async def set_cpu_clock_limit(self, value: int):
        si = subprocess.STARTUPINFO()
        hex_str = f"0x{value:08X}"
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        # powercfg /SETACVALUEINDEX SCHEME_CURRENT SUB_PROCESSOR PROCFREQMAX 0x00000bb8
        # powercfg /SETDCVALUEINDEX SCHEME_CURRENT SUB_PROCESSOR PROCFREQMAX 0x00000bb8
        # powercfg /SETACVALUEINDEX SCHEME_CURRENT SUB_PROCESSOR PROCFREQMAX1 0x00000bb8
        # powercfg /SETDCVALUEINDEX SCHEME_CURRENT SUB_PROCESSOR PROCFREQMAX1 0x00000bb8
        # powercfg -S SCHEME_CURRENT
        result1 = subprocess.run(
            ["powercfg", "/SETACVALUEINDEX", "SCHEME_CURRENT", "SUB_PROCESSOR", "PROCFREQMAX", hex_str],
            capture_output=True,
            text=True,
            startupinfo=si
        )
        result2 = subprocess.run(
            ["powercfg", "/SETDCVALUEINDEX", "SCHEME_CURRENT", "SUB_PROCESSOR", "PROCFREQMAX", hex_str],
            capture_output=True,
            text=True,
            startupinfo=si
        )
        result3 = subprocess.run(
            ["powercfg", "/SETACVALUEINDEX", "SCHEME_CURRENT", "SUB_PROCESSOR", "PROCFREQMAX1", hex_str],
            capture_output=True,
            text=True,
            startupinfo=si
        )
        result4 = subprocess.run(
            ["powercfg", "/SETDCVALUEINDEX", "SCHEME_CURRENT", "SUB_PROCESSOR", "PROCFREQMAX1", hex_str],
            capture_output=True,
            text=True,
            startupinfo=si
        )
        result5 = subprocess.run(
            ["powercfg", "/S", "SCHEME_CURRENT"],
            capture_output=True,
            text=True,
            startupinfo=si
        )

        decky.logger.info(f"Set cpu clock limit: {hex_str} {value}")

    async def system_loop(self, timestamp: int):
        self.SYSTEM_LOOP = timestamp
        while self.SYSTEM_LOOP == timestamp:
            hwnd, process_id, name, exe, title = get_active_window()
            current_fps, found_process_id, found_app_name = await self.get_fps(process_id)
            cpu_clock, cpu_effective_clock, cpu_usage, gpu_clock, gpu_effective_clock, gpu_usage = await self.get_hwinfo_sensors()
            lossless_scaling_running = await self.is_lossless_scaling_running()
            # decky.logger.info(f"System Statistics fps: {fps} cpu_clock: {cpu_clock} gpu_clock: {gpu_clock} cpu_usage: {cpu_usage} gpu_usage: {gpu_usage}")
            await decky.emit("sytem_statistics_event", current_fps, cpu_clock, cpu_usage, gpu_clock, gpu_usage, lossless_scaling_running)
            self.current_game_path = found_app_name
            self.current_game_name = find_game_name_from_path(found_app_name)

            if self.auto_tdp:
                if current_fps == 0:
                    if self.NO_FPS_COUNT >= self.IDLE_NO_FPS_NUM:
                        current_tdp = round(await self.get_tdp_limit(False))
                        if current_tdp != self.AVERAGE_TDP:
                            decky.logger.info(f"[{self.SYSTEM_LOOP}] Not playing any game, set TDP limit to {self.AVERAGE_TDP}W.")
                            await self.set_tdp_limit(self.AVERAGE_TDP)
                        else:
                            decky.logger.info(f"[{self.SYSTEM_LOOP}] Not playing any game.")
                        self.clear_fps()
                    else:
                        decky.logger.info(f"[{self.SYSTEM_LOOP}] No FPS detected, wait a bit longer to confirm that game is closed.")
                        self.NO_FPS_COUNT += 1
                else:
                    self.NO_FPS_COUNT = 0
                    current_tdp = round(await self.get_tdp_limit(False))
                    self.record_fps(current_tdp, current_fps)
                    if self.find_recorded_fps_count(current_tdp) < self.STABLE_NUM_RECORDED_FPS:
                        decky.logger.info(f"[{self.SYSTEM_LOOP}] FPS is {current_fps} at {current_tdp}W (CPU: {cpu_clock}Mhz {cpu_usage}%, GPU: {gpu_clock}Mhz {gpu_usage}%), wait a little bit longer for FPS to be stable.")
                    else:
                        average_fps = self.find_recorded_fps(current_tdp)
                        super_well = False
                        super_well_text = ""
                        if average_fps >= self.target_fps - 1:
                            # self.clear_lower_tdp(current_tdp)
                            super_well_text = "super "
                            super_well = True
                        if average_fps >= round(self.target_fps * self.GOOD_RATIO): # if already at good FPS, we can decrease the TDP.
                            if current_tdp <= self.MIN_TDP: # if already at lowest TDP, no need to do anything.
                                decky.logger.info(f"[{self.SYSTEM_LOOP}] Average FPS is {average_fps} at {current_tdp}W (CPU: {cpu_clock}Mhz {cpu_usage}%, GPU: {gpu_clock}Mhz {gpu_usage}%) but already running at min TDP {self.MIN_TDP}W, no need to adjust.")
                            else:
                                less_tdp_fps = self.find_recorded_fps(current_tdp - 1)
                                if less_tdp_fps == self.UNKNOWN:
                                    decky.logger.info(f"[{self.SYSTEM_LOOP}] Running {super_well_text}well ({average_fps}) at {current_tdp}W (CPU: {cpu_clock}Mhz {cpu_usage}%, GPU: {gpu_clock}Mhz {gpu_usage}%), trying to decrease TDP to {current_tdp - 1}W.")
                                    await self.set_tdp_limit(current_tdp - 1)
                                elif less_tdp_fps < round(self.target_fps * self.BAD_RATIO):
                                    if super_well:
                                        decky.logger.info(f"[{self.SYSTEM_LOOP}] Running {super_well_text}well ({average_fps}) at {current_tdp}W (CPU: {cpu_clock}Mhz {cpu_usage}%, GPU: {gpu_clock}Mhz {gpu_usage}%), decrease TDP will affect performance but let's try.")
                                        await self.set_tdp_limit(current_tdp - 1)
                                    else:
                                        decky.logger.info(f"[{self.SYSTEM_LOOP}] Running {super_well_text}well ({average_fps}) at {current_tdp}W (CPU: {cpu_clock}Mhz {cpu_usage}%, GPU: {gpu_clock}Mhz {gpu_usage}%), decrease TDP will affect performance. Keep it now.")
                                else:
                                    decky.logger.info(f"[{self.SYSTEM_LOOP}] Running {super_well_text}well ({average_fps}) at {current_tdp}W (CPU: {cpu_clock}Mhz {cpu_usage}%, GPU: {gpu_clock}Mhz {gpu_usage}%). Trying to decrease TDP to {current_tdp - 1}.")
                                    await self.set_tdp_limit(current_tdp - 1)
                        else:
                            if current_tdp >= self.MAX_TDP:
                                decky.logger.info(f"[{self.SYSTEM_LOOP}] Average FPS is {average_fps} at {current_tdp}W (CPU: {cpu_clock}Mhz {cpu_usage}%, GPU: {gpu_clock}Mhz {gpu_usage}%) but already running at max TDP {self.MAX_TDP}W, can't adjust.")
                            else:
                                decky.logger.info(f"[{self.SYSTEM_LOOP}] Average FPS is {average_fps} at {current_tdp}W (CPU: {cpu_clock}Mhz {cpu_usage}%, GPU: {gpu_clock}Mhz {gpu_usage}%), trying to increase TDP to {current_tdp + 1}W.")
                                await self.set_tdp_limit(current_tdp + 1)
            else:
                decky.logger.info(f"Not adjust TDP. FPS is {current_fps}.")
            
            if self.auto_tdp:
                if current_fps > 0:
                    await asyncio.sleep(1)
                else:
                    if self.NO_FPS_COUNT >= self.IDLE_NO_FPS_NUM:
                        await asyncio.sleep(2)
                    else:
                        await asyncio.sleep(1)
            else:
                await asyncio.sleep(3)

    async def start_system_loop(self):
        timestamp_now = round(datetime.now().timestamp())
        decky.logger.info(f"Start System Loop at {timestamp_now}")
        self.loop.create_task(self.system_loop(timestamp_now))

    async def log_info(self, message: str):
        decky.logger.info(str)

    # Migrations that should be performed before entering `_main()`.
    async def _migration(self):
        decky.logger.info("Migrating")
        # Here's a migration example for logs:
        # - `~/.config/decky-template/template.log` will be migrated to `decky.decky_LOG_DIR/template.log`
        decky.migrate_logs(os.path.join(decky.DECKY_USER_HOME,
                                               ".config", "decky-template", "template.log"))
        # Here's a migration example for settings:
        # - `~/homebrew/settings/template.json` is migrated to `decky.decky_SETTINGS_DIR/template.json`
        # - `~/.config/decky-template/` all files and directories under this root are migrated to `decky.decky_SETTINGS_DIR/`
        decky.migrate_settings(
            os.path.join(decky.DECKY_HOME, "settings", "template.json"),
            os.path.join(decky.DECKY_USER_HOME, ".config", "decky-template"))
        # Here's a migration example for runtime data:
        # - `~/homebrew/template/` all files and directories under this root are migrated to `decky.decky_RUNTIME_DIR/`
        # - `~/.local/share/decky-template/` all files and directories under this root are migrated to `decky.decky_RUNTIME_DIR/`
        decky.migrate_runtime(
            os.path.join(decky.DECKY_HOME, "template"),
            os.path.join(decky.DECKY_USER_HOME, ".local", "share", "decky-template"))
        
