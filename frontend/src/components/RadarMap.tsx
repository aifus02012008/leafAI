import 'leaflet/dist/leaflet.css';
import { Circle, CircleMarker, MapContainer, TileLayer, Tooltip, useMap } from 'react-leaflet';
import { useEffect } from 'react';
import type { GeoPoint, RadarGridCell } from '../types';

interface RadarMapProps {
  center: GeoPoint;
  radiusKm: number;
  cells: RadarGridCell[];
}

function Recenter({ center, radiusKm }: { center: GeoPoint; radiusKm: number }) {
  const map = useMap();
  useEffect(() => {
    // Zoom so the whole radius circle is visible.
    const zoom = radiusKm <= 2 ? 14 : radiusKm <= 5 ? 12 : radiusKm <= 10 ? 11 : 10;
    map.setView([center.lat, center.lng], zoom);
  }, [map, center.lat, center.lng, radiusKm]);
  return null;
}

function cellColor(cases: number): string {
  if (cases >= 8) return '#dc2626';
  if (cases >= 4) return '#f59e0b';
  return '#facc15';
}

/** Case-density map: anonymised ~2 km cells (only cells reported by >= 2 growers are shown). */
export function RadarMap({ center, radiusKm, cells }: RadarMapProps) {
  return (
    <MapContainer
      center={[center.lat, center.lng]}
      zoom={12}
      scrollWheelZoom={false}
      className="h-[320px] sm:h-[380px] w-full rounded-2xl z-0"
      attributionControl
    >
      <Recenter center={center} radiusKm={radiusKm} />
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <Circle
        center={[center.lat, center.lng]}
        radius={radiusKm * 1000}
        pathOptions={{ color: '#15803D', weight: 2, fillOpacity: 0.05 }}
      />
      <CircleMarker
        center={[center.lat, center.lng]}
        radius={7}
        pathOptions={{ color: '#ffffff', weight: 2, fillColor: '#15803D', fillOpacity: 1 }}
      >
        <Tooltip>Vị trí vườn của bạn</Tooltip>
      </CircleMarker>
      {cells.map((c) => (
        <CircleMarker
          key={`${c.lat},${c.lng}`}
          center={[c.lat, c.lng]}
          radius={Math.min(10 + c.cases * 2, 28)}
          pathOptions={{ color: cellColor(c.cases), weight: 1, fillColor: cellColor(c.cases), fillOpacity: 0.55 }}
        >
          <Tooltip>
            {c.cases} ca · {c.top_disease}
          </Tooltip>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}
