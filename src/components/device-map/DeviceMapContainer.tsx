import { useState } from 'react';
import { DeviceMarker } from './DeviceMarker';
import { MapLegend } from './MapLegend';
import { RouterPoint } from './RouterPoint';
import { DevicesData } from './types';

interface DeviceMapContainerProps {
  devices: DevicesData;
  zoom: number;
}

export const DeviceMapContainer = ({ devices, zoom }: DeviceMapContainerProps) => {
  const [hoveredDevice, setHoveredDevice] = useState<string | null>(null);

  // Calculate the maximum distance and scale factor
  const maxDistance = Math.max(...Object.values(devices).map(d => d.distance), 0.1);
  const maxRadius = 400;
  const scaleFactor = maxRadius / maxDistance;

  // Calculate circle positions based on max distance
  const circlePositions = [1.0, 0.75, 0.5, 0.25].map(fraction => ({
    size: maxRadius * 2 * fraction,
    label: `${(maxDistance * fraction * 100).toFixed(0)}cm`
  }));

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
  };

  return (
    <div
      className="relative h-[500px] bg-gray-100 rounded-lg overflow-hidden"
      onWheel={handleWheel}
    >
      {/* Map container with zoom transform */}
      <div
        className="absolute top-1/2 left-1/2 w-full h-full"
        style={{
          transform: `translate(-50%, -50%)`
        }}
      >
        {/* Zoomable background with circles */}
        <div
          className="absolute top-1/2 left-1/2 w-full h-full transition-transform duration-200"
          style={{
            transform: `translate(-50%, -50%) scale(${zoom})`
          }}
        >
          <MapLegend circlePositions={circlePositions} zoom={zoom} />
        </div>

        <RouterPoint />

        {/* Device points */}
        {Object.entries(devices).map(([mac, device], index) => {
          const angle = (index / Object.keys(devices).length) * Math.PI * 2;
          const radius = device.distance * scaleFactor * zoom;
          const x = Math.cos(angle) * radius;
          const y = Math.sin(angle) * radius;

          return (
            <DeviceMarker
              key={device.mac_address}
              device={device}
              position={{ x, y }}
              isHovered={hoveredDevice === device.mac_address}
              onHover={setHoveredDevice}
            />
          );
        })}
      </div>
    </div>
  );
};
