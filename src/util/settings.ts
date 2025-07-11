// import {
//   JsonObject,
//   JsonProperty,
//   JsonSerializer,
// } from "typescript-json-serializer";

import { callable } from "@decky/api";

//const SETTINGS_KEY = "DeckyWindowsTools";
//const serializer = new JsonSerializer();

const set_volume = callable<[number], void>('set_volume');
const set_muted = callable<[boolean], void>('set_muted');
const set_brightness = callable<[number], void>('set_brightness');
const set_osd = callable<[number], void>('set_osd');
const set_osd_size = callable<[number], void>('set_osd_size');
const set_tdp_limit = callable<[number], void>('set_tdp_limit');
const set_refresh_rate = callable<[number], void>('set_refresh_rate');
const set_turbo_boost = callable<[boolean], void>('set_turbo_boost');
const set_epp = callable<[number], void>('set_epp');
const set_cpu_clock_limit = callable<[number], void>('set_cpu_clock_limit');
const set_gpu_clock_limit = callable<[number], void>('set_gpu_clock_limit');
const set_auto_tdp = callable<[boolean], void>('set_auto_tdp');

//@JsonObject()
export class SystemSetting {
  //@JsonProperty()
  public volume: number;

  //@JsonProperty()
  public muted: boolean;

  //@JsonProperty()
  public brightness: number;

  //@JsonProperty()
  public osd: number;

  //@JsonProperty()
  public osdSize: number;

  //@JsonProperty()
  public tdpLimit: number;

  //@JsonProperty()
  public refreshRate: number;

  //@JsonProperty()
  public turboBoost: boolean;

  //@JsonProperty()
  public epp: number;

  //@JsonProperty()
  public shouldLimitCPUClock: boolean;

  //@JsonProperty()
  public cpuClockLimit: number;

  //@JsonProperty()
  public shouldLimitGPUClock: boolean;

  //@JsonProperty()
  public gpuClockLimit: number;

  //@JsonProperty()
  public autoTDP: boolean;

  constructor() {
    this.volume = 20;
    this.muted = false;
    this.brightness = 50;
    this.osd = 0;
    this.osdSize = 1;
    this.tdpLimit = 10;
    this.refreshRate = 60;
    this.turboBoost = true;
    this.epp = 80;
    this.cpuClockLimit = 2400;
    this.shouldLimitCPUClock = false;
    this.shouldLimitGPUClock = false;
    this.gpuClockLimit = 800;
    this.autoTDP = true;
    set_auto_tdp(true);
  }

  deepCopy(copyTarget: SystemSetting) {
    // this.overwrite=copyTarget.overwrite;
    this.volume = copyTarget.volume;
    this.muted = copyTarget.muted;
    this.brightness = copyTarget.brightness;
    this.osd = copyTarget.osd;
    this.osdSize = copyTarget.osdSize;
    this.tdpLimit = copyTarget.tdpLimit;
    this.refreshRate = copyTarget.refreshRate;
    this.turboBoost = copyTarget.turboBoost;
    this.epp = copyTarget.epp;
    this.cpuClockLimit = copyTarget.cpuClockLimit;
    this.shouldLimitCPUClock = copyTarget.shouldLimitCPUClock;
    this.shouldLimitGPUClock = copyTarget.shouldLimitGPUClock;
    this.gpuClockLimit = copyTarget.gpuClockLimit;
    this.autoTDP = copyTarget.autoTDP;
  }
}

export class Settings {
  private static _instance: Settings = new Settings();

  public system: SystemSetting;

  constructor() {
    this.system = new SystemSetting();
  }

  static get instance(): Settings {
    if (!this._instance) {
      console.log("Creating new Settings instance");
      this._instance = new Settings();
    }
    
    return this._instance;
  }

  // private settingChangeEvent = new EventTarget();

  static setVolume(volume: number) {
    if (this.instance.system.volume != volume) {
      this.instance.system.volume = volume;
      set_volume(volume);
      // Settings.saveSettingsToLocalStorage();
    }
  }

  static syncVolume(volume: number) {
    if (this.instance.system.volume != volume) {
      this.instance.system.volume = volume;
    }
  }

  static getVolume() {
    return this.instance.system.volume;
  }

  static getMuted() {
    return this.instance.system.muted;
  }

  static setMuted(muted: boolean) {
    if (this.instance.system.muted != muted) {
      this.instance.system.muted = muted;
      set_muted(muted);
      // Settings.saveSettingsToLocalStorage();
    }
  }

  static syncMuted(muted: boolean) {
    if (this.instance.system.muted != muted) {
      this.instance.system.muted = muted;
    }
  }

  static setBrightness(brightness: number) {
    if (this.instance.system.brightness != brightness) {
      this.instance.system.brightness = brightness;
      set_brightness(brightness);
      // Settings.saveSettingsToLocalStorage();
    }
  }

  static syncBrightness(brightness: number) {
    if (this.instance.system.brightness != brightness) {
      this.instance.system.brightness = brightness;
    }
  }

  static getBrightness() {
    return this.instance.system.brightness;
  }

  static getOSD() {
    return this.instance.system.osd;
  }

  static setOSD(osd: number) {
    if (this.instance.system.osd != osd) {
      this.instance.system.osd = osd;
      set_osd(osd);
      // Settings.saveSettingsToLocalStorage();
    }
  }

  static syncOSD(osd: number) {
    if (this.instance.system.osd != osd) {
      this.instance.system.osd = osd;
    }
  }

  static getOSDSize() {
    return this.instance.system.osdSize;
  }

  static setOSDSize(osdSize: number) {
    if (this.instance.system.osdSize != osdSize) {
      this.instance.system.osdSize = osdSize;
      set_osd_size(osdSize);
      // Settings.saveSettingsToLocalStorage();
    }
  }

  static syncOSDSize(osdSize: number) {
    if (this.instance.system.osdSize != osdSize) {
      this.instance.system.osdSize = osdSize;
    }
  }

  static getTDPLimit() {
    return this.instance.system.tdpLimit;
  }

  static setTDPLimit(tdpLimit: number) {
    if (this.instance.system.tdpLimit != tdpLimit) {
      this.instance.system.tdpLimit = tdpLimit;
      set_tdp_limit(tdpLimit);
      // Settings.saveSettingsToLocalStorage();
    }
  }

  static syncTDPLimit(tdpLimit: number) {
    if (this.instance.system.tdpLimit != tdpLimit) {
      this.instance.system.tdpLimit = tdpLimit;
    }
  }

  static getRefreshRate() {
    return this.instance.system.refreshRate;
  }

  static setRefreshRate(refreshRate: number) {
    if (this.instance.system.refreshRate != refreshRate) {
      this.instance.system.refreshRate = refreshRate;
      set_refresh_rate(refreshRate);
      // Settings.saveSettingsToLocalStorage();
    }
  }

  static syncRefreshRate(refreshRate: number) {
    if (this.instance.system.refreshRate != refreshRate) {
      this.instance.system.refreshRate = refreshRate;
    }
  }

  static getTurboBoost() {
    return this.instance.system.turboBoost;
  }

  static setTurboBoost(turboBoost: boolean) {
    if (this.instance.system.turboBoost != turboBoost) {
      this.instance.system.turboBoost = turboBoost;
      set_turbo_boost(turboBoost);
      // Settings.saveSettingsToLocalStorage();
    }
  }

  static syncTurboBoost(turboBoost: boolean) {
    if (this.instance.system.turboBoost != turboBoost) {
      this.instance.system.turboBoost = turboBoost;
    }
  }

  static getEPP() {
    return this.instance.system.epp;
  }

  static setEPP(epp: number) {
    if (this.instance.system.epp != epp) {
      this.instance.system.epp = epp;
      set_epp(epp);
      // Settings.saveSettingsToLocalStorage();
    }
  }

  static syncEPP(epp: number) {
    if (this.instance.system.epp != epp) {
      this.instance.system.epp = epp;
    }
  }

  static getCPUClockLimit() {
    return this.instance.system.cpuClockLimit;
  }

  static setCPUClockLimit(cpuClockLimit: number) {
    if (cpuClockLimit == 0){
      cpuClockLimit = 2400;
    }

    if (this.instance.system.cpuClockLimit != cpuClockLimit) {
      this.instance.system.cpuClockLimit = cpuClockLimit;
      if (this.instance.system.shouldLimitCPUClock) {
        set_cpu_clock_limit(cpuClockLimit);
      }
      else {
        set_cpu_clock_limit(0);
      }
      // Settings.saveSettingsToLocalStorage();
    }
  }

  static syncCPUClockLimit(cpuClockLimit: number) {
    if (cpuClockLimit == 0){
      cpuClockLimit = 2400;
    }
    
    if (this.instance.system.cpuClockLimit != cpuClockLimit) {
      this.instance.system.cpuClockLimit = cpuClockLimit;
    }
  }

  static getShouldLimitCPUClock() {
    return this.instance.system.shouldLimitCPUClock;
  }

  static setShouldLimitCPUClock(shouldLimit: boolean) {
    if (this.instance.system.shouldLimitCPUClock != shouldLimit) {
      this.instance.system.shouldLimitCPUClock = shouldLimit;
      if (!shouldLimit) {
        set_cpu_clock_limit(0);
      }
      else {
        set_cpu_clock_limit(this.instance.system.cpuClockLimit);
      }
      // Settings.saveSettingsToLocalStorage();
    }
  }

  static syncShouldLimitCPUClock(shouldLimit: boolean) {
    if (this.instance.system.shouldLimitCPUClock != shouldLimit) {
      this.instance.system.shouldLimitCPUClock = shouldLimit;
    }
  }

  static getGPUClockLimit() {
    return this.instance.system.gpuClockLimit;
  }

  static setGPUClockLimit(gpuClockLimit: number) {
    if (gpuClockLimit == 0){
      gpuClockLimit = 800;
    }

    if (this.instance.system.gpuClockLimit != gpuClockLimit) {
      this.instance.system.gpuClockLimit = gpuClockLimit;
      if (this.instance.system.shouldLimitGPUClock) {
        // Call the API to set the GPU clock limit
        set_gpu_clock_limit(gpuClockLimit);
      }
      else {
        // Call the API to disable the GPU clock limit
        // set_gpu_clock_limit(0);
      }
      // Settings.saveSettingsToLocalStorage();
    }
  }

  static syncGPUClockLimit(gpuClockLimit: number) {
    if (gpuClockLimit == 0){
      gpuClockLimit = 800;
    }

    if (this.instance.system.gpuClockLimit != gpuClockLimit) {
      this.instance.system.gpuClockLimit = gpuClockLimit;
    }
  }

  static getShouldLimitGPUClock() {
    return this.instance.system.shouldLimitGPUClock;
  }

  static setShouldLimitGPUClock(shouldLimit: boolean) {
    if (this.instance.system.shouldLimitGPUClock != shouldLimit) {
      this.instance.system.shouldLimitGPUClock = shouldLimit;
      if (shouldLimit) {
        if (this.instance.system.gpuClockLimit > 0)
        {
          set_gpu_clock_limit(this.instance.system.gpuClockLimit);
        }
      }
      else {
        // Call the API to set the GPU clock limit
        // set_gpu_clock_limit(this.instance.system.gpuClockLimit);
      }
      // Settings.saveSettingsToLocalStorage();
    }
  }

  static syncShouldLimitGPUClock(shouldLimit: boolean) {
    if (this.instance.system.shouldLimitGPUClock != shouldLimit) {
      this.instance.system.shouldLimitGPUClock = shouldLimit;
    }
  }

  static getAutoTDP() {
    return this.instance.system.autoTDP;
  }

  static setAutoTDP(enableAutoTDP: boolean) {
    if (this.instance.system.autoTDP != enableAutoTDP) {
      this.instance.system.autoTDP = enableAutoTDP;
      set_auto_tdp(enableAutoTDP);
    }
  }
}
