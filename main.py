import os

# The decky plugin module is located at decky-loader/plugin
# For easy intellisense checkout the decky-loader code repo
# and add the `decky-loader/plugin/imports` path to `python.analysis.extraPaths` in `.vscode/settings.json`
import decky
import asyncio
import os
import sys
import time
import subprocess
import math
import re
import keyboard
import winreg
from ctypes import *
from ctypes.wintypes import *
from shutil import copyfile

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

def adjust(field, value):
    function_name = "set_" + field
    adjust_func = ryzenadj_lib.__getattr__(function_name)
    adjust_func.argtypes = [c_void_p, c_ulong]
    res = adjust_func(ry, value)
    if res:
        decky.logger.error(f"Adjust {field} failed: {error.format(function_name, res)}")

def determine(field):
    # First, refresh the table to ensure we have the latest values
    ryzenadj_lib.refresh_table(ry)
    function_name = "get_" + field
    determine_func = ryzenadj_lib.__getattr__(function_name)
    determine_func.argtypes = [c_void_p]
    determine_func.restype = c_float
    res = determine_func(ry)
    decky.logger.info(f"Determined {field}: {res}")
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
    dw_size = DWORD(ctypes.sizeof(dw_value))
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
    dw_size = DWORD(ctypes.sizeof(dw_value))
    success = rtss_set_property_func(property_name, byref(dw_value), dw_size)

    rtss_save_profile_func = rtss_lib.__getattr__("SaveProfile")
    rtss_save_profile_func.argtypes = [c_char_p]
    rtss_save_profile_func(b"")

    rtss_update_profile_func = rtss_lib.__getattr__("UpdateProfiles")
    rtss_update_profile_func.argtypes = []
    rtss_update_profile_func()

class Plugin:
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
        decky.logger.info("Hello World!")

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
        exe_path = os.path.join(decky.DECKY_PLUGIN_DIR, "bin", "adjust_get_current_system_volume_vista_plus.exe")

        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        result = subprocess.run(
            [exe_path],
            capture_output=True,
            text=True,
            startupinfo=si
        )

        volume = int(result.stdout.strip())
        decky.logger.info(f"Get volume: {volume}")
        return volume

    async def set_volume(self, volume: int):
        exe_path = os.path.join(decky.DECKY_PLUGIN_DIR, "bin", "adjust_get_current_system_volume_vista_plus.exe")

        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        result = subprocess.run(
            [exe_path, str(volume)],
            capture_output=True,
            text=True,
            startupinfo=si
        )

        if result.returncode != 0:
            decky.logger.error(f"Failed to set volume: {result.stderr.strip()}")

        decky.logger.info(f"Set volumne: {volume}")

    async def get_brightness(self):
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        result = subprocess.run(
            ["powershell", "-Command", "Get-Ciminstance -Namespace root/WMI -ClassName WmiMonitorBrightness | Select -ExpandProperty \"CurrentBrightness\""],
            capture_output=True,
            text=True,
            startupinfo=si
        )

        try:
            brightness = int(result.stdout.strip())
        except ValueError:
            brightness = 0
            decky.logger.info(f"Get brightness: Can't convert {result.stdout} to int")

        decky.logger.info(f"Get brightness: {brightness}")
        return brightness

    async def set_brightness(self, brightness: int):
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        # powershell -Command "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,70)"
        result = subprocess.run(
            ["powershell", "-Command", f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{brightness})"],
            capture_output=True,
            text=True,
            startupinfo=si
        )

        if result.returncode != 0:
            decky.logger.error(f"Set brightness to {brightness} failed: {result.stderr.strip()}")

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

    async def get_max_tdp(self):
        max_tdp = determine("slow_limit")
        decky.logger.info(f"Get max tdp: {max_tdp} W")
        return max_tdp

    async def set_max_tdp(self, value: int):
        adjust("stapm_limit", value * 1000)
        adjust("fast_limit", value * 1000)
        adjust("slow_limit", value * 1000)
        adjust("apu_slow_limit", value * 1000)
        decky.logger.info(f"Set max tdp: {value * 1000} mW")

    async def get_gpu_clock(self):
        gpu_clock = determine("gfx_clk")
        decky.logger.info(f"Get gpu clock: {gpu_clock} MHz")
        if gpu_clock < 800:
            return 800
        return gpu_clock

    async def set_gpu_clock(self, value: int):
        adjust("gfx_clk", value)
        decky.logger.info(f"Set gpu clock: {value} MHz")

    async def get_refresh_rates(self):
        exe_path = os.path.join(decky.DECKY_PLUGIN_DIR, "bin", "QRes.exe")

        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        result = subprocess.run(
            [exe_path, "/L"],
            capture_output=True,
            text=True,
            startupinfo=si
        )
        
        # decky.logger.info(f"Get refresh rate: {result.stdout}")
        # Split the output into lines
        lines = result.stdout.strip().splitlines()
        # Extract refresh rates
        refresh_rates = []

        for line in lines:
            if re.match(r'^\d', line):  # line starts with a number
                match = re.search(r'@ (\d+) Hz', line)
                if match:
                    refresh_rate_value = int(match.group(1))
                    if refresh_rate_value % 5 == 0:  # Only include refresh rates that are multiples of 5
                        refresh_rates.append(refresh_rate_value)
                    else:
                        decky.logger.info(f"Ignore refresh rate: {refresh_rate_value} Hz because it seems weird")

        # Get unique values and sort them
        unique_sorted_rates = sorted(set(refresh_rates))

        decky.logger.info(unique_sorted_rates)

        return unique_sorted_rates

    async def get_refresh_rate(self):
        exe_path = os.path.join(decky.DECKY_PLUGIN_DIR, "bin", "QRes.exe")

        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        result = subprocess.run(
            [exe_path, "/S"],
            capture_output=True,
            text=True,
            startupinfo=si
        )
        
        # Search for the first line starting with a resolution and containing "@ <number> Hz"
        for line in result.stdout.strip().splitlines():
            if re.match(r'^\d', line):  # line starts with a number
                match = re.search(r'@ (\d+) Hz', line)
                if match:
                    current_refresh_rate = int(match.group(1))
                    decky.logger.info(f"Get refresh rate: {current_refresh_rate}")
                    break
        else:
            current_refresh_rate = 60  # Not found
            decky.logger.info("Get refresh rate failed, fall back to 60")

        return current_refresh_rate

    async def set_refresh_rate(self, value: int):
        exe_path = os.path.join(decky.DECKY_PLUGIN_DIR, "bin", "QRes.exe")

        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        result = subprocess.run(
            [exe_path, "/R", str(value)],
            capture_output=True,
            text=True,
            startupinfo=si
        )

        if result.returncode != 0:
            decky.logger.error(f"Failed to set refresh rate: {result.stderr.strip()}")

        decky.logger.info(f"Set refresh rate: {value}")

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
            print(f"Decimal value: {decimal_value}")
        except ValueError:
            decimal_value = 80
            print(f"Invalid hexadecimal string: {value}")

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
            print(f"Decimal value: {decimal_value}")
        except ValueError:
            decimal_value = 0
            print(f"Invalid hexadecimal string: {value}")

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
