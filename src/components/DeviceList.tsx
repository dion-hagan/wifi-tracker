import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Laptop, Smartphone, Tablet, HardDrive, Signal, Tv, Speaker, Router, GamepadIcon } from 'lucide-react';

interface Device {
  distance: number;
  rssi: number;
  last_seen: string;
  ip_address: string;
  mac_address: string;
  manufacturer: string | null;
  device_type: string;
  hostname: string | null;
}

interface DevicesData {
  [key: string]: Device;
}

interface SortConfig {
  key: keyof Device | 'name';
  direction: 'ascending' | 'descending';
}

const DeviceList = () => {
  const [devices, setDevices] = useState<DevicesData>({});
  const [error, setError] = useState<string | null>(null);
  const [sortConfig, setSortConfig] = useState<SortConfig>({ 
    key: 'distance', 
    direction: 'ascending' 
  });

  useEffect(() => {
    const fetchDevices = async () => {
      try {
        const response = await fetch('http://localhost:5001/devices');
        const data = await response.json();
        if (data.devices) {
          setDevices(data.devices);
        }
      } catch (err) {
        setError('Failed to fetch device data');
        console.error('Error fetching devices:', err);
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
      return <Smartphone className="h-5 w-5" />;
    } else if (type.includes('ipad')) {
      return <Tablet className="h-5 w-5" />;
    } else if (type.includes('macbook') || type.includes('laptop')) {
      return <Laptop className="h-5 w-5" />;
    } else if (type.includes('tv') || name.includes('tv')) {
      return <Tv className="h-5 w-5" />;
    } else if (type.includes('gaming') || device.manufacturer?.toLowerCase().includes('playstation')) {
      return <GamepadIcon className="h-5 w-5" />;
    } else if (type.includes('speaker')) {
      return <Speaker className="h-5 w-5" />;
    } else if (type.includes('network') || device.manufacturer?.toLowerCase().includes('ubee')) {
      return <Router className="h-5 w-5" />;
    }
    return <HardDrive className="h-5 w-5" />;
  };

  const getSignalStrength = (rssi: number) => {
    if (rssi >= -50) return 'Excellent';
    if (rssi >= -60) return 'Good';
    if (rssi >= -70) return 'Fair';
    return 'Poor';
  };

  const getSignalColor = (rssi: number) => {
    if (rssi >= -50) return 'text-green-500';
    if (rssi >= -60) return 'text-blue-500';
    if (rssi >= -70) return 'text-yellow-500';
    return 'text-red-500';
  };

  const formatDistance = (distance: number) => {
    if (distance < 1) {
      return `${(distance * 100).toFixed(0)}cm`;
    }
    return `${distance.toFixed(1)}m`;
  };

  const formatLastSeen = (lastSeen: string) => {
    const date = new Date(lastSeen);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    if (diff < 1000) return 'just now';
    if (diff < 60000) return `${Math.floor(diff / 1000)}s ago`;
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    return `${Math.floor(diff / 3600000)}h ago`;
  };

  const sortedDevices = Object.entries(devices).sort(([nameA, deviceA], [nameB, deviceB]) => {
    if (sortConfig.key === 'name') {
      return sortConfig.direction === 'ascending'
        ? nameA.localeCompare(nameB)
        : nameB.localeCompare(nameA);
    }
    const valueA = deviceA[sortConfig.key];
    const valueB = deviceB[sortConfig.key];
    if (typeof valueA === 'number' && typeof valueB === 'number') {
      return sortConfig.direction === 'ascending'
        ? valueA - valueB
        : valueB - valueA;
    }
    return sortConfig.direction === 'ascending'
      ? String(valueA).localeCompare(String(valueB))
      : String(valueB).localeCompare(String(valueA));
  });

  const handleSort = (key: SortConfig['key']) => {
    setSortConfig(current => ({
      key,
      direction: current.key === key && current.direction === 'ascending' 
        ? 'descending' 
        : 'ascending'
    }));
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Signal className="h-6 w-6" />
          Connected Devices ({Object.keys(devices).length})
        </CardTitle>
      </CardHeader>
      <CardContent>
        {error ? (
          <div className="text-red-500 p-4">{error}</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('name')}
                  >
                    Device
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('distance')}
                  >
                    Distance
                  </th>
                  <th 
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('rssi')}
                  >
                    Signal
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Last Seen
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Details
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {sortedDevices.map(([name, device]) => (
                  <tr key={device.mac_address} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="flex-shrink-0">
                          {getDeviceIcon(device)}
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">
                            {name}
                            {device.hostname && device.hostname !== name && (
                              <span className="text-gray-500 ml-1">({device.hostname})</span>
                            )}
                          </div>
                          <div className="text-sm text-gray-500">
                            {device.manufacturer || 'Unknown manufacturer'}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{formatDistance(device.distance)}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className={`text-sm ${getSignalColor(device.rssi)}`}>
                        {getSignalStrength(device.rssi)} ({device.rssi} dBm)
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatLastSeen(device.last_seen)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div>Type: {device.device_type}</div>
                      <div>IP: {device.ip_address}</div>
                      <div>MAC: {device.mac_address}</div>
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
