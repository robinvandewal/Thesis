import math
from qgis.core import *
import processing

#INPUT

HalfStr = "XxxXxx1"

T_attackers = {}

#END INPUT

T_List = []
T_possession = {}

Players = QgsProject.instance().mapLayersByName(HalfStr[:6] + " Players")[0]

#needed for geometry calculations    
d = QgsDistanceArea()
d.setEllipsoid('WGS84 / Plate Carree')

#Playerlist
PlayerList = {"ball": "None"}
PlayerList2 = []
TeamList = []

for object in Players.getFeatures():
    attr = object.attributes()
    PlayerList[int(attr[0])] = attr[5]
    PlayerList2.append(int(attr[0]))
    if attr[5] not in TeamList:
        TeamList.append(attr[5])

for T_att in T_attackers:
    if len(T_attackers[T_att]) > 0:
        T_List.append(T_att)
        T_possession[T_att] = PlayerList[T_attackers[T_att][0]]

possible_regions = QgsProject.instance().mapLayersByName(HalfStr + " - possible regions")[0]
line_layer = QgsProject.instance().mapLayersByName(HalfStr + " - intersection lines")[0]

centroid_layer = QgsProject.instance().mapLayersByName(HalfStr + " - centroids")[0]
centroid_dataprovider = centroid_layer.dataProvider()

centroid_TList = {}

#time contours setup
top_speed = 7.8 #m/s
acceleration = 2 #m/s/s this is not real
labda = 1.3
contours_amount = 8
contour_time = 0.25

contours = []
x = 1
while x < contours_amount:
    contours.append(x)
    x += 1

contours.append(12)
contours.append(16)
contours.append(20)
contours.append(39)
contours.append(40)

fid_centroid = 1
for fid_feature_centroid in centroid_layer.getFeatures():
    fid_centroid += 1
    if fid_feature_centroid.attributes()[2] in T_List:
        T_List.remove(fid_feature_centroid.attributes()[2])

for feature1 in line_layer.getFeatures():
    T_from = feature1.attributes()[3]
    if T_from in T_List:
        if T_from not in centroid_TList:
            centroid_TList[T_from] = {}
        centroid_from = contours[feature1.attributes()[4]]
        id1 = feature1.attributes()[1]
        if id1 in centroid_TList[T_from]:
            centroid_TList[T_from][id1] = min(centroid_from, centroid_TList[T_from][id1])
        else:
            centroid_TList[T_from][id1] = centroid_from

#PROCESSING CENTROIDS
possible_regions.removeSelection()
for T_Stamp in centroid_TList:
    for player_centroid in centroid_TList[T_Stamp]:
        possible_regions.selectByExpression("T = " + str(centroid_TList[T_Stamp][player_centroid]) + " and ID = " + str(player_centroid) + ' and "T Stamp" = ' + str(T_Stamp), 1)

algresult4 = processing.run("native:centroids", {'INPUT':QgsProcessingFeatureSourceDefinition(possible_regions.id(), True),'ALL_PARTS':False,'OUTPUT':'TEMPORARY_OUTPUT'})
output4 = algresult4["OUTPUT"]
for feature4 in output4.getFeatures():
    feature_centroid = feature4
    attributes = feature4.attributes()
    feature_centroid.setAttributes([fid_centroid, attributes[2], attributes[6]])
    fid_centroid += 1
    centroid_dataprovider.addFeatures([feature_centroid])
    centroid_layer.updateExtents()
    centroid_layer.updateFields()


