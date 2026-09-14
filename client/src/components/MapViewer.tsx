import { useEffect, useState } from "react";
import { MapContainer, TileLayer, LayersControl, useMap, ImageOverlay } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { fetchMapBounds } from "../services/api";

// Utility to handle map resizing dynamically
const MapResizer = () => {
  const map = useMap();
  useEffect(() => {
    map.invalidateSize();
  }, [map]);
  return null;
};

// Utility to clip a specific pane based on sliderX
const ClipPane = ({ sliderX }: { sliderX: number }) => {
  const map = useMap();
  
  useEffect(() => {
    const pane = map.getPane("overlayPane");
    if (pane) {
      // Set clip path to reveal the left side (0% to sliderX%)
      pane.style.clipPath = `polygon(0 0, ${sliderX}% 0, ${sliderX}% 100%, 0 100%)`;
      pane.style.transition = "clip-path 0.1s ease-out";
    }
  }, [map, sliderX]);
  
  return null;
};

// Utility to automatically fly to bounds when they load
const BoundsFitter = ({ bounds }: { bounds: [[number, number], [number, number]] }) => {
  const map = useMap();
  useEffect(() => {
    if (bounds) {
      map.flyToBounds(bounds, { duration: 1.5 });
    }
  }, [map, bounds]);
  return null;
};

export default function MapViewer({ sliderX, isCompleted, objectName }: { sliderX: number, isCompleted: boolean, objectName: string | null }) {
  const center: [number, number] = [30.7333, 76.7794];
  const [bounds, setBounds] = useState<[[number, number], [number, number]] | null>(null);
  
  useEffect(() => {
    if (isCompleted && objectName) {
      fetchMapBounds(1, objectName)
        .then(res => setBounds(res.bounds))
        .catch(err => console.error("Failed to fetch map bounds", err));
    }
  }, [isCompleted, objectName]);

  const thumbnailUrl = isCompleted && objectName 
    ? `http://localhost:8000/api/v1/map/1/outputs/sr_${objectName.split('/').pop()}/thumbnail` 
    : undefined;
  
  return (
    <div className="absolute inset-0 z-0 bg-navy-950">
      <MapContainer 
        center={center} 
        zoom={13} 
        scrollWheelZoom={true}
        className="w-full h-full"
        zoomControl={false}
      >
        <MapResizer />
        {bounds && <BoundsFitter bounds={bounds} />}
        
        <LayersControl position="topright">
          <LayersControl.BaseLayer checked name="Satellite Base (Esri)">
            <TileLayer
              attribution='&copy; Esri'
              url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            />
          </LayersControl.BaseLayer>
          <LayersControl.BaseLayer name="OpenStreetMap">
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
          </LayersControl.BaseLayer>
        </LayersControl>

        {isCompleted && thumbnailUrl && bounds && (
          <>
            <ImageOverlay url={thumbnailUrl} bounds={bounds} zIndex={400} />
            <ClipPane sliderX={sliderX} />
          </>
        )}
      </MapContainer>
    </div>
  );
}
