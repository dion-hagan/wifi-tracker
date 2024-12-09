import { ZoomIn, ZoomOut } from 'lucide-react';

interface MapControlsProps {
  zoom: number;
  onZoomChange: (delta: number) => void;
}

export const MapControls = ({ zoom, onZoomChange }: MapControlsProps) => {
  return (
    <div className="flex items-center gap-2">
      <button
        onClick={() => onZoomChange(-0.1)}
        className="p-1 rounded hover:bg-gray-100"
        title="Zoom Out"
      >
        <ZoomOut className="h-5 w-5" />
      </button>
      <span className="text-sm">{(zoom * 100).toFixed(0)}%</span>
      <button
        onClick={() => onZoomChange(0.1)}
        className="p-1 rounded hover:bg-gray-100"
        title="Zoom In"
      >
        <ZoomIn className="h-5 w-5" />
      </button>
    </div>
  );
};
