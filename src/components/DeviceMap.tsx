import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Signal } from 'lucide-react';
import { DeviceMapContainer } from './device-map/DeviceMapContainer';
import { MapControls } from './device-map/MapControls';
import { DevicesData } from './device-map/types';

const DeviceMap = () => {
  const [devices, setDevices] = useState<DevicesData>({});
  const [error, setError] = useState<string | null>(null);
  const [zoom, setZoom] = useState(1);

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

  const handleZoomChange = (delta: number) => {
    setZoom(prevZoom => Math.min(Math.max(0.5, prevZoom + delta), 2));
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardTitle className="flex items-center gap-2">
            <Signal className="h-6 w-6" />
            Device Map
          </CardTitle>
          <MapControls zoom={zoom} onZoomChange={handleZoomChange} />
        </div>
      </CardHeader>
      <CardContent>
        {error ? (
          <div className="text-red-500">{error}</div>
        ) : (
          <DeviceMapContainer devices={devices} zoom={zoom} />
        )}
      </CardContent>
    </Card>
  );
};

export default DeviceMap;
