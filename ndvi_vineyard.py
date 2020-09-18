import ee
from ee_plugin import Map
import os
from datetime import datetime

home_dir = os.path.join(os.path.expanduser('~'))
wdir = 'Documents/copernicus_hackathon/'
template = os.path.join(home_dir, wdir, 'ndvi_map.qpt')

# Define bounding box
geometry = ee.Geometry.Polygon([[
    [9.21856, 48.75982],
    [9.22144, 48.75943],
    [9.22060, 48.75745],
    [9.21885, 48.75822]
    ]])
farm = ee.Feature(geometry, {'name': 'bounding_box'})
fc = ee.FeatureCollection([farm])
Map.centerObject(fc)
empty = ee.Image().byte();
outline = empty.paint(**{
  'featureCollection': fc,
  'color': 1,
  'width': 1
});
viz_params = {'bands': ['B5', 'B4', 'B3'], 'min' : 0, 'max' : 2000}

def maskCloudAndShadows(image):
    cloudProb = image.select('MSK_CLDPRB')
    snowProb = image.select('MSK_SNWPRB')
    cloud = cloudProb.lt(10)
    snow = snowProb.lt(10)
    scl = image.select('SCL');
    shadow = scl.eq(3) #3 = cloud shadow
    cirrus = scl.eq(10) # 10 = cirrus
    # Cloud and Snow probability less than 10% or cloud shadow classification
    mask = (cloud.And(snow)).And(cirrus.neq(1)).And(shadow.neq(1))
    return image.updateMask(mask);

def addNDVI(image):
    ndvi = image.normalizedDifference(['B5', 'B4']).rename('ndvi')
    return image.addBands([ndvi])

start_date = '2019-09-11'
end_date = '2020-09-10'

collection = ee.ImageCollection('COPERNICUS/S2_SR')\
    .filterDate(start_date, end_date)\
    .map(maskCloudAndShadows)\
    .map(addNDVI)\
    .filter(ee.Filter.intersects('.geo', farm.geometry()))

def get_ndvi(image):
    stats = image.select('ndvi').reduceRegion(**{
        'geometry': farm.geometry(),
        'reducer': ee.Reducer.mean().combine(**{
            'reducer2': ee.Reducer.count(),
            'sharedInputs': True}
            ).setOutputs(['mean', 'pixelcount']),
        'scale': 10
        })
    ndvi = stats.get('ndvi_mean')
    pixelcount = stats.get('ndvi_pixelcount')
    return ee.Feature(None, {
        'ndvi': ndvi,
        'validpixels': pixelcount,
        'id': image.id(),
        'date': ee.Date(image.get('system:time_start')).format('YYYY-MM-dd')
      })


with_ndvi = collection.map(get_ndvi)

# Find how many pixels in the farm extent
max_validpixels = with_ndvi.aggregate_max('validpixels').getInfo()

def select_color(ndvi):
    ndvi_colors = {
        0.3: QColor('#dfc27d'),
        0.5: QColor('#c2e699'),
        1: QColor('#31a354')}

    for max_value, color in ndvi_colors.items():
        if ndvi < max_value:
            return color

def select_season(date_str):
    seasons = {
        'Buds break': [4, 5],
        'Dormancy': [11, 12, 1, 2, 3],
        'Bloom and berries set': [6, 7],
        'Veraison and harvest': [8, 9],
        'Post-Harvest':[10]
    }
    date = datetime.strptime(date_str, '%Y-%m-%d')
    month = date.month
    for season, months in seasons.items():
        if month in months:
            return season

features = with_ndvi.getInfo()['features']
for feature in features:
    ndvi = feature['properties']['ndvi']
    validpixels = feature['properties']['validpixels']
    date = feature['properties']['date']
    id = feature['properties']['id']
    # The following condition ensures we pick images where
    # all pixels in the farm geometry are unmasked
    if ndvi and (validpixels == max_validpixels):
        image = ee.Image(collection.filter(
            ee.Filter.eq('system:index', id)).first())
        Map.addLayer(image, viz_params, 'ndvi_image')
        Map.addLayer(outline, {'palette': ['green', 'yellow', 'red']}, 'farm')
        project = QgsProject.instance()
        layout = QgsLayout(project)
        layout.initializeDefaults()
        
        
#        with open(template) as f:
#            template_content = f.read()
#        doc = QDomDocument()
#        doc.setContent(template_content)
#        # adding to existing items
#        items, ok = layout.loadFromTemplate(doc, QgsReadWriteContext(), False)
#        ndvi_label = layout.itemById('ndvi_label')
#        ndvi_label.setText('{:.2f}'.format(ndvi))
#        ndvi_label.setFontColor(select_color(ndvi))

#        date_label = layout.itemById('date_label')
#        date_label.setText(date)

#        season = select_season(date)
#        season_label = layout.itemById('season_label')
#        season_label.setText(season)

#        exporter = QgsLayoutExporter(layout)
#        output_image = os.path.join(home_dir, wdir, 'ndvi_img', '{}.png'.format(date))
#        exporter.exportToImage(output_image, QgsLayoutExporter.ImageExportSettings())
#        exporter.exportToPdf(output_image, QgsLayoutExporter.PdfExportSettings())
