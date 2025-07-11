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
import ADLXPybind as ADLX
# Additional setup for pywin32, similar to pywin32.pth
if os.path.join(decky.DECKY_PLUGIN_DIR, "py_modules", "win32") not in sys.path:
    sys.path.append(os.path.join(decky.DECKY_PLUGIN_DIR, "py_modules", "win32"))
if os.path.join(decky.DECKY_PLUGIN_DIR, "py_modules", "win32", "lib") not in sys.path:
    sys.path.append(os.path.join(decky.DECKY_PLUGIN_DIR, "py_modules", "win32", "lib"))
if os.path.join(decky.DECKY_PLUGIN_DIR, "py_modules", "Pythonwin") not in sys.path:
    sys.path.append(os.path.join(decky.DECKY_PLUGIN_DIR, "py_modules", "Pythonwin"))
import pywin32_bootstrap
import screen_brightness_control as sbc
import win32api
import win32con
import pywintypes
import psutil
from collections import defaultdict
from datetime import datetime
from ctypes import *
from ctypes.wintypes import *
from shutil import copyfile
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
decky.logger.info(f"Platform: {platform.architecture()}")
decky.logger.info(f"Platform: {platform.python_implementation()}")
decky.logger.info(f"Version: {sys.version}")
#decky.logger.info(f"Path: {sys.path}")

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
    sys.exit("RyzenAdj could not get initialized")

#ryzenadj_lib.refresh_table(ry)

error_messages = {
    -1: "{:s} is not supported on this family\n",
    -3: "{:s} is not supported on this SMU\n",
    -4: "{:s} is rejected by SMU\n"
}

# RTSS
rtss_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Unwinder\RTSS", 0, winreg.KEY_READ)
rtss_install_dir, _ = winreg.QueryValueEx(rtss_key, "InstallDir")
winreg.CloseKey(rtss_key)
rtss_lib = cdll.LoadLibrary(os.path.join(rtss_install_dir, "RTSSHooks64.dll"))
rtss_osd_visible_flag = 1
rtss_overlay_config_path = os.path.join(rtss_install_dir, "Plugins", "Client", "OverlayEditor.cfg")

# RTSS SHARED MEMORY
last_dwTime0s = defaultdict(int)

def adjust(field, value):
    function_name = "set_" + field
    adjust_func = ryzenadj_lib.__getattr__(function_name)
    adjust_func.argtypes = [c_void_p, c_ulong]
    res = adjust_func(ry, value)
    if res:
        decky.logger.error(f"Adjust {field} using {function_name} failed: {res}")

def determine(field):
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
    function_name = "set_" + field
    adjust_func = ryzenadj_lib.__getattr__(function_name)
    adjust_func.argtypes = [c_void_p]
    res = adjust_func(ry)
    if res:
        error = error_messages.get(res, "{:s} did fail with {:d}\n")
        sys.stderr.write(error.format(function_name, res))

def get_flags():
    rtss_get_flags_func = rtss_lib.__getattr__("GetFlags")
    rtss_get_flags_func.argtypes = []
    rtss_get_flags_func.restype = c_ulong
    return rtss_get_flags_func()

def set_flags(flag, value):
    rtss_set_flags_func = rtss_lib.__getattr__("SetFlags")
    rtss_set_flags_func.argtypes = [c_ulong, c_ulong]
    rtss_set_flags_func(~flag, value)
    # rtss_post_message_func = rtss_lib.__getattr__("PostMessage")
    # rtss_post_message_func.argtypes = [c_ulong, WPARAM, LPARAM]
    # rtss_post_message_func(0, WPARAM(0), LPARAM(0))

def get_property(property_name):
    rtss_load_profile_func = rtss_lib.__getattr__("LoadProfile")
    rtss_load_profile_func.argtypes = [c_char_p]
    rtss_load_profile_func(b"")

    rtss_get_property_func = rtss_lib.__getattr__("GetProfileProperty")
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

def set_property(property_name, value):
    rtss_load_profile_func = rtss_lib.__getattr__("LoadProfile")
    rtss_load_profile_func.argtypes = [c_char_p]
    rtss_load_profile_func(b"")

    rtss_set_property_func = rtss_lib.__getattr__("SetProfileProperty")
    rtss_set_property_func.argtypes = [LPCSTR, c_void_p, DWORD]
    rtss_set_property_func.restype = BOOL

    dw_value = DWORD(value)
    dw_size = DWORD(sizeof(dw_value))
    success = rtss_set_property_func(property_name, byref(dw_value), dw_size)

    rtss_save_profile_func = rtss_lib.__getattr__("SaveProfile")
    rtss_save_profile_func.argtypes = [c_char_p]
    rtss_save_profile_func(b"")

    rtss_update_profile_func = rtss_lib.__getattr__("UpdateProfiles")
    rtss_update_profile_func.argtypes = []
    rtss_update_profile_func()

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
            subprocess.run([process_path], check=True)
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
                subprocess.run(["C:\Program Files\HWiNFO64\HWiNFO64.EXE"], check=True, timeout=5)
                decky.logger.info("[HWInfo] HWiNFO started.")
            except subprocess.CalledProcessError as e:
                decky.logger.info("[HWInfo] Can't start HWiNFO. Make sure it's installed.")
            except FileNotFoundError:
                decky.logger.info("[HWInfo] HWiNFO not found at C:\Program Files\HWiNFO64\HWiNFO64.EXE. Make sure it's installed.")

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

    # FPS values
    UNKNOWN: int = -1
    BEST: int = 60
    GOOD: int = 55
    BAD: int = 50
    STABLE_NUM_RECORDED_FPS: int = 5

    # TDP values
    MIN_TDP: int = 4
    MAX_TDP: int = 32
    AVERAGE_TDP: int = 18

    # Misc
    SYSTEM_LOOP: int = 0
    NO_FPS_COUNT: int = 0
    IDLE_NO_FPS_NUM: int = 3

    def display_demo(self):
        # Get ADLXHelp and ADLX initialization
        adlxHelper = ADLX.ADLXHelper()
        ret = adlxHelper.Initialize()

        if ret == ADLX.ADLX_RESULT.ADLX_OK:
            # Get system services
            system = adlxHelper.GetSystemServices()

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

        # Terminate ADLX
        ret = adlxHelper.Terminate()
        decky.logger.info("ADLX Terminate ret is: {}".format(ret))

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
    
    # async def find_lower_tdp(self, tdp):
    #     if len(self.tdps) <= 1:
    #         return tdp - 1
        
    #     lower_tdp = -1
    #     for idx, last_tdp in enumerate(self.tdps):
    #         if last_tdp[0] >= tdp:
    #             continue
    #         if last_tdp[1] >= self.GOOD:
    #             continue
    #         lower_tdp = 
    
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

    async def get_fps(self):
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
    
        fps = 0
        app_name = 'No'
        
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
                    if app_fps > fps:
                        fps = app_fps
                        app_name = raw_app_name
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
        return round(fps), app_name
    
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
        # self.display_demo()

    # Function called first during the unload process, utilize this to handle your plugin being stopped, but not
    # completely removed
    async def _unload(self):
        decky.logger.info("Goodnight World!")
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
        brightness = sbc.get_brightness(display=0)[0]

        decky.logger.info(f"Get brightness: {brightness}")
        return brightness

    async def set_brightness(self, brightness: int):
        sbc.set_brightness(brightness, display=0)

        decky.logger.info(f"Set brightness to {brightness}")

    async def get_osd(self):
        flags = get_flags()
        overlay_enabled = flags & rtss_osd_visible_flag
        if overlay_enabled == 0:
            osd = 0
        else:
            if not os.path.exists(rtss_overlay_config_path):
                decky.logger.info("OverlayEditor.cfg not found at:", rtss_overlay_config_path)
                osd = 1
            else:
                try:
                    found = False
                    with open(rtss_overlay_config_path, 'r', encoding='utf-8') as f:
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
        set_flags(rtss_osd_visible_flag, enabled)
        if value == 1:
            keyboard.send('ctrl+shift+f1')
        elif value == 2:
            keyboard.send('ctrl+shift+f2')
        elif value == 3:
            keyboard.send('ctrl+shift+f3')
        elif value == 4:
            keyboard.send('ctrl+shift+f4')
        
        # Update the overlay configuration file
        if not os.path.exists(rtss_overlay_config_path):
            decky.logger.info("OverlayEditor.cfg not found at:", rtss_overlay_config_path)
        else:
            try:
                # Read all lines from the config file
                with open(rtss_overlay_config_path, 'r', encoding='utf-8') as f:
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
                with open(rtss_overlay_config_path, 'w', encoding='utf-8') as f:
                    f.writelines(updated_lines)
            except Exception as e:
                decky.logger.info("Error updating config file:", e)
        decky.logger.info(f"Set osd: {value}")

    async def get_osd_size(self):
        osd_size = get_property(b"ZoomRatio")
        
        decky.logger.info(f"Get osd size: {osd_size}")
        return osd_size
    
    async def set_osd_size(self, value: int):
        set_property(b"ZoomRatio", value)

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
        # Get primary display device
        dev = win32api.EnumDisplayDevices(None, 0)
        dev_name = dev.DeviceName

        rates = set()
        mode_num = 0
        common_refresh_rates = [40, 45, 60, 90, 120, 144, 165, 240, 300]

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

    async def get_refresh_rate(self):
        dev = win32api.EnumDisplayDevices(None, 0)
        dev_name = dev.DeviceName
        dm = win32api.EnumDisplaySettings(dev_name, win32con.ENUM_CURRENT_SETTINGS)

        decky.logger.info(f"Get refresh rate: {dm.DisplayFrequency}")
        return dm.DisplayFrequency

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
            elif change_result == win32con.DISP_CHANGE_RESTART:
                decky.logger.info(f"Set refresh rate: {value} Hz, but a restart is required.")
            else:
                decky.logger.info(f"Failed to set refresh rate to {value} Hz. Error code: {change_result}")
        except pywintypes.error as e:
            decky.logger.error(f"An error occurred: {e}")

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
            current_fps, app_name = await self.get_fps()
            cpu_clock, cpu_effective_clock, cpu_usage, gpu_clock, gpu_effective_clock, gpu_usage = await self.get_hwinfo_sensors()
            # decky.logger.info(f"System Statistics fps: {fps} cpu_clock: {cpu_clock} gpu_clock: {gpu_clock} cpu_usage: {cpu_usage} gpu_usage: {gpu_usage}")
            await decky.emit("sytem_statistics_event", current_fps, cpu_clock, cpu_usage, gpu_clock, gpu_usage)

            if self.auto_tdp:
                if current_fps == 0:
                    if self.NO_FPS_COUNT >= self.IDLE_NO_FPS_NUM:
                        current_tdp = round(await self.get_tdp_limit(False))
                        if current_tdp != self.AVERAGE_TDP:
                            decky.logger.info(f"[{self.SYSTEM_LOOP}] Not playing any game, set TDP limit to 16W.")
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
                        super_well_text = ""
                        if average_fps >= self.BEST:
                            # self.clear_lower_tdp(current_tdp)
                            super_well_text = "super "
                        if average_fps >= self.GOOD: # if already at good FPS, we can decrease the TDP.
                            if current_tdp <= self.MIN_TDP: # if already at lowest TDP, no need to do anything.
                                decky.logger.info(f"[{self.SYSTEM_LOOP}] Average FPS is {average_fps} at {current_tdp}W (CPU: {cpu_clock}Mhz {cpu_usage}%, GPU: {gpu_clock}Mhz {gpu_usage}%) but already running at min TDP {self.MIN_TDP}W, no need to adjust.")
                            else:
                                less_tdp_fps = self.find_recorded_fps(current_tdp - 1)
                                if less_tdp_fps == self.UNKNOWN:
                                    decky.logger.info(f"[{self.SYSTEM_LOOP}] Running {super_well_text}well ({average_fps}) at {current_tdp}W (CPU: {cpu_clock}Mhz {cpu_usage}%, GPU: {gpu_clock}Mhz {gpu_usage}%), trying to decrease TDP to {current_tdp - 1}W.")
                                    await self.set_tdp_limit(current_tdp - 1)
                                elif less_tdp_fps < self.BAD:
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
                        await asyncio.sleep(5)
                    else:
                        await asyncio.sleep(1)
            else:
                await asyncio.sleep(5)

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
        
