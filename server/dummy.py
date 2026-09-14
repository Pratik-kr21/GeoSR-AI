import rasterio
import numpy as np
meta = {
    'driver': 'GTiff',
    'dtype': 'uint8',
    'nodata': None,
    'width': 10,
    'height': 10,
    'count': 1,
    'crs': 'EPSG:4326',
    'transform': rasterio.transform.from_origin(0, 0, 1, 1)
}
with rasterio.open('server/data/dummy.tif', 'w', **meta) as dst:
    dst.write(np.zeros((1, 10, 10), dtype='uint8'))
