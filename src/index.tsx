import {
  ButtonItem,
  PanelSection,
  PanelSectionRow,
  SliderField,
  DropdownItem,
  DropdownOption,
  ToggleField,
  ProgressBarWithInfo,
  //Navigation,
  staticClasses
} from "@decky/ui";
import {
  addEventListener,
  removeEventListener,
  callable,
  definePlugin,
  toaster,
  // call,
  // routerHook
} from "@decky/api"
import { Settings, LosslessScalingRunState } from "./util";
import { useState, useEffect } from "react";
import { FaRegWindowRestore } from "react-icons/fa";

// import logo from "../assets/logo.png";

let cpuMinClock = 100
let cpuMaxClock = 5100
let gpuMinClock = 200
let gpuMaxClock = 3000

let getVolumeFunc = callable<[], number>('get_volume');
Settings.syncVolume(await getVolumeFunc());

let getMutedFunc = callable<[], boolean>('get_muted');
Settings.syncMuted(await getMutedFunc());

// Brightness
let getBrightnessFunc = callable<[], number>('get_brightness');
Settings.syncBrightness(await getBrightnessFunc());

// OSD
let getOSDFunc = callable<[], number>('get_osd');
Settings.syncOSD(await getOSDFunc());

// OSD Size
let getOSDSizeFunc = callable<[], number>('get_osd_size');
Settings.syncOSDSize(await getOSDSizeFunc());

// Max TDP
let getTDPLimitFunc = callable<[boolean], number>('get_tdp_limit')
Settings.syncTDPLimit(await getTDPLimitFunc(true));

let getRefreshRatesFunc = callable<[], number[]>('get_refresh_rates');
let refreshRates: number[] = await getRefreshRatesFunc();

let getRefreshRateFunc = callable<[], number>('get_refresh_rate');
Settings.syncRefreshRate(await getRefreshRateFunc());

let getTurboBoostFunc = callable<[], boolean>('get_turbo_boost');
Settings.syncTurboBoost(await getTurboBoostFunc());

let getEPPFunc = callable<[], number>('get_epp');
Settings.syncEPP(await getEPPFunc());

let getCPUClockLimitFunc = callable<[], number>('get_cpu_clock_limit');
let baseCPUClockLimit = await getCPUClockLimitFunc()
if (baseCPUClockLimit != 0) {
  Settings.syncCPUClockLimit(baseCPUClockLimit);
}
Settings.syncShouldLimitCPUClock(baseCPUClockLimit != 0);

let getGPUClockLimitFunc = callable<[], number>('get_gpu_clock_limit');
Settings.syncGPUClockLimit(await getGPUClockLimitFunc());
Settings.setShouldLimitGPUClock(false);

const startSystemLoopFunc = callable<[], void>('start_system_loop');
await startSystemLoopFunc()

const startOsdLoopFunc = callable<[], void>('start_osd_loop');
await startOsdLoopFunc()

let minTDP = await callable<[], number>('get_min_tdp')();
let maxTDP = await callable<[], number>('get_max_tdp')();

let initADLXFunc = callable<[string]>('init_adlx');

let getRadeonSuperResolutionFunc = callable<[], boolean>('get_radeon_super_resolution');
Settings.syncRadeonSuperResolution(await getRadeonSuperResolutionFunc());
let getRadeonSuperResolutionSharpnessFunc = callable<[], number>('get_radeon_super_resolution_sharpness');
Settings.syncRadeonSuperResolutionSharpness(await getRadeonSuperResolutionSharpnessFunc());
let getAMDFluidMotionFrameFunc = callable<[], boolean>('get_amd_fluid_motion_frame');
Settings.syncAMDFluidMotionFrame(await getAMDFluidMotionFrameFunc())
let getRadeonAntiLagFunc = callable<[], boolean>('get_radeon_anti_lag');
Settings.syncRadeonAntiLag(await getRadeonAntiLagFunc())
let getRadeonBoostFunc = callable<[], boolean>('get_radeon_boost');
Settings.syncRadeonBoost(await getRadeonBoostFunc())
let getRadeonChillFunc = callable<[], boolean>('get_radeon_chill');
Settings.syncRadeonChill(await getRadeonChillFunc())
let getRadeonChillMinFPSFunc = callable<[], number>('get_radeon_chill_min_fps');
Settings.syncRadeonChillMinFPS(await getRadeonChillMinFPSFunc())
let getRadeonChillMaxFPSFunc = callable<[], number>('get_radeon_chill_max_fps');
Settings.syncRadeonChillMaxFPS(await getRadeonChillMaxFPSFunc())
let getGPUScalingFunc = callable<[], boolean>('get_gpu_scaling');
Settings.syncGPUScaling(await getGPUScalingFunc())
let getScalingModeFunc = callable<[], number>('get_scaling_mode');
Settings.syncScalingMode(await getScalingModeFunc())
let getIntegerScalingFunc = callable<[], boolean>('get_integer_scaling');
Settings.syncIntegerScaling(await getIntegerScalingFunc())
let scalingModes = [
  { data: 0, label: "Preserve Aspect Ratio" },
  { data: 1, label: "Full Panel" },
  { data: 2, label: "Center" },
];
let getTargetFPSFunc = callable<[], number>('get_target_fps');
Settings.syncTargetFPS(await getTargetFPSFunc());

let isLosslessScalingRunningFunc = callable<[], boolean>('is_lossless_scaling_running');
Settings.syncLosslessScalingState((await isLosslessScalingRunningFunc()) ? LosslessScalingRunState.Running : LosslessScalingRunState.Closed);

let getCurrentGameInfoFunc = callable<[], [string, string]>('get_current_game_info');
let findLosslessScalingProfileNameFunc = callable<[string], string>('find_lossless_scaling_profile_name');
let getLosslessScalingProfileNamesFunc = callable<[], string[]>('get_lossless_scaling_profile_names');
let getLosslessScalingProfileByNameFunc = callable<[string], [boolean, number, number, number, number, boolean, number, number, number, number, number, boolean]>('get_lossless_scaling_profile_by_name');
let setLosslessScalingProfileByNameFunc = callable<[string, string, string], void>('set_lossless_scaling_profile_by_name')

let losslessScalingFrameGenOptions = [
  { data: 0, label: "Off" },
  { data: 1, label: "LSFG3" },
  { data: 2, label: "LSFG2" },
  { data: 3, label: "LSFG1" },
];

let losslessScalingFrameGen3Mode1Options = [
  { data: 0, label: "FIXED" },
  { data: 1, label: "ADAPTIVE" }
];

let losslessScalingFrameGen2ModeOptions = [
  { data: 0, label: "X2" },
  { data: 1, label: "X3" },
  { data: 1, label: "X4" }
];

let losslessScalingDefaultProfile = "Default"

let addLosslessScalingProfileFunc = callable<[string, string], boolean>('add_lossless_scaling_profile');
let restartLosslessScalingFunc = callable<[], void>('restart_lossless_scaling');

let getNumberOfMonitorsFunc = callable<[], number>("get_num_monitors")
let getMultipleMonitorsModeFunc = callable<[], number>("get_multiple_monitors_mode")
let externalMonitorModes = [
  { data: 0, label: "Built-in Only" },
  { data: 1, label: "External Only" },
  { data: 2, label: "Duplicate" },
  { data: 3, label: "Extend" },
];

function Content() {
  const [volume, setVolume] = useState<number>(Settings.getVolume());
  const [muted, setMuted] = useState<boolean>(Settings.getMuted());
  const [brightness, setBrightness] = useState<number>(Settings.getBrightness());
  const [osd, setOSD] = useState<number>(Settings.getOSD());
  const [osdSize, setOSDSize] = useState<number>(Settings.getOSDSize());
  const [autoTDP, setAutoTDP] = useState<boolean>(Settings.getAutoTDP());
  const [tdpLimit, setTDPLimit] = useState<number>(Settings.getTDPLimit());
  const [refreshRate, setRefreshRate] = useState<number>(Settings.getRefreshRate());
  const [turboBoost, setTurboBoost] = useState<boolean>(Settings.getTurboBoost());
  const [epp, setEPP] = useState<number>(Settings.getEPP());
  const [shouldLimitCPUClock, setShouldLimitCPUClock] = useState<boolean>(Settings.getShouldLimitCPUClock() && !Settings.getAutoTDP());
  const [cpuClockLimit, setCPUClockLimit] = useState<number>(Settings.getCPUClockLimit());
  const [shouldLimitGPUClock, setShouldLimitGPUClock] = useState<boolean>(Settings.getShouldLimitGPUClock() && !Settings.getAutoTDP());
  const [gpuClockLimit, setGPUClockLimit] = useState<number>(Settings.getGPUClockLimit());
  const [radeonSuperResolution, setRadeonSuperResolution] = useState<boolean>(Settings.getRadeonSuperResolution());
  const [radeonSuperResolutionSharpness, setRadeonSuperResolutionSharpness] = useState<number>(Settings.getRadeonSuperResolutionSharpness());
  const [amdFluidMotionFrame, setAMDFluidMotionFrame] = useState<boolean>(Settings.getAMDFluidMotionFrame());
  const [radeonAntiLag, setRadeonAntiLag] = useState<boolean>(Settings.getRadeonAntiLag());
  const [radeonBoost, setRadeonBoost] = useState<boolean>(Settings.getRadeonBoost());
  const [radeonChill, setRadeonChill] = useState<boolean>(Settings.getRadeonChill());
  const [radeonChillMinFPS, setRadeonChillMinFPS] = useState<number>(Settings.getRadeonChillMinFPS());
  const [radeonChillMaxFPS, setRadeonChillMaxFPS] = useState<number>(Settings.getRadeonChillMaxFPS());
  const [gpuScaling, setGPUScaling] = useState<boolean>(Settings.getGPUScaling());
  const [scalingMode, setScalingMode] = useState<number>(Settings.getScalingMode());
  const [integerScaling, setIntegerScaling] = useState<boolean>(Settings.getIntegerScaling());
  const [targetFPS, setTargetFPS] = useState<number>(Settings.getTargetFPS());
  const [losslessScalingState, setLosslessScalingState] = useState<LosslessScalingRunState>(Settings.getLosslessScalingState());
  const [currentGameName, setCurrentGameName] = useState<string>("");
  const [currentGamePath, setCurrentGamePath] = useState<string>("");
  const [isLosslessScalingConfigured, setIsLosslessScalingConfigured] = useState<boolean>(false);
  const [losslessScalingProfileNames, setLosslessScalingProfileNames] = useState<string[]>([losslessScalingDefaultProfile]);
  const [losslessScalingProfileName, setLosslessScalingProfileName] = useState<string>(Settings.getLosslessScalingProfileName());
  const [autoScale, setAutoScale] = useState<boolean>(Settings.getLosslessScalingAutoScale());
  const [autoScaleDelay, setAutoScaleDelay] = useState<number>(Settings.getLosslessScalingAutoScaleDelay());
  const [scalingModeValue, setScalingModeValue] = useState<number>(0);
  const [scalingFitModeValue, setScalingFitModeValue] = useState<number>(0);
  const [frameGen, setFrameGen] = useState<number>(Settings.getLosslessScalingFrameGen());
  const [drawFPS, setDrawFPS] = useState<boolean>(Settings.getLosslessScalingDrawFPS());
  const [frameGen3Mode1, setFrameGen3Mode1] = useState<number>(Settings.getLosslessScalingFrameGen3Mode1());
  const [frameGen2Mode, setFrameGen2Mode] = useState<number>(Settings.getLosslessScalingFrameGen2Mode());
  const [frameGen3Multiplier, setFrameGen3Multiplier] = useState<number>(Settings.getLosslessScalingFrameGen3Multiplier());
  const [frameGen3Target, setFrameGen3Target] = useState<number>(Settings.getLosslessScalingFrameGen3Target());
  const [frameGenFlowScale, setFrameGenFlowScale] = useState<number>(Settings.getLosslessScalingFrameGenFlowScale());
  const [frameGenPerformance, setFrameGenPerformance] = useState<boolean>(Settings.getLosslessScalingFrameGenPerformance());
  const [numberOfMonitors, setNumberOfMonitors] = useState<number>(1);
  const [multiMonitorMode, setMultiMonitorMode] = useState<number>(Settings.getMultiMonitorMode());

  function changeLosslessScalingState(losslessScalingRunning: boolean) {
    if (losslessScalingRunning) {
      setLosslessScalingState(LosslessScalingRunState.Running);
      Settings.syncLosslessScalingState(LosslessScalingRunState.Running);
    }
    else {
      if (losslessScalingState == LosslessScalingRunState.Starting) {
        console.log("[Frontend] Lossless Scaling is starting");
      }
      else {
        console.log("[Frontend] Lossless Scaling is closed");
        setLosslessScalingState(LosslessScalingRunState.Closed);
        Settings.syncLosslessScalingState(LosslessScalingRunState.Closed);
      }
    }
  };
  function onSystemStatistics(newFPS: number, newCPUClock: number, newCPUUsage: number, newGPUClock: number, newGPUUsage: number, losslessScalingRunning: boolean) {
    console.log("[Frontend] newFPS: ", newFPS, " newCPUClock: ", newCPUClock, " newGPUClock: ", newGPUClock, " new CPUUsage: ", newCPUUsage, " newGPUUsage; ", newGPUUsage);
    changeLosslessScalingState(losslessScalingRunning);
  };

  useEffect(() => {
    addEventListener('system_statistics_event', onSystemStatistics);
    return () => {
      removeEventListener('system_statistics_event', onSystemStatistics);
    }
  }, []);

  const [cancelSyncVolume, setCancelSyncVolume] = useState<boolean>(false);
  useEffect(() => {
    let syncVolume = true;
    getVolumeFunc().then((value) => {
      console.log("[Frontend] Got volume value:", value);
      if (syncVolume) {
        setVolume(value);
        Settings.syncVolume(value);
      }
    });
    return () => { syncVolume = false;}
  }, [cancelSyncVolume]);

  const [cancelSyncMuted, setCancelSyncMuted] = useState<boolean>(false);
  useEffect(() => {
    let syncMuted = true;
    getMutedFunc().then((value) => {
      if (syncMuted) {
        console.log("[Frontend] Got muted value:", value, "user not changed so update");
        setMuted(value);
        Settings.syncMuted(value);
      }
      else {
        console.log("[Frontend] Got muted value:", value, "user changed so not update");
      }
    });
    return () => { syncMuted = false; }
  }, [cancelSyncMuted]);

  useEffect(() => {
    getNumberOfMonitorsFunc().then((value) => {
      console.log("[Frontend] Got monitors:", value);
      setNumberOfMonitors(value);
    });
    getMultipleMonitorsModeFunc().then((value) => {
      console.log("[Frontend] Get multiple monitors mode: ", value);
      setMultiMonitorMode(value);
      Settings.syncMultiMonitorMode(value);
    });
  }, []);

  const [cancelSyncBrightness, setCancelSyncBrightness] = useState<boolean>(false);
  useEffect(() => {
    let syncBrightness = true;
    getBrightnessFunc().then((value) => {
      if (syncBrightness) {
        console.log("[Frontend] Got brightness value:", value);
        setBrightness(value);
        Settings.syncBrightness(value);
      }
    });
    return () => { syncBrightness = false; }
  }, [cancelSyncBrightness]);

  const [cancelSyncOSD, setCancelSyncOSD] = useState<boolean>(false);
  useEffect(() => {
    let syncOSD = true;
    getOSDFunc().then((value) => {
      if (syncOSD) {
        console.log("[Frontend] Got OSD value:", value);
        setOSD(value);
        Settings.syncOSD(value);
      }
    });
    return () => { syncOSD = false; }
  }, [cancelSyncOSD]);

  const [cancelSyncOSDSize, setCancelSyncOSDSize] = useState<boolean>(false);
  useEffect(() => {
    let syncOSDSize = true;
    getOSDSizeFunc().then((value) => {
      if (syncOSDSize) {
        console.log("[Frontend] Got OSD size value:", value);
        setOSDSize(value);
        Settings.syncOSDSize(value);
      }
    });
    return () => { syncOSDSize = false; }
  }, [cancelSyncOSDSize]);

  let userChangedMaxTDP = false;
  useEffect(() => {
    getTDPLimitFunc(true).then((value) => {
      if (!userChangedMaxTDP) {
        console.log("[Frontend] Got TDP value:", value);
        if (value > 3) {
          setTDPLimit(value);
          Settings.syncTDPLimit(value);
        }
        else {
          console.warn("[Frontend] Invalid TDP value received:", value);
        }
      }
    });
  }, []);

  useEffect(() => {
    getRefreshRateFunc().then((value) => {
      console.log("[Frontend] Got refresh rate value:", value);
      setRefreshRate(value);
      Settings.syncRefreshRate(value);
    });
  }, []);

  useEffect(() => {
    getTurboBoostFunc().then((value) => {
      console.log("[Frontend] Got turbo boost value:", value);
      setTurboBoost(value);
      Settings.syncTurboBoost(value);
    });
  }, []);

  let userChangedEPP = false;
  useEffect(() => {
    getEPPFunc().then((value) => {
      if (!userChangedEPP) {
        console.log("[Frontend] Got EPP value:", value);
        setEPP(value);
        Settings.syncEPP(value);
      }
    });
  }, []);

  useEffect(() => {
    getCPUClockLimitFunc().then((value) => {
      console.log("[Frontend] Got CPU clock limit value:", value);
      setShouldLimitCPUClock(value != 0);
      if (value != 0) {
        setCPUClockLimit(value);
        Settings.syncCPUClockLimit(value);
      }
      Settings.syncShouldLimitCPUClock(value != 0);
    });
  }, []);

  useEffect(() => {
    getGPUClockLimitFunc().then((value) => {
      console.log("[Frontend] Got GPU clock limit value:", value);
      if (value != 0) {
        setGPUClockLimit(value);
        Settings.syncGPUClockLimit(value);
      }
    });
  }, []);

  useEffect(() => {
    getTargetFPSFunc().then((value) => {
      console.log("[Frontend] Got target FPS:", value);
      if (value != 0) {
        setTargetFPS(value);
        Settings.syncTargetFPS(value);
      }
    });
  }, []);

  useEffect(() => {
    initADLXFunc("Content").then(() => {
      console.log("[Frontend] ADLX initialized");

      getRadeonSuperResolutionFunc().then((value) => {
        console.log("[Frontend] Got Radeon Super Resolution:", value);
        setRadeonSuperResolution(value);
        Settings.syncRadeonSuperResolution(value);
      });

      getRadeonSuperResolutionSharpnessFunc().then((value) => {
        console.log("[Frontend] Got Radeon Super Resolution Sharpness:", value);
        setRadeonSuperResolutionSharpness(value);
        Settings.syncRadeonSuperResolutionSharpness(value);
      });

      getAMDFluidMotionFrameFunc().then((value) => {
        console.log("[Frontend] Got AMD Fluid Motion Frame:", value);
        setAMDFluidMotionFrame(value);
        Settings.syncAMDFluidMotionFrame(value);
      });

      getRadeonAntiLagFunc().then((value) => {
        console.log("[Frontend] Got Radeon Anti Lag:", value);
        setRadeonAntiLag(value);
        Settings.syncRadeonAntiLag(value);
      });

      getRadeonBoostFunc().then((value) => {
        console.log("[Frontend] Got Radeon Boost:", value);
        setRadeonBoost(value);
        Settings.syncRadeonBoost(value);
      });

      getRadeonChillFunc().then((value) => {
        console.log("[Frontend] Got Radeon Chill:", value);
        setRadeonChill(value);
        Settings.syncRadeonChill(value);
      });

      getRadeonChillMinFPSFunc().then((value) => {
        console.log("[Frontend] Got Radeon Chill Min FPS:", value);
        setRadeonChillMinFPS(value);
        Settings.syncRadeonChillMinFPS(value);
      });

      getRadeonChillMaxFPSFunc().then((value) => {
        console.log("[Frontend] Got Radeon Chill Max FPS:", value);
        setRadeonChillMaxFPS(value);
        Settings.syncRadeonChillMaxFPS(value);
      });

      getGPUScalingFunc().then((value) => {
        console.log("[Frontend] Got GPU Scaling:", value);
        setGPUScaling(value);
        Settings.syncGPUScaling(value);
      });

      getScalingModeFunc().then((value) => {
        console.log("[Frontend] Got Scaling Mode:", value);
        setScalingMode(value);
        Settings.syncScalingMode(value);
      });

      getIntegerScalingFunc().then((value) => {
        console.log("[Frontend] Got Integer Scaling:", value);
        setIntegerScaling(value);
        Settings.syncIntegerScaling(value);
      });
    });
  }, []);

  useEffect(() => {
    isLosslessScalingRunningFunc().then((value) => {
      console.log("[Frontend] Lossless Scaling running:", value);
      changeLosslessScalingState(value);
    });
  }, []);

  useEffect(() => {
    getCurrentGameInfoFunc().then((value) => {
      console.log("[Frontend] Current game name:", value[0], "Current game path:", value[1]);
      setCurrentGameName(value[0]);
      setCurrentGamePath(value[1]);
    });
  }, []);

  useEffect(() => {
    if (currentGamePath.length == 0) {
        setIsLosslessScalingConfigured(true);
      }
      else {
        findLosslessScalingProfileNameFunc(currentGamePath).then((foundProfileName) => {
          if (foundProfileName.length == 0) {
            if (losslessScalingProfileNames.includes(currentGameName)) {
              console.log("[Frontend] Game at path :", currentGamePath, " is not found but game name", currentGameName, " found, set new path");
              setCurrentGameName(currentGameName);
              setLosslessScalingProfileName(currentGameName);
              setIsLosslessScalingConfigured(true);
              setLosslessScalingProfileByNameFunc(currentGameName, "Path", currentGamePath).then(() => {
                console.log("[Frontend] Lossless Scaling profile updated Path:", currentGamePath);
              });
            }
            else {
              console.log("[Frontend] Game at path :", currentGamePath, " is not found but game name", currentGameName, " not found neither");
              setIsLosslessScalingConfigured(false);
            }
          }
          else {
            console.log("[Frontend] Game at path :", currentGamePath, " is configured");
            setCurrentGameName(foundProfileName);
            setLosslessScalingProfileName(foundProfileName);
            setIsLosslessScalingConfigured(true);
          }
        });
      }
  }, [currentGamePath]);

  useEffect(() => {
    getLosslessScalingProfileNamesFunc().then((value) => {
      console.log("[Frontend] Got profiles:", value.length);
      setLosslessScalingProfileNames(value);
    });
  }, []);

  const onLosslessScalingProfileChanged = (value: [boolean, number, number, number, number, boolean, number, number, number, number, number, boolean]) => {
    console.log("[Frontend] Got profile:", losslessScalingProfileName, "frame gen:", value[4]);
      setAutoScale(value[0]);
      Settings.syncLosslessScalingAutoScale(value[0]);

      setAutoScaleDelay(value[1]);
      Settings.syncLosslessScalingAutoScaleDelay(value[1]);

      setScalingModeValue(value[2]);
      setScalingFitModeValue(value[3]);

      setFrameGen(value[4]);
      Settings.syncLosslessScalingFrameGen(value[4]);

      setDrawFPS(value[5]);
      Settings.syncLosslessScalingDrawFPS(value[5]);

      setFrameGen3Mode1(value[6]);
      Settings.syncLosslessScalingFrameGen3Mode1(value[6]);

      setFrameGen2Mode(value[7]);
      Settings.syncLosslessScalingFrameGen2Mode(value[7]);

      setFrameGen3Multiplier(value[8]);
      Settings.syncLosslessScalingFrameGen3Multiplier(value[8]);

      setFrameGen3Target(value[9]);
      Settings.syncLosslessScalingFrameGen3Target(value[9]);

      setFrameGenFlowScale(value[10]);
      Settings.syncLosslessScalingFrameGenFlowScale(value[10]);

      setFrameGenPerformance(value[11]);
      Settings.syncLosslessScalingFrameGenPerformance(value[11]);
  };
  
  useEffect(() => {
    console.log("[Frontend] getLosslessScalingProfileByNameFunc(", losslessScalingProfileName, ")");
    getLosslessScalingProfileByNameFunc(losslessScalingProfileName).then(onLosslessScalingProfileChanged);
  }, [losslessScalingProfileName]);

  const sections = [
    <PanelSection title="System">
      <PanelSectionRow>
        <SliderField
          label={"Volume"}
          showValue={true}
          min={0}
          max={100}
          value={volume}
          step={1}
          onChange={(value: number) => {
            setCancelSyncVolume(true);
            console.log("[Frontend] Volume changed to:", value);
            setVolume(value);
            Settings.setVolume(value);
          }}>
        </SliderField>
        <ToggleField
          label={"Mute"}
          checked={muted}
          highlightOnFocus={true}
          onChange={(value: boolean) => {
            setCancelSyncMuted(true);
            console.log("[Frontend] Mute changed to:", value);
            setMuted(value);
            Settings.setMuted(value);
          }}>
        </ToggleField>
      </PanelSectionRow>
      <PanelSectionRow>
        <SliderField
          label="Brightness"
          showValue={true}
          min={0}
          max={100}
          value={brightness}
          step={10}
          onChange={(value: number) => {
            setCancelSyncBrightness(true);
            console.log("[Frontend] Brightness changed to:", value);
            setBrightness(value);
            Settings.setBrightness(value);
          }}>
        </SliderField>
      </PanelSectionRow>
      <PanelSectionRow>
        <DropdownItem
          label={"Refresh Rate"}
          selectedOption={refreshRates.find(rate => rate == refreshRate)}
          rgOptions={refreshRates.map(rate => ({
            data: rate,
            label: `${rate} Hz`
          })) as DropdownOption[]}
          onChange={(option) => {
            console.log("[Frontend] Refresh Rate changed to:", option.data);
            setRefreshRate(option.data);
            Settings.setRefreshRate(option.data);
          }}
        >
        </DropdownItem>
      </PanelSectionRow>
      {
        numberOfMonitors == 2 ? 
        (
          <DropdownItem
            label={"External Monitor"}
            selectedOption={externalMonitorModes.findIndex(mode => mode.data == multiMonitorMode)}
            rgOptions={externalMonitorModes.map(mode => ({
              data: mode.data,
              label: mode.label
            })) as DropdownOption[]}
            onChange={(option) => {
              console.log("[Frontend] Monitor mode:", option.data);
              setMultiMonitorMode(option.data);
              Settings.setMultiMonitorMode(option.data);
            }}
          >
          </DropdownItem>
        )
        :
        null
      }
    </PanelSection>
  ];

  sections.push(<PanelSection title="OSD">
      <PanelSectionRow>
        <SliderField
          label={"Overlay"}
          showValue={false}
          min={0}
          max={4}
          notchCount={5}
          notchLabels={[
            { notchIndex: 0, label: "Off" },
            { notchIndex: 1, label: "FPS" },
            { notchIndex: 2, label: "Battery" },
            { notchIndex: 3, label: "Detailed" },
            { notchIndex: 4, label: "Full" }
          ]}
          value={osd}
          step={1}
          onChange={(value: number) => {
            setCancelSyncOSD(true);
            console.log("[Frontend] OSD changed to:", value);
            setOSD(value);
            Settings.setOSD(value);
          }}>
        </SliderField>
        <SliderField
          label={"Overlay Size"}
          showValue={true}
          min={1}
          max={6}
          value={osdSize}
          step={1}
          onChange={(value: number) => {
            setCancelSyncOSDSize(true);
            console.log("[Frontend] OSD size changed to:", value);
            setOSDSize(value);
            Settings.setOSDSize(value);
          }}>
        </SliderField>
      </PanelSectionRow>
    </PanelSection>);
  
  if (autoTDP) {
    sections.push(<PanelSection title="Auto Performance">
      <PanelSectionRow>
        <ToggleField
          label={"Auto TDP"}
          checked={autoTDP}
          highlightOnFocus={true}
          onChange={(value: boolean) => {
            console.log("[Frontend] Auto TDP changed to:", value);
            setAutoTDP(value);
            Settings.setAutoTDP(value);
            if (value) {
              setShouldLimitCPUClock(false);
              Settings.setShouldLimitCPUClock(false);
              setShouldLimitGPUClock(false);
              Settings.setShouldLimitGPUClock(false);
            }
          }}>
        </ToggleField>
      </PanelSectionRow>
      <PanelSectionRow>
        <SliderField
          label={"Target FPS"}
          showValue={true}
          disabled={!autoTDP}
          min={15}
          max={refreshRate}
          value={targetFPS}
          step={1}
          valueSuffix="FPS"
          onChange={(value: number) => {
            console.log("[Frontend] Target FPS changed to:", value);
            setTargetFPS(value);
            Settings.setTargetFPS(value);
          }}>
        </SliderField>
      </PanelSectionRow>
    </PanelSection>);
  }
  else {
    sections.push(<PanelSection title="Auto Performance">
      <PanelSectionRow>
        <ToggleField
          label={"Auto TDP"}
          checked={autoTDP}
          highlightOnFocus={true}
          onChange={(value: boolean) => {
            console.log("[Frontend] Auto TDP changed to:", value);
            setAutoTDP(value);
            Settings.setAutoTDP(value);
            if (value) {
              setShouldLimitCPUClock(false);
              Settings.setShouldLimitCPUClock(false);
              setShouldLimitGPUClock(false);
              Settings.setShouldLimitGPUClock(false);
            }
          }}>
        </ToggleField>
      </PanelSectionRow>
    </PanelSection>);
  }
  
  if (!autoTDP) {
    sections.push(<PanelSection title="Performance Tweak">
      <PanelSectionRow>
        <SliderField
          label={"Max TDP"}
          showValue={true}
          disabled={autoTDP}
          min={minTDP}
          max={maxTDP}
          value={tdpLimit}
          step={1}
          valueSuffix="W"
          onChange={(value: number) => {
            userChangedMaxTDP = true;
            console.log("[Frontend] Max TDP changed to:", value);
            setTDPLimit(value);
            Settings.setTDPLimit(value);
          }}>
        </SliderField>
      </PanelSectionRow>
      <PanelSectionRow>
        <ToggleField
          label={"Turbo Boost"}
          checked={turboBoost}
          disabled={autoTDP}
          highlightOnFocus={true}
          onChange={(value: boolean) => {
            console.log("[Frontend] Turbo Boost changed to:", value);
            setTurboBoost(value);
            Settings.setTurboBoost(value);
          }}>
        </ToggleField>
      </PanelSectionRow>
      <PanelSectionRow>
        <SliderField
          label={"EPP"}
          showValue={true}
          disabled={autoTDP}
          min={0}
          max={100}
          value={epp}
          step={1}
          valueSuffix="%"
          onChange={(value: number) => {
            userChangedEPP = true;
            console.log("[Frontend] EPP changed to:", value);
            setEPP(value);
            Settings.setEPP(value);
          }}>
        </SliderField>
      </PanelSectionRow>
      <PanelSectionRow>
        <ToggleField
          label={"Limit CPU Clock"}
          disabled={autoTDP}
          checked={shouldLimitCPUClock}
          highlightOnFocus={true}
          onChange={(value: boolean) => {
            console.log("[Frontend] Should limit CPU clock changed to:", value);
            setShouldLimitCPUClock(value);
            Settings.setShouldLimitCPUClock(value);
          }}>
        </ToggleField>
      </PanelSectionRow>
      <PanelSectionRow>
        <SliderField
          label={"CPU Clock"}
          showValue={true}
          disabled={!shouldLimitCPUClock || autoTDP}
          min={cpuMinClock}
          max={cpuMaxClock}
          value={cpuClockLimit}
          step={100}
          valueSuffix="Mhz"
          onChange={(value: number) => {
            console.log("[Frontend] CPU clock limit changed to:", value);
            setCPUClockLimit(value);
            Settings.setCPUClockLimit(value);
          }}>
        </SliderField>
      </PanelSectionRow>
      <PanelSectionRow>
        <ToggleField
          label={"Limit GPU Clock"}
          checked={shouldLimitGPUClock}
          disabled={autoTDP}
          highlightOnFocus={true}
          onChange={(value: boolean) => {
            console.log("[Frontend] Should limit GPU clock changed to:", value);
            setShouldLimitGPUClock(value);
            Settings.setShouldLimitGPUClock(value);
          }}>
        </ToggleField>
      </PanelSectionRow>
      <PanelSectionRow>
        <SliderField
          label={"GPU Clock"}
          showValue={true}
          disabled={!shouldLimitGPUClock || autoTDP}
          min={gpuMinClock}
          max={gpuMaxClock}
          value={gpuClockLimit}
          step={100}
          valueSuffix="Mhz"
          onChange={(value: number) => {
            console.log("[Frontend] GPU clock limit changed to:", value);
            setGPUClockLimit(value);
            Settings.setGPUClockLimit(value);
          }}>
        </SliderField>
      </PanelSectionRow>
    </PanelSection>);
  }
  
  sections.push(<PanelSection title="AMD">
      <PanelSectionRow>
        <ToggleField
          label={"Radeon Super Resolution"}
          checked={radeonSuperResolution}
          disabled={false}
          highlightOnFocus={true}
          onChange={(value: boolean) => {
            console.log("[Frontend] Radeon Super Resolution changed to:", value);
            setRadeonSuperResolution(value);
            Settings.setRadeonSuperResolution(value);
            if (value) {
              if (!gpuScaling) {
                setGPUScaling(true);
              }
              if (!Settings.getGPUScaling()) {
                Settings.syncGPUScaling(true);
              }
            }
          }}>
        </ToggleField>
        <SliderField
          label={"Sharpness"}
          showValue={true}
          disabled={!radeonSuperResolution}
          min={0}
          max={100}
          value={radeonSuperResolutionSharpness}
          step={1}
          valueSuffix="%"
          onChange={(value: number) => {
            console.log("[Frontend] Radeon Super Resolution Sharpness changed to:", value);
            setRadeonSuperResolutionSharpness(value);
            Settings.setRadeonSuperResolutionSharpness(value);
          }}>
        </SliderField>
        <ToggleField
          label={"AMD Fluid Motion Frame"}
          checked={amdFluidMotionFrame}
          disabled={false}
          highlightOnFocus={true}
          onChange={(value: boolean) => {
            console.log("[Frontend] AMD Fluid Motion Frame changed to:", value);
            setAMDFluidMotionFrame(value);
            Settings.setAMDFluidMotionFrame(value);
            if (value) {
              if (!radeonAntiLag) {
                setRadeonAntiLag(true);
              }
              if (!Settings.getRadeonAntiLag()) {
                Settings.setRadeonAntiLag(true);
              }
            }
          }}>
        </ToggleField>
        <ToggleField
          label={"Radeon Anti Lag"}
          checked={radeonAntiLag}
          disabled={false}
          highlightOnFocus={true}
          onChange={(value: boolean) => {
            console.log("[Frontend] Radeon Anti Lag changed to:", value);
            setRadeonAntiLag(value);
            Settings.setRadeonAntiLag(value);
            if (value) {
              if (radeonChill) {
                setRadeonChill(false);
              }
              if (Settings.getRadeonChill()) {
                Settings.syncRadeonChill(false);
              }
            }
          }}>
        </ToggleField>
        <ToggleField
          label={"Radeon Boost"}
          checked={radeonBoost}
          disabled={false}
          highlightOnFocus={true}
          onChange={(value: boolean) => {
            console.log("[Frontend] Radeon Boost changed to:", value);
            setRadeonBoost(value);
            Settings.setRadeonBoost(value);
            if (value) {
              if (radeonChill) {
                setRadeonChill(false);
              }
              if (Settings.getRadeonChill()) {
                Settings.syncRadeonChill(false);
              }
            }
          }}>
        </ToggleField>
        <ToggleField
          label={"Radeon Chill"}
          checked={radeonChill}
          disabled={false}
          highlightOnFocus={true}
          onChange={(value: boolean) => {
            console.log("[Frontend] Radeon Chill changed to:", value);
            setRadeonChill(value);
            Settings.setRadeonChill(value);
            if (value) {
              if (radeonAntiLag) {
                setRadeonAntiLag(false);
              }
              if (Settings.getRadeonAntiLag()) {
                Settings.syncRadeonAntiLag(false);
              }
              if (radeonBoost) {
                setRadeonBoost(false);
              }
              if (Settings.getRadeonBoost()) {
                Settings.syncRadeonBoost(false);
              }
            }
          }}>
        </ToggleField>
        <SliderField
          label={"Radeon Chill Min FPS"}
          showValue={true}
          disabled={!radeonChill}
          min={30}
          max={300}
          value={radeonChillMinFPS}
          step={1}
          valueSuffix="FPS"
          onChange={(value: number) => {
            console.log("[Frontend] Radeon Chill Min FPS changed to:", value);
            setRadeonChillMinFPS(value);
            Settings.setRadeonChillMinFPS(value);
            if (value > radeonChillMaxFPS) {
              // console.log("[Frontend] Radeon Chill Min FPS is greater than Max FPS, setting Max FPS to Min FPS");
              setRadeonChillMaxFPS(value);
              Settings.setRadeonChillMaxFPS(value);
            }
          }}>
        </SliderField>
        <SliderField
          label={"Radeon Chill Max FPS"}
          showValue={true}
          disabled={!radeonChill}
          min={30}
          max={300}
          value={radeonChillMaxFPS}
          step={1}
          valueSuffix="FPS"
          onChange={(value: number) => {
            console.log("[Frontend] Radeon Chill Max FPS changed to:", value);
            setRadeonChillMaxFPS(value);
            Settings.setRadeonChillMaxFPS(value);
            if (value < radeonChillMinFPS) {
              // console.log("[Frontend] Radeon Chill Max FPS is less than Min FPS, setting Min FPS to Max FPS");
              setRadeonChillMinFPS(value);
              Settings.setRadeonChillMinFPS(value);
            }
          }}>
        </SliderField>
        <ToggleField
          label={"GPU Scaling"}
          checked={gpuScaling}
          disabled={false}
          highlightOnFocus={true}
          onChange={(value: boolean) => {
            console.log("[Frontend] GPU Scaling changed to:", value);
            setGPUScaling(value);
            Settings.setGPUScaling(value);
            if (!value) {
              if (radeonSuperResolution) {
                setRadeonSuperResolution(false);
              }
              if (Settings.getRadeonSuperResolution()) {
                Settings.syncRadeonSuperResolution(false);
              }
            }
          }}>
        </ToggleField>
        <DropdownItem
          label={"Scaling Mode"}
          disabled={!gpuScaling}
          selectedOption={scalingModes.findIndex(mode => mode.data == scalingMode)}
          rgOptions={scalingModes.map(mode => ({
            data: mode.data,
            label: mode.label
          })) as DropdownOption[]}
          onChange={(option) => {
            console.log("[Frontend] Scaling Mode changed to:", option.label);
            setScalingMode(option.data);
            Settings.setScalingMode(option.data);
          }}
        >
        </DropdownItem>
        <ToggleField
          label={"Integer Scaling"}
          checked={integerScaling}
          disabled={!gpuScaling}
          highlightOnFocus={true}
          onChange={(value: boolean) => {
            console.log("[Frontend] Integer Scaling changed to:", value);
            setIntegerScaling(value);
            Settings.setIntegerScaling(value);
          }}>
        </ToggleField>
      </PanelSectionRow>
    </PanelSection>);

  const onClickStartLosslessScaling = async () => {
    console.log("[Frontend] Starting Lossless Scaling...");
    setLosslessScalingState(LosslessScalingRunState.Starting);
    Settings.syncLosslessScalingState(LosslessScalingRunState.Starting);
    await restartLosslessScalingFunc();
  };

  const onClickAddProfile = async () => {
    let addResult = await addLosslessScalingProfileFunc(currentGameName, currentGamePath);
    if (addResult) {
      setLosslessScalingProfileNames([...losslessScalingProfileNames, currentGameName]);
      setLosslessScalingProfileName(currentGameName);
      Settings.syncLosslessScalingProfileName(currentGameName);
      setIsLosslessScalingConfigured(true);
    }
  }
  
  if (losslessScalingState == LosslessScalingRunState.Running) {
    sections.push(<PanelSection title="Lossless Scaling">
      <PanelSectionRow>
        <DropdownItem
          label={"Profiles"}
          selectedOption={losslessScalingProfileName}
          rgOptions={losslessScalingProfileNames.map(profileName => ({
            data: profileName,
            label: profileName
          })) as DropdownOption[]}
          onChange={(option) => {
            console.log("[Frontend] Lossless Scaling profile changed to:", option.data);
            setLosslessScalingProfileName(option.data);
            Settings.syncLosslessScalingProfileName(option.data);
            getLosslessScalingProfileByNameFunc(losslessScalingProfileName).then(onLosslessScalingProfileChanged);
          }}>
        </DropdownItem>
      </PanelSectionRow>
      {
        !isLosslessScalingConfigured ? 
        (
          <PanelSectionRow>
            <ButtonItem
              layout={"below"}
              highlightOnFocus={true}
              onClick={onClickAddProfile}
            >
              {"Add " + currentGameName}
            </ButtonItem>
          </PanelSectionRow>
        )
        :
        null
      }
      <PanelSectionRow>
        <ToggleField
          label={"Auto Scale"}
          checked={autoScale}
          disabled={false}
          highlightOnFocus={true}
          onChange={(value: boolean) => {
            console.log("[Frontend] Auto Scale changed to:", value);
            setAutoScale(value);
            Settings.syncLosslessScalingAutoScale(value);
            setLosslessScalingProfileByNameFunc(losslessScalingProfileName, "AutoScale", value ? "true" : "false").then(() => {
              console.log("[Frontend] Lossless Scaling profile updated with Auto Scale:", value);
            }).catch((error) => {
              console.error("[Frontend] Error updating Lossless Scaling profile with Auto Scale:", error);
            });
          }}>
        </ToggleField>
      </PanelSectionRow>
      <PanelSectionRow>
        <SliderField
          label={"Auto Scale Delay"}
          showValue={true}
          disabled={!autoScale}
          min={0}
          max={20}
          value={autoScaleDelay}
          step={1}
          valueSuffix=" Seconds"
          onChange={(value: number) => {
            console.log("[Frontend] Auto Scale Delay changed to:", value);
            setAutoScaleDelay(value);
            Settings.syncLosslessScalingAutoScaleDelay(value);
            setLosslessScalingProfileByNameFunc(losslessScalingProfileName, "AutoScaleDelay", value.toString()).then(() => {
              console.log("[Frontend] Lossless Scaling profile updated with Auto Scale Delay:", value);
            }).catch((error) => {
              console.error("[Frontend] Error updating Lossless Scaling profile with Auto Scale Delay:", error);
            });
          }}>
        </SliderField>
      </PanelSectionRow>
      <PanelSectionRow>
        <DropdownItem
          label={"Frame Gen"}
          disabled={false}
          selectedOption={losslessScalingFrameGenOptions.findIndex(option => option.data == frameGen)}
          rgOptions={losslessScalingFrameGenOptions.map(option => ({
            data: option.data,
            label: option.label
          })) as DropdownOption[]}
          onChange={(option) => {
            console.log("[Frontend] Lossless Scaling frame gen changed to:", option.data);
            setFrameGen(option.data);
            Settings.syncLosslessScalingFrameGen(option.data);
            let optionLabel = option.label?.toString() || "Off";
            setLosslessScalingProfileByNameFunc(losslessScalingProfileName, "FrameGeneration", optionLabel).then(() => {
              console.log("[Frontend] Lossless Scaling profile updated with Frame Generation:", optionLabel);
            }).catch((error) => {
              console.error("[Frontend] Error updating Lossless Scaling profile with Frame Generation:", error);
            });
          }}>
        </DropdownItem>
      </PanelSectionRow>
      {
      frameGen == 1 ?
        (<PanelSectionRow>
          <DropdownItem
            label={"LSFG3 Mode"}
            disabled={false}
            selectedOption={losslessScalingFrameGen3Mode1Options.findIndex(option => option.data == frameGen3Mode1)}
            rgOptions={losslessScalingFrameGen3Mode1Options.map(option => ({
              data: option.data,
              label: option.label
            })) as DropdownOption[]}
            onChange={(option) => {
              console.log("[Frontend] Lossless Scaling frame gen 3 mode changed to:", option.data);
              setFrameGen3Mode1(option.data);
              Settings.syncLosslessScalingFrameGen3Mode1(option.data);
              let optionLabel = option.label?.toString() || "FIXED";
              setLosslessScalingProfileByNameFunc(losslessScalingProfileName, "LSFG3Mode1", optionLabel).then(() => {
                console.log("[Frontend] Lossless Scaling profile updated with Frame Generation 3:", optionLabel);
              }).catch((error) => {
                console.error("[Frontend] Error updating Lossless Scaling profile with Frame Generation 3:", error);
              });
            }}>
          </DropdownItem>
        </PanelSectionRow>)
      :
        (
          frameGen == 2 ?
            <PanelSectionRow>
              <DropdownItem
                label={"LSFG2 Mode"}
                disabled={false}
                selectedOption={losslessScalingFrameGen2ModeOptions.findIndex(option => option.data == frameGen2Mode)}
                rgOptions={losslessScalingFrameGen2ModeOptions.map(option => ({
                  data: option.data,
                  label: option.label
                })) as DropdownOption[]}
                onChange={(option) => {
                  console.log("[Frontend] Lossless Scaling frame gen changed to:", option.data);
                  setFrameGen2Mode(option.data);
                  Settings.syncLosslessScalingFrameGen2Mode(option.data);
                  let optionLabel = option.label?.toString() || "X2";
                  setLosslessScalingProfileByNameFunc(losslessScalingProfileName, "LSFG2Mode", optionLabel).then(() => {
                    console.log("[Frontend] Lossless Scaling profile updated with Frame Generation 2:", optionLabel);
                  }).catch((error) => {
                    console.error("[Frontend] Error updating Lossless Scaling profile with Frame Generation 2:", error);
                  });
                }}>
              </DropdownItem>
            </PanelSectionRow>
            :
            null
        )
      }
      {
      frameGen == 1 ? 
        (
          frameGen3Mode1 == 0 ? 
            <SliderField
              label={"LSFG3 Multiplier"}
              showValue={true}
              disabled={false}
              min={1}
              max={10}
              value={frameGen3Multiplier}
              step={1}
              valueSuffix="X"
              onChange={(value: number) => {
                console.log("[Frontend] LSFG3 Multipler:", value);
                setFrameGen3Multiplier(value);
                Settings.syncLosslessScalingFrameGen3Multiplier(value);
                setLosslessScalingProfileByNameFunc(losslessScalingProfileName, "LSFG3Multiplier", value.toString()).then(() => {
                  console.log("[Frontend] Lossless Scaling profile updated with LSFG3Multiplier:", value);
                }).catch((error) => {
                  console.error("[Frontend] Error updating Lossless Scaling profile with LSFG3Multiplier:", error);
                });
              }}>
            </SliderField>
            :
            <SliderField
              label={"LSFG3 Target"}
              showValue={true}
              disabled={false}
              min={20}
              max={120}
              value={frameGen3Target}
              step={1}
              valueSuffix=" FPS"
              onChange={(value: number) => {
                console.log("[Frontend] LSFG3 Target changed to:", value);
                setFrameGen3Target(value);
                Settings.syncLosslessScalingFrameGen3Target(value);
                setLosslessScalingProfileByNameFunc(losslessScalingProfileName, "LSFG3Target", value.toString()).then(() => {
                  console.log("[Frontend] Lossless Scaling profile updated with LSFG3Target:", value);
                }).catch((error) => {
                  console.error("[Frontend] Error updating Lossless Scaling profile with LSFG3Target:", error);
                });
              }}>
            </SliderField>
        )
        :
        null
      }
      {
      frameGen == 1 || frameGen == 2 ?
       (
        <PanelSectionRow>
          <SliderField
            label={"Flow Scale"}
            showValue={true}
            disabled={false}
            min={25}
            max={100}
            value={frameGenFlowScale}
            step={5}
            valueSuffix="%"
            onChange={(value: number) => {
              console.log("[Frontend] Flow Ccale changed to:", value);
              setFrameGenFlowScale(value);
              Settings.syncLosslessScalingFrameGenFlowScale(value);
              setLosslessScalingProfileByNameFunc(losslessScalingProfileName, "LSFGFlowScale", value.toString()).then(() => {
                console.log("[Frontend] Lossless Scaling profile updated with LSFGFlowScale:", value);
              }).catch((error) => {
                console.error("[Frontend] Error updating Lossless Scaling profile with LSFGFlowScale:", error);
              });
            }}>
          </SliderField>
          <ToggleField
            label={"Performance"}
            checked={frameGenPerformance}
            disabled={false}
            highlightOnFocus={true}
            onChange={(value: boolean) => {
              console.log("[Frontend] FrameGen Performance changed to:", value);
              setFrameGenPerformance(value);
              Settings.syncLosslessScalingFrameGenPerformance(value);
              setLosslessScalingProfileByNameFunc(losslessScalingProfileName, "LSFGSize", value ? "PERFORMANCE" : "BALANCED").then(() => {
                console.log("[Frontend] Lossless Scaling profile updated with LSFGSize:", value);
              }).catch((error) => {
                console.error("[Frontend] Error updating Lossless Scaling profile with LSFGSize:", error);
              });
            }}>
          </ToggleField>
        </PanelSectionRow>
       )
       :
       null 
      }
      <PanelSectionRow>
        <ToggleField
          label={"Draw FPS"}
          checked={drawFPS}
          disabled={false}
          highlightOnFocus={true}
          onChange={(value: boolean) => {
            console.log("[Frontend] Draw FPS changed to:", value);
            setDrawFPS(value);
            Settings.syncLosslessScalingDrawFPS(value);
            setLosslessScalingProfileByNameFunc(losslessScalingProfileName, "DrawFps", value ? "true" : "false").then(() => {
              console.log("[Frontend] Lossless Scaling profile updated with Draw FPS:", value);
            }).catch((error) => {
              console.error("[Frontend] Error updating Lossless Scaling profile with Draw FPS:", error);
            });
          }}>
        </ToggleField>
      </PanelSectionRow>
      <PanelSectionRow>
        <ButtonItem
          layout={"below"}
          highlightOnFocus={true}
          onClick={onClickStartLosslessScaling}
        >
          {"Restart Lossless Scaling"}
        </ButtonItem>
      </PanelSectionRow>
    </PanelSection>);
  }
  else if (losslessScalingState == LosslessScalingRunState.Starting) {
    sections.push(<PanelSection title="Starting Lossless Scaling">
      <PanelSectionRow>
      </PanelSectionRow>
    </PanelSection>);
  }
  else if (losslessScalingState == LosslessScalingRunState.Closed) {
    sections.push(<PanelSection title="Lossless Scaling">
      <PanelSectionRow>
        <ButtonItem
          layout={"below"}
          highlightOnFocus={true}
          onClick={onClickStartLosslessScaling}
        >
          {"Start Lossless Scaling"}
        </ButtonItem>
      </PanelSectionRow>
    </PanelSection>);
  }

  return sections;
};

export default definePlugin(() => {
  console.log("Template plugin initializing, this is called once on frontend startup")

  // serverApi.routerHook.addRoute("/decky-plugin-test", DeckyPluginRouterTest, {
  //   exact: true,
  // });

  return {
    // The name shown in various decky menus
    name: "Decky Windows Tools",
    // The element displayed at the top of your plugin's menu
    titleView: <div className={staticClasses.Title}>Decky Windows Tools</div>,
    // The content of your plugin's menu
    content: <Content />,
    // The icon displayed in the plugin list
    icon: <FaRegWindowRestore />,
    // The function triggered when your plugin unloads
    onDismount() {
      console.log("Unloading")
      // serverApi.routerHook.removeRoute("/decky-plugin-test");
    },
  };
});
