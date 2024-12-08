import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar
} from 'recharts';

interface Device {
  distance: number;
}

interface HistoricalDataPoint {
  timestamp: string;
  deviceCount: number;
  averageDistance: number;
}

const Analytics = () => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [historicalData, setHistoricalData] = useState<HistoricalDataPoint[]>([]);

  useEffect(() => {
    const fetchDevices = async () => {
      try {
        const response = await fetch('http://localhost:5001/devices');
        const data = await response.json();
        setDevices(data.devices || []);
        
        // Add historical data point
        const timestamp = new Date().toLocaleTimeString();
        setHistoricalData(prev => {
          const newData = [...prev, {
            timestamp,
            deviceCount: data.devices.length,
            averageDistance: data.devices.reduce((acc: number, dev: Device) => acc + dev.distance, 0) / data.devices.length || 0
          }];
          
          // Keep last 20 data points
          if (newData.length > 20) {
            return newData.slice(-20);
          }
          return newData;
        });
      } catch (err) {
        console.error('Failed to fetch device data:', err);
      }
    };

    fetchDevices();
    const interval = setInterval(fetchDevices, 2000);
    return () => clearInterval(interval);
  }, []);

  // Calculate statistics
  const stats = {
    totalDevices: devices.length,
    averageDistance: devices.length 
      ? devices.reduce((acc: number, dev: Device) => acc + dev.distance, 0) / devices.length 
      : 0,
    closestDevice: devices.length 
      ? Math.min(...devices.map(dev => dev.distance)) 
      : 0,
    furthestDevice: devices.length 
      ? Math.max(...devices.map(dev => dev.distance)) 
      : 0
  };

  // Prepare distance distribution data
  const distanceRanges = [
    { range: '0-2m', count: 0 },
    { range: '2-5m', count: 0 },
    { range: '5-10m', count: 0 },
    { range: '10m+', count: 0 }
  ];

  devices.forEach(device => {
    if (device.distance <= 2) distanceRanges[0].count++;
    else if (device.distance <= 5) distanceRanges[1].count++;
    else if (device.distance <= 10) distanceRanges[2].count++;
    else distanceRanges[3].count++;
  });

  return (
    <div className="space-y-6">
      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm font-medium text-gray-500">Total Devices</div>
            <div className="mt-1 text-3xl font-semibold">{stats.totalDevices}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm font-medium text-gray-500">Average Distance</div>
            <div className="mt-1 text-3xl font-semibold">
              {stats.averageDistance.toFixed(2)}m
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm font-medium text-gray-500">Closest Device</div>
            <div className="mt-1 text-3xl font-semibold">
              {stats.closestDevice.toFixed(2)}m
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm font-medium text-gray-500">Furthest Device</div>
            <div className="mt-1 text-3xl font-semibold">
              {stats.furthestDevice.toFixed(2)}m
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Device Count Over Time */}
        <Card>
          <CardHeader>
            <CardTitle>Device Count Over Time</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={historicalData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="deviceCount" 
                    stroke="#3b82f6" 
                    name="Devices"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Distance Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Distance Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={distanceRanges}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="range" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar 
                    dataKey="count" 
                    fill="#3b82f6" 
                    name="Devices"
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Analytics;
