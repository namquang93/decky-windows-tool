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
