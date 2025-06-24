import {
  //ButtonItem,
  PanelSection,
  PanelSectionRow,
  SliderField,
  //Dropdown,
  DropdownItem,
  DropdownOption,
  ToggleField,
  //DropdownItemProps,
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

let getVolumeFunc = callable<[], number>('get_volume');
Settings.syncVolume(await getVolumeFunc());

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
let getMaxTDPFunc = callable<[], number>('get_max_tdp')
Settings.syncMaxTDP(await getMaxTDPFunc());
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

let getGPUClockLimitFunc = callable<[], number>('get_gpu_clock');
Settings.syncGPUClockLimit(await getGPUClockLimitFunc());
Settings.setShouldLimitGPUClock(false);

function Content() {
  // start_syncing_ryzen();

  const [volume, setVolume] = useState<number>(
    Settings.getVolume()
  );
  const [brightness, setBrightness] = useState<number>(
    Settings.getBrightness()
  );
  const [osd, setOSD] = useState<number>(
    Settings.getOSD()
  );
  const [osdSize, setOSDSize] = useState<number>(
    Settings.getOSDSize()
  );
  const [maxTDP, setMaxTDP] = useState<number>(
    Settings.getMaxTDP()
  );
  const [refreshRate, setRefreshRate] = useState<number>(
    Settings.getRefreshRate()
  );
  const [turboBoost, setTurboBoost] = useState<boolean>(
    Settings.getTurboBoost()
  );
  const [epp, setEPP] = useState<number>(
    Settings.getEPP()
  );
  const [shouldLimitCPUClock, setShouldLimitCPUClock] = useState<boolean>(
    Settings.getShouldLimitCPUClock()
  );
  const [cpuClockLimit, setCPUClockLimit] = useState<number>(
    Settings.getCPUClockLimit()
  );
  const [shouldLimitGPUClock, setShouldLimitGPUClock] = useState<boolean>(
    Settings.getShouldLimitGPUClock()
  );
  const [gpuClockLimit, setGPUClockLimit] = useState<number>(
    Settings.getGPUClockLimit()
  );

  console.log("[Frontend] Initial values:")

  useEffect(() => {
    getVolumeFunc().then((value) => {
      console.log("[Frontend] Got volume value:", value);
      setVolume(value);
      Settings.syncVolume(value);
    });
  }, []);

  useEffect(() => {
    getBrightnessFunc().then((value) => {
      console.log("[Frontend] Got brightness value:", value);
      setBrightness(value);
      Settings.syncBrightness(value);
    });
  }, []);

  useEffect(() => {
    getOSDFunc().then((value) => {
      console.log("[Frontend] Got OSD value:", value);
      setOSD(value);
      Settings.syncOSD(value);
    });
  }, []);

  useEffect(() => {
    getOSDSizeFunc().then((value) => {
      console.log("[Frontend] Got OSD size value:", value);
      setOSDSize(value);
      Settings.syncOSDSize(value);
    });
  }, []);

  useEffect(() => {
    getMaxTDPFunc().then((value) => {
      console.log("[Frontend] Got TDP value:", value);
      if (value > 3) {
        setMaxTDP(value);
        Settings.syncMaxTDP(value);
      }
      else {
        console.warn("[Frontend] Invalid TDP value received:", value);
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

  useEffect(() => {
    getEPPFunc().then((value) => {
      console.log("[Frontend] Got EPP value:", value);
      setEPP(value);
      Settings.syncEPP(value);
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
            console.log("[Frontend] Volume changed to:", value);
            setVolume(value);
            Settings.setVolume(value);
          }}>
        </SliderField>
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
            console.log("[Frontend] OSD size changed to:", value);
            setOSDSize(value);
            Settings.setOSDSize(value);
          }}>
        </SliderField>
      </PanelSectionRow>
    </PanelSection>,
    <PanelSection title="Performance">
      <PanelSectionRow>
        <SliderField
          label={"Max TDP"}
          showValue={true}
          min={4}
          max={28}
          value={maxTDP}
          step={1}
          valueSuffix="W"
          onChange={(value: number) => {
            console.log("[Frontend] Max TDP changed to:", value);
            setMaxTDP(value);
            Settings.setMaxTDP(value);
          }}>
        </SliderField>
        <ToggleField
          label={"Turbo Boost"}
          checked={turboBoost}
          highlightOnFocus={true}
          onChange={(value: boolean) => {
            console.log("[Frontend] Turbo Boost changed to:", value);
            setTurboBoost(value);
            Settings.setTurboBoost(value);
          }}>
        </ToggleField>
        <SliderField
          label={"EPP"}
          showValue={true}
          min={0}
          max={100}
          value={epp}
          step={1}
          valueSuffix="%"
          onChange={(value: number) => {
            console.log("[Frontend] EPP changed to:", value);
            setEPP(value);
            Settings.setEPP(value);
          }}>
        </SliderField>
        <ToggleField
          label={"Limit CPU Clock"}
          checked={shouldLimitCPUClock}
          highlightOnFocus={true}
          onChange={(value: boolean) => {
            console.log("[Frontend] Should limit CPU clock changed to:", value);
            setShouldLimitCPUClock(value);
            Settings.setShouldLimitCPUClock(value);
          }}>
        </ToggleField>
        <SliderField
          label={"CPU Clock"}
          showValue={true}
          disabled={!shouldLimitCPUClock}
          min={800}
          max={4400}
          value={cpuClockLimit}
          step={100}
          valueSuffix="Mhz"
          onChange={(value: number) => {
            console.log("[Frontend] CPU clock limit changed to:", value);
            setCPUClockLimit(value);
            Settings.setCPUClockLimit(value);
          }}>
        </SliderField>
        <ToggleField
          label={"Limit GPU Clock"}
          checked={shouldLimitGPUClock}
          highlightOnFocus={true}
          onChange={(value: boolean) => {
            console.log("[Frontend] Should limit GPU clock changed to:", value);
            setShouldLimitGPUClock(value);
            Settings.setShouldLimitGPUClock(value);
          }}>
        </ToggleField>
        <SliderField
          label={"GPU Clock"}
          showValue={true}
          disabled={!shouldLimitGPUClock}
          min={200}
          max={3000}
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
