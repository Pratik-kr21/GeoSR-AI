import { useEffect, useState } from "react";
import L from "leaflet";
import { MapContainer, TileLayer, LayersControl, useMap, ImageOverlay, Pane } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet-draw/dist/leaflet.draw.css";
import "leaflet-draw";
import { fetchMapBounds, fetchInputMapBounds } from "../services/api";

// Fix Leaflet draw icons if needed (optional, depends on setup)
(window as any).type = '';

// Custom Native Leaflet Draw Component
const DrawControl = ({ onBboxSelect }: { onBboxSelect: (bbox: [number, number, number, number]) => void }) => {
  const map = useMap();
  
  useEffect(() => {
    const drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);
    
    const drawControl = new (L.Control as any).Draw({
      position: 'topleft',
      draw: {
        rectangle: true,
        polygon: false,
        circle: false,
        circlemarker: false,
        marker: false,
        polyline: false,
      },
      edit: {
        featureGroup: drawnItems,
        edit: false,
        remove: true,
      }
    });
    
    map.addControl(drawControl);
    
    map.on((L.Draw as any).Event.CREATED, (e: any) => {
      const layer = e.layer;
      drawnItems.clearLayers();
      drawnItems.addLayer(layer);
      
      if (e.layerType === 'rectangle') {
        const bounds = layer.getBounds();
        onBboxSelect([bounds.getWest(), bounds.getSouth(), bounds.getEast(), bounds.getNorth()]);
      }
    });
    
    return () => {
      map.removeControl(drawControl);
      map.removeLayer(drawnItems);
      map.off((L.Draw as any).Event.CREATED);
    };
  }, [map, onBboxSelect]);
  
  return null;
};

// Utility to handle map resizing dynamically
const MapResizer = () => {
  const map = useMap();
  useEffect(() => {
    map.invalidateSize();
  }, [map]);
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

export default function MapViewer({ activeLayers, isCompleted, objectName, onBboxSelect }: { activeLayers: Set<string>, isCompleted: boolean, objectName: string | null, onBboxSelect?: (bbox: [number, number, number, number]) => void }) {
  const center: [number, number] = [30.7333, 76.7794];
  const [inputBounds, setInputBounds] = useState<[[number, number], [number, number]] | null>(null);
  const [outputBounds, setOutputBounds] = useState<[[number, number], [number, number]] | null>(null);
  
  // Fetch input bounds as soon as an object is uploaded
  useEffect(() => {
    if (objectName) {
      fetchInputMapBounds(1, objectName)
        .then(res => setInputBounds(res.bounds))
        .catch(err => console.error("Failed to fetch input bounds", err));
    } else {
      setInputBounds(null);
    }
  }, [objectName]);

  // Fetch output bounds when SR completes
  useEffect(() => {
    if (isCompleted && objectName) {
      fetchMapBounds(1, objectName)
        .then(res => setOutputBounds(res.bounds))
        .catch(err => console.error("Failed to fetch output bounds", err));
    } else {
      setOutputBounds(null);
    }
  }, [isCompleted, objectName]);

  const fileId = objectName ? objectName.split('/').pop() : null;
  const inputThumbnailUrl = fileId ? `http://localhost:8000/api/v1/map/1/inputs/${fileId}/thumbnail` : undefined;
  const outputThumbnailUrl = fileId ? `http://localhost:8000/api/v1/map/1/outputs/sr_${fileId}/thumbnail` : undefined;
  
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
        {inputBounds && <BoundsFitter bounds={inputBounds} />}
        
        {onBboxSelect && <DrawControl onBboxSelect={onBboxSelect} />}

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

        {/* Original Input Layer - rendered behind with blur to simulate lower resolution */}
        {activeLayers.has("original") && inputThumbnailUrl && inputBounds && (
          <Pane name="originalPane" style={{ zIndex: 300 }}>
            <ImageOverlay url={inputThumbnailUrl} bounds={inputBounds} className="original-overlay-blur" />
          </Pane>
        )}

        {/* Enhanced Output Layer - rendered in a custom pane, sharp */}
        {activeLayers.has("enhanced") && isCompleted && outputThumbnailUrl && outputBounds && (
          <Pane name="enhancedPane" style={{ zIndex: 400 }}>
            <ImageOverlay url={outputThumbnailUrl} bounds={outputBounds} />
          </Pane>
        )}
      </MapContainer>
    </div>
  );
}
