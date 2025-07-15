import {
  //ButtonItem,
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
import { Settings } from "./util";
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
// const start_syncing_ryzen = callable<[], void>("start_syncing_ryzen");

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

function Content() {
  // start_syncing_ryzen();

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

  // Listen to HWInfo
  const [fps, setFPS] = useState<number>(0);
  const [fpsRatio, setFPSRatio] = useState<number>(fps * 100.0);
  const [cpuClock, setCPUClock] = useState<number>(1000);
  const [cpuUsage, setCPUUsage] = useState<number>(50);
  const [gpuClock, setGPUClock] = useState<number>(500);
  const [gpuUsage, setGPUUsage] = useState<number>(50);
  function onSystemStatistics(newFPS: number, newCPUClock: number, newCPUUsage: number, newGPUClock: number, newGPUUsage: number) {
    console.log("[Frontend] newFPS: ", newFPS, " newCPUClock: ", newCPUClock, " newGPUClock: ", newGPUClock, " new CPUUsage: ", newCPUUsage, " newGPUUsage; ", newGPUUsage);
    setFPS(newFPS);
    setFPSRatio(newFPS * 100.0 / 60)
    setCPUClock(newCPUClock);
    setCPUUsage(newCPUUsage);
    setGPUClock(newGPUClock);
    setGPUUsage(newGPUUsage);
  };

  useEffect(() => {
    addEventListener('sytem_statistics_event', onSystemStatistics);
    return () => {
      removeEventListener('sytem_statistics_event', onSystemStatistics);
    }
  }, []);

  let userChangedVolume = false;
  useEffect(() => {
    getVolumeFunc().then((value) => {
      console.log("[Frontend] Got volume value:", value);
      if (!userChangedVolume) {
        setVolume(value);
        Settings.syncVolume(value);
      }
    });
  }, []);

  let userChangedMuted = false;
  useEffect(() => {
    getMutedFunc().then((value) => {
      console.log("[Frontend] Got muted value:", value);
      if (!userChangedMuted) {
        setMuted(value);
        Settings.syncMuted(value);
      }
    });
  }, []);

  let userChangedBrightness = false;
  useEffect(() => {
    getBrightnessFunc().then((value) => {
      if (!userChangedBrightness) {
        console.log("[Frontend] Got brightness value:", value);
        setBrightness(value);
        Settings.syncBrightness(value);
      }
    });
  }, []);

  let userChangedOSD = false;
  useEffect(() => {
    getOSDFunc().then((value) => {
      if (!userChangedOSD) {
        console.log("[Frontend] Got OSD value:", value);
        setOSD(value);
        Settings.syncOSD(value);
      }
    });
  }, []);

  let userChangedOSDSize = false;
  useEffect(() => {
    getOSDSizeFunc().then((value) => {
      if (!userChangedOSDSize) {
        console.log("[Frontend] Got OSD size value:", value);
        setOSDSize(value);
        Settings.syncOSDSize(value);
      }
    });
  }, []);

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

  // useEffect(() => {
  //   getRadeonSuperResolutionFunc().then((value) => {
  //     console.log("[Frontend] Got Radeon Super Resolution:", value);
  //     setRadeonSuperResolution(value);
  //     Settings.syncRadeonSuperResolution(value);
  //   });
  // }, []);

  // useEffect(() => {
  //   getRadeonSuperResolutionSharpnessFunc().then((value) => {
  //     console.log("[Frontend] Got Radeon Super Resolution Sharpness:", value);
  //     setRadeonSuperResolutionSharpness(value);
  //     Settings.syncRadeonSuperResolutionSharpness(value);
  //   });
  // }, []);

  // useEffect(() => {
  //   getAMDFluidMotionFrameFunc().then((value) => {
  //     console.log("[Frontend] Got AMD Fluid Motion Frame:", value);
  //     setAMDFluidMotionFrame(value);
  //     Settings.syncAMDFluidMotionFrame(value);
  //   });
  // }, []);

  // useEffect(() => {
  //   getRadeonAntiLagFunc().then((value) => {
  //     console.log("[Frontend] Got Radeon Anti Lag:", value);
  //     setRadeonAntiLag(value);
  //     Settings.syncRadeonAntiLag(value);
  //   });
  // }, []);

  // useEffect(() => {
  //   getRadeonBoostFunc().then((value) => {
  //     console.log("[Frontend] Got Radeon Boost:", value);
  //     setRadeonBoost(value);
  //     Settings.syncRadeonBoost(value);
  //   });
  // }, []);

  // useEffect(() => {
  //   getRadeonChillFunc().then((value) => {
  //     console.log("[Frontend] Got Radeon Chill:", value);
  //     setRadeonChill(value);
  //     Settings.syncRadeonChill(value);
  //   });
  // }, []);

  // useEffect(() => {
  //   getRadeonChillMinFPSFunc().then((value) => {
  //     console.log("[Frontend] Got Radeon Chill Min FPS:", value);
  //     setRadeonChillMinFPS(value);
  //     Settings.syncRadeonChillMinFPS(value);
  //   });
  // }, []);

  // useEffect(() => {
  //   getRadeonChillMaxFPSFunc().then((value) => {
  //     console.log("[Frontend] Got Radeon Chill Max FPS:", value);
  //     setRadeonChillMaxFPS(value);
  //     Settings.syncRadeonChillMaxFPS(value);
  //   });
  // }, []);

  // useEffect(() => {
  //   getGPUScalingFunc().then((value) => {
  //     console.log("[Frontend] Got GPU Scaling:", value);
  //     setGPUScaling(value);
  //     Settings.syncGPUScaling(value);
  //   });
  // }, []);

  // useEffect(() => {
  //   getScalingModeFunc().then((value) => {
  //     console.log("[Frontend] Got Scaling Mode:", value);
  //     setScalingMode(value);
  //     Settings.syncScalingMode(value);
  //   });
  // }, []);

  // useEffect(() => {
  //   getIntegerScalingFunc().then((value) => {
  //     console.log("[Frontend] Got Integer Scaling:", value);
  //     setIntegerScaling(value);
  //     Settings.syncIntegerScaling(value);
  //   });
  // }, []);

  return [
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
            userChangedVolume = true;
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
            userChangedMuted = true;
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
            userChangedBrightness = true;
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
    </PanelSection>,
    <PanelSection title="OSD">
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
            userChangedOSD = true;
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
            userChangedOSDSize = true;
            console.log("[Frontend] OSD size changed to:", value);
            setOSDSize(value);
            Settings.setOSDSize(value);
          }}>
        </SliderField>
      </PanelSectionRow>
    </PanelSection>,
    <PanelSection title="Performance">
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
    </PanelSection>,
    <PanelSection title="AMD">
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
    </PanelSection>,
    <PanelSection title="Lossless Scaling">
      <PanelSectionRow>
        <ToggleField
          label={"Enable"}
          checked={false}
          disabled={false}
          highlightOnFocus={true}
          onChange={(value: boolean) => {
            console.log("[Frontend] Enable Lossless Scaling:", value);
          }}>
        </ToggleField>
      </PanelSectionRow>
    </PanelSection>,
    <PanelSection title="Monitoring">
      <PanelSectionRow>
        <ProgressBarWithInfo
          label={"CPU"}
          indeterminate={false}
          nProgress={cpuUsage}
          focusable={true}
          sOperationText={cpuClock + " Mhz"}
          >
        </ProgressBarWithInfo>
      </PanelSectionRow>
      <PanelSectionRow>
        <ProgressBarWithInfo
          label={"GPU"}
          indeterminate={false}
          nProgress={gpuUsage}
          focusable={true}
          sOperationText={gpuClock + " Mhz"}
          >
        </ProgressBarWithInfo>
      </PanelSectionRow>
      <PanelSectionRow>
        <ProgressBarWithInfo
          label={"FPS"}
          indeterminate={false}
          nProgress={fpsRatio}
          focusable={true}
          sOperationText={Math.round(fps) + " FPS"}
          >
        </ProgressBarWithInfo>
      </PanelSectionRow>
    </PanelSection>
  ];
};

export default definePlugin(() => {
  console.log("Template plugin initializing, this is called once on frontend startup")

  // serverApi.routerHook.addRoute("/decky-plugin-test", DeckyPluginRouterTest, {
  //   exact: true,
  // });

  // Add an event listener to the "timer_event" event from the backend
  const listener = addEventListener<[
    tdp_name: string,
    tdp_value: boolean
  ]>("tdp_event", (tdp_name, tdp_value) => {
    console.log("tdp_event with:", tdp_name, tdp_value)
    toaster.toast({
      title: "got tdp_event",
      body: `${tdp_name}, ${tdp_value}`
    });
  });

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
      removeEventListener("tdp_event", listener);
      // serverApi.routerHook.removeRoute("/decky-plugin-test");
    },
  };
});
