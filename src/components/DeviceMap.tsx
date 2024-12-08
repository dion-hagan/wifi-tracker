import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';

interface Device {
  mac_address: string;
  distance: number;
}

const DeviceMap = () => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDevices = async () => {
      try {
        const response = await fetch('http://localhost:5000/devices');
        const data = await response.json();
        setDevices(data.devices || []);
      } catch (err) {
        setError('Failed to fetch device data');
      }
    };

    fetchDevices();
    const interval = setInterval(fetchDevices, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Device Map</CardTitle>
      </CardHeader>
      <CardContent>
        {error ? (
          <div className="text-red-500">{error}</div>
        ) : (
          <div className="relative h-[500px] bg-gray-100 rounded-lg">
            {/* Center point representing the WiFi router */}
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
              <div className="w-6 h-6 bg-blue-500 rounded-full animate-pulse" />
              <div className="mt-2 text-sm font-medium text-center">Router</div>
            </div>

            {/* Device points */}
            {devices.map((device) => {
              // Convert distance to relative position (max 200px from center)
              const angle = Math.random() * Math.PI * 2; // Random angle
              const maxRadius = 200;
              const radius = (device.distance / 10) * maxRadius; // Scale distance to pixels
              const x = Math.cos(angle) * radius;
              const y = Math.sin(angle) * radius;

              return (
                <div
                  key={device.mac_address}
                  className="absolute transform -translate-x-1/2 -translate-y-1/2"
                  style={{
                    left: `calc(50% + ${x}px)`,
                    top: `calc(50% + ${y}px)`,
                  }}
                >
                  <div className="w-4 h-4 bg-green-500 rounded-full" />
                  <div className="mt-1 text-xs text-center">
                    {device.distance.toFixed(1)}m
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
