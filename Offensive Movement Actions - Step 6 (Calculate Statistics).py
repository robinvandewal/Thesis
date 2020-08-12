import math
from qgis.core import *
import processing

#INPUT

HalfStr = "XxxXxx1"

#END INPUT

dominant_regions = QgsProject.instance().mapLayersByName(HalfStr + " - dominant regions")[0]
real_xG = QgsProject.instance().mapLayersByName(HalfStr + " - real xg points")[0]

#OUTPUT
region_layer = QgsVectorLayer("polygon", HalfStr + " - statistics", "memory")
region_data = region_layer.dataProvider()
region_data.addAttributes([QgsField("pk", QVariant.Int), QgsField("ID", QVariant.Int), QgsField("Team", QVariant.String), QgsField("T Stamp", QVariant.Int), QgsField("Sum xG", QVariant.Double), QgsField("Average xG", QVariant.Double), QgsField("Var xG", QVariant.Double), QgsField("Dev xG", QVariant.Double), QgsField("Min xG", QVariant.Double), QgsField("Max xG", QVariant.Double), QgsField("Number xG", QVariant.Int)])
region_layer.updateFields()

#needed for geometry calculations
d = QgsDistanceArea()
d.setEllipsoid('WGS84 / Plate Carree')

T_List = []
T_Possession = {}

for dominant_region_feature in dominant_regions.getFeatures():
    dominant_attr = dominant_region_feature.attributes()
    if dominant_attr[3] not in T_List:
        T_List.append(dominant_attr[3])
        T_Possession[dominant_attr[3]] = dominant_attr[2] 

pk_list = []

for T0 in T_List:
    real_xG.selectByExpression('T_Stamp = ' + str(T0))
    dominant_regions.selectByExpression('"T Stamp" = ' + str(T0) + " and Team = " + "'" + str(T_Possession[T0]) + "'")
    algresult1 = processing.run("saga:pointstatisticsforpolygons", {'POINTS':QgsProcessingFeatureSourceDefinition(real_xG.id(), True),'POLYGONS':QgsProcessingFeatureSourceDefinition(dominant_regions.id(), True),'FIELDS':'xG','FIELD_NAME':0,'SUM             ':True,'AVG             ':True,'VAR             ':True,'DEV             ':True,'MIN             ':True,'MAX             ':True,'NUM             ':True,'STATISTICS':'D:/GIMA/Thesis/QGIS/Matches/-' + HalfStr + '-xG statistics.shp'})
    layer0 = QgsVectorLayer('D:/GIMA/Thesis/QGIS/Matches/-' + HalfStr + '-xG statistics.shp')
    for feature1 in layer0.getFeatures():
        attr0 = feature1.attributes()
        pk = attr0[0]
        if attr0[10] > 0 and pk not in pk_list:
            pk_list.append(pk)
            region_data.addFeature(feature1)
            region_layer.updateFields()
            region_layer.updateExtents()

QgsProject.instance().addMapLayer(region_layer)


