/* CRS proiettati usati dai GeoJSON del portale storico.
 *
 * ckanext-geoview (geojson_view) passa il `crs` del GeoJSON a proj4leaflet ma
 * registra solo EPSG:4326/CRS84: con un CRS projected la costruzione del layer
 * fallisce e la mappa resta vuota. Le definizioni (epsg.io) coprono i CRS
 * presenti nel catalogo e i piu' comuni UTM italiani.
 */
(function () {
  'use strict';

  if (typeof proj4 === 'undefined') {
    return;
  }

  var definitions = {
    // Monte Mario / Italy zone 1 e 2 (Roma40)
    'EPSG:3003':
      '+proj=tmerc +lat_0=0 +lon_0=9 +k=0.9996 +x_0=1500000 +y_0=0 ' +
      '+ellps=intl +towgs84=-104.1,-49.1,-9.9,0.971,-2.917,0.714,-11.68 ' +
      '+units=m +no_defs +type=crs',
    'EPSG:3004':
      '+proj=tmerc +lat_0=0 +lon_0=15 +k=0.9996 +x_0=2520000 +y_0=0 ' +
      '+ellps=intl +towgs84=-104.1,-49.1,-9.9,0.971,-2.917,0.714,-11.68 ' +
      '+units=m +no_defs +type=crs',
    // ETRS89 / UTM 32N-33N
    'EPSG:25832':
      '+proj=utm +zone=32 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs +type=crs',
    'EPSG:25833':
      '+proj=utm +zone=33 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs +type=crs',
    // WGS 84 / UTM 32N-33N
    'EPSG:32632': '+proj=utm +zone=32 +datum=WGS84 +units=m +no_defs +type=crs',
    'EPSG:32633': '+proj=utm +zone=33 +datum=WGS84 +units=m +no_defs +type=crs',
    // RDN2008 / UTM 32N e geographiche ETRS89/RDN2008
    'EPSG:7791':
      '+proj=utm +zone=32 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs +type=crs',
    'EPSG:4258': '+proj=longlat +ellps=GRS80 +no_defs +type=crs',
    'EPSG:6706': '+proj=longlat +ellps=GRS80 +no_defs +type=crs',
  };

  Object.keys(definitions).forEach(function (code) {
    if (!proj4.defs[code]) {
      proj4.defs(code, definitions[code]);
    }
  });
})();
