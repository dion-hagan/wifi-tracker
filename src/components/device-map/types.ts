export interface Device {
  mac_address: string;
  distance: number;
  device_type: string;
  manufacturer: string | null;
  hostname: string | null;
  rssi: number;
}

export interface DevicesData {
  [key: string]: Device;
}
