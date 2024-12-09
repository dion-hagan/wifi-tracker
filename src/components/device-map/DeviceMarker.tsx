import { Laptop, Smartphone, Tablet, HardDrive, Tv, Speaker, Router, GamepadIcon } from 'lucide-react';
import { Device } from "./types";

interface DeviceMarkerProps {
  device: Device;
  position: { x: number; y: number };
  isHovered: boolean;
  onHover: (mac: string | null) => void;
}

export const getDeviceIcon = (device: Device) => {
  const type = device.device_type.toLowerCase();
  const name = device.hostname?.toLowerCase() || '';

  if (type.includes('iphone') || type.includes('android phone')) {
    return <Smartphone className="h-4 w-4" />;
  } else if (type.includes('ipad')) {
    return <Tablet className="h-4 w-4" />;
  } else if (type.includes('macbook') || type.includes('laptop')) {
    return <Laptop className="h-4 w-4" />;
  } else if (type.includes('tv') || name.includes('tv')) {
    return <Tv className="h-4 w-4" />;
  } else if (type.includes('gaming') || device.manufacturer?.toLowerCase().includes('playstation')) {
    return <GamepadIcon className="h-4 w-4" />;
  } else if (type.includes('speaker')) {
    return <Speaker className="h-4 w-4" />;
  } else if (type.includes('network') || device.manufacturer?.toLowerCase().includes('ubee')) {
    return <Router className="h-4 w-4" />;
  }
  return <HardDrive className="h-4 w-4" />;
};

const getSignalColor = (rssi: number) => {
  if (rssi >= -50) return 'bg-green-500';
  if (rssi >= -60) return 'bg-blue-500';
  if (rssi >= -70) return 'bg-yellow-500';
  return 'bg-red-500';
};

export const DeviceMarker = ({ device, position, isHovered, onHover }: DeviceMarkerProps) => {
  return (
    <div
      className="absolute transform -translate-x-1/2 -translate-y-1/2 group transition-all duration-200"
      style={{
        left: `calc(50% + ${position.x}px)`,
        top: `calc(50% + ${position.y}px)`,
        zIndex: isHovered ? 50 : 10,
      }}
      onMouseEnter={() => onHover(device.mac_address)}
      onMouseLeave={() => onHover(null)}
    >
      <div
        className={`w-8 h-8 ${getSignalColor(device.rssi)} rounded-full flex items-center justify-center text-white transition-transform duration-200`}
        style={{
          transform: isHovered ? 'scale(1.2)' : 'scale(1)',
        }}
      >
        {getDeviceIcon(device)}
      </div>
      <div className="mt-1 text-xs text-center font-medium bg-white bg-opacity-75 px-1 rounded">
        {device.hostname || device.device_type}
      </div>
      <div className="mt-0.5 text-xs text-center text-gray-500 bg-white bg-opacity-75 px-1 rounded">
        {(device.distance * 100).toFixed(0)}cm
      </div>

      <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-black bg-opacity-75 text-white text-xs rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity z-10">
        <div>{device.device_type}</div>
        {device.manufacturer && <div>{device.manufacturer}</div>}
        <div>RSSI: {device.rssi} dBm</div>
      </div>
    </div>
  );
};
