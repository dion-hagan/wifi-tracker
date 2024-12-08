import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';

interface Device {
  mac_address: string;
  distance: number;
}

interface SortConfig {
  key: keyof Device;
  direction: 'ascending' | 'descending';
}

const DeviceList = () => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [sortConfig, setSortConfig] = useState<SortConfig>({ 
    key: 'distance', 
    direction: 'ascending' 
  });

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

  const sortDevices = (key: keyof Device) => {
    let direction: 'ascending' | 'descending' = 'ascending';
    if (sortConfig.key === key && sortConfig.direction === 'ascending') {
      direction = 'descending';
    }
    setSortConfig({ key, direction });

    const sortedDevices = [...devices].sort((a, b) => {
      if (key === 'distance') {
        return direction === 'ascending' 
          ? a.distance - b.distance 
          : b.distance - a.distance;
      }
      return direction === 'ascending'
        ? a[key].toString().localeCompare(b[key].toString())
        : b[key].toString().localeCompare(a[key].toString());
    });
    setDevices(sortedDevices);
  };

  const getDistanceColor = (distance: number): string => {
    if (distance <= 2) return 'text-green-500';
    if (distance <= 5) return 'text-yellow-500';
    if (distance <= 10) return 'text-orange-500';
    return 'text-red-500';
  };

  const getDistanceLabel = (distance: number): string => {
    if (distance <= 2) return 'Near';
    if (distance <= 5) return 'Medium';
    if (distance <= 10) return 'Far';
    return 'Very Far';
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Connected Devices</CardTitle>
      </CardHeader>
      <CardContent>
        {error ? (
          <div className="text-red-500">{error}</div>
        ) : (
          <div className="space-y-4">
            <table className="min-w-full">
              <thead>
                <tr>
                  <th 
                    className="cursor-pointer"
                    onClick={() => sortDevices('mac_address')}
                  >
                    MAC Address
                  </th>
                  <th 
                    className="cursor-pointer"
                    onClick={() => sortDevices('distance')}
                  >
                    Distance
                  </th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {devices.map((device) => (
                  <tr key={device.mac_address}>
                    <td>{device.mac_address}</td>
                    <td>{device.distance.toFixed(2)}m</td>
                    <td>
                      <span className={getDistanceColor(device.distance)}>
                        {getDistanceLabel(device.distance)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default DeviceList;
