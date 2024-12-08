import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';

interface Settings {
  scan_interval: number;
  distance_threshold: number;
}

const SettingsView = () => {
  const [settings, setSettings] = useState<Settings>({
    scan_interval: 2,
    distance_threshold: 10
  });
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const response = await fetch('http://localhost:5000/settings');
        const data = await response.json();
        setSettings(data);
      } catch (err) {
        setError('Failed to fetch settings');
      }
    };

    fetchSettings();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await fetch('http://localhost:5000/settings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings),
      });

      if (response.ok) {
        setSuccess('Settings updated successfully');
        setError(null);
        // Clear success message after 3 seconds
        setTimeout(() => setSuccess(null), 3000);
      } else {
        throw new Error('Failed to update settings');
      }
    } catch (err) {
      setError('Failed to update settings');
      setSuccess(null);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setSettings(prev => ({
      ...prev,
      [name]: parseFloat(value)
    }));
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Settings</CardTitle>
      </CardHeader>
      <CardContent>
        {error && <div className="mb-4 text-red-500">{error}</div>}
        {success && <div className="mb-4 text-green-500">{success}</div>}
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Scan Interval (seconds)
            </label>
            <input
              type="number"
              name="scan_interval"
              value={settings.scan_interval}
              onChange={handleChange}
              min="1"
              max="60"
              step="1"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            />
            <p className="mt-1 text-sm text-gray-500">
              How often to scan for devices (1-60 seconds)
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Distance Threshold (meters)
            </label>
            <input
              type="number"
              name="distance_threshold"
              value={settings.distance_threshold}
              onChange={handleChange}
              min="1"
              max="50"
              step="1"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            />
            <p className="mt-1 text-sm text-gray-500">
              Maximum distance to track devices (1-50 meters)
            </p>
          </div>

          <div>
            <button
              type="submit"
              className="inline-flex justify-center rounded-md border border-transparent bg-blue-600 py-2 px-4 text-sm font-medium text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              Save Settings
            </button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};

export default SettingsView;
