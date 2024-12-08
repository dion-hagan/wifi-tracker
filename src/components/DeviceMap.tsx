import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Laptop, Smartphone, Tablet, HardDrive, Signal, Tv, Speaker, Router, GamepadIcon } from 'lucide-react';

interface Device {
  mac_address: string;
  distance: number;
  device_type: string;
  manufacturer: string | null;
  hostname: string | null;
  rssi: number;
}

interface DevicesData {
  [key: string]: Device;
}

const DeviceMap = () => {
  const [devices, setDevices] = useState<DevicesData>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDevices = async () => {
      try {
        const response = await fetch('http://localhost:5001/devices');
        const data = await response.json();
        setDevices(data.devices || {});
      } catch (err) {
        setError('Failed to fetch device data');
      }
    };

    fetchDevices();
    const interval = setInterval(fetchDevices, 2000);
    return () => clearInterval(interval);
  }, []);

  const getDeviceIcon = (device: Device) => {
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

  // Calculate the maximum distance and scale factor
  const maxDistance = Math.max(...Object.values(devices).map(d => d.distance), 0.1);
  const maxRadius = 400; // Increased from 220 to 400 for better visibility
  const scaleFactor = maxRadius / maxDistance;

  // Calculate circle positions based on max distance
  const circlePositions = [1.0, 0.75, 0.5, 0.25].map(fraction => ({
    size: maxRadius * 2 * fraction,
    label: `${(maxDistance * fraction * 100).toFixed(0)}cm`
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Signal className="h-6 w-6" />
          Device Map
        </CardTitle>
      </CardHeader>
      <CardContent>
        {error ? (
          <div className="text-red-500">{error}</div>
        ) : (
          <div className="relative h-[500px] bg-gray-100 rounded-lg overflow-hidden">
            {/* Signal strength circles with labels */}
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
              {circlePositions.map((circle, index) => (
                <div key={index} className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                  <div 
                    className="border-2 border-gray-200 rounded-full opacity-20"
                    style={{
                      width: `${circle.size}px`,
                      height: `${circle.size}px`
                    }}
                  />
                  <div 
                    className="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-4 text-xs text-gray-500"
                  >
                    {circle.label}
                  </div>
                </div>
              ))}
            </div>

            {/* Center point representing the WiFi router */}
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
              <div className="w-6 h-6 bg-blue-500 rounded-full animate-pulse" />
              <div className="mt-2 text-xs font-medium text-center">Router</div>
            </div>

            {/* Device points */}
            {Object.entries(devices).map(([name, device], index) => {
              const angle = (index / Object.keys(devices).length) * Math.PI * 2; // Distribute devices evenly
              const radius = device.distance * scaleFactor;
              const x = Math.cos(angle) * radius;
              const y = Math.sin(angle) * radius;

              return (
                <div
                  key={device.mac_address}
                  className="absolute transform -translate-x-1/2 -translate-y-1/2 group"
                  style={{
                    left: `calc(50% + ${x}px)`,
                    top: `calc(50% + ${y}px)`,
                  }}
                >
                  <div className={`w-8 h-8 ${getSignalColor(device.rssi)} rounded-full flex items-center justify-center text-white`}>
                    {getDeviceIcon(device)}
                  </div>
                  <div className="mt-1 text-xs text-center font-medium bg-white bg-opacity-75 px-1 rounded">
                    {name}
                  </div>
                  <div className="mt-0.5 text-xs text-center text-gray-500 bg-white bg-opacity-75 px-1 rounded">
                    {(device.distance * 100).toFixed(0)}cm
                  </div>
                  
                  {/* Tooltip */}
                  <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-black bg-opacity-75 text-white text-xs rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity z-10">
                    <div>{device.device_type}</div>
                    {device.manufacturer && <div>{device.manufacturer}</div>}
                    <div>RSSI: {device.rssi} dBm</div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default DeviceMap;
