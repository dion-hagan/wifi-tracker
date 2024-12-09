interface CirclePosition {
  size: number;
  label: string;
}

interface MapLegendProps {
  circlePositions: CirclePosition[];
  zoom: number;
}

export const MapLegend = ({ circlePositions, zoom }: MapLegendProps) => {
  return (
    <>
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
            style={{
              transform: `scale(${1/zoom})`
            }}
          >
            {circle.label}
          </div>
        </div>
      ))}
    </>
  );
};
