import math
from qgis.core import *
import processing

#needed for geometry calculations
d = QgsDistanceArea()
d.setEllipsoid('WGS84 / Plate Carree')

#INPUT
HalfStr = "XxxXXx1"

T_attackers = {}

#END INPUT

T_List = []
T_possession = {}

Players = QgsProject.instance().mapLayersByName(HalfStr[:6] + " Players")[0]


#Playerlist
PlayerList = []
PlayerDict = {}
for object in Players.getFeatures():
    attr = object.attributes()
    PlayerList.append(int(attr[0]))
    PlayerDict[int(attr[0])] = attr[5]

for T_att in T_attackers:
    if len(T_attackers[T_att]) > 0:
        T_List.append(T_att)
        T_possession[T_att] = PlayerDict[T_attackers[T_att][0]]

intersection_lines = QgsProject.instance().mapLayersByName(HalfStr + " - intersection lines")[0]
poly_contours = QgsProject.instance().mapLayersByName(HalfStr + " - possible regions")[0]
centroids = QgsProject.instance().mapLayersByName(HalfStr + " - centroids")[0]

#OUTPUT
dominant_regions = QgsProject.instance().mapLayersByName(HalfStr + " - dominant regions")[0]
dominant_dataprovider = dominant_regions.dataProvider()

centroids_amount = 0
regions_amount = 0

checklist = {}
for dominant_region in dominant_regions.getFeatures():
    regions_amount += 1
    attr_dom0 = dominant_region.attributes()
    if attr_dom0[3] in T_List:
        T_List.remove(attr_dom0[3])
    
regions_fid = regions_amount + 1

test = 0

#Pitch Dimensions
Pitch_length = 105
Pitch_width = 68

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
contours_amount += 5

print(len(T_List))

#Processing
for T0 in T_List:
    for player in PlayerList:
        if PlayerDict[player] == T_possession[T0]:
            test += 1
            centroids.selectByExpression("ID = " + str(player) + ' and "T Stamp" = ' + str(T0))
            if len(centroids.selectedFeatures()) > 0:
                if player in T_attackers[T0]:
                    
                #if centroids.selectedFeatures()[0].geometry().asPoint()[0] * Playing_Dir[PlayerDict[player]] > 17.5:
            
                    poly_contours.selectByExpression("ID = " + str(player) + "and T = " + str(contours[-2]) + ' and "T Stamp" = ' + str (T0))
                    intersection_lines.selectByExpression("Player1 = " + str(player) + ' and "T Stamp" = ' + str(T0))
                    
                    algresult1 = processing.run("native:splitwithlines", {'INPUT':QgsProcessingFeatureSourceDefinition(poly_contours.id(), True),'LINES':QgsProcessingFeatureSourceDefinition(intersection_lines.id(), True),'OUTPUT':'TEMPORARY_OUTPUT'})
                    output1 = algresult1["OUTPUT"]
                    
                    algresult2 = processing.run("native:selectbylocation", {'INPUT':output1,'PREDICATE':[1],'INTERSECT':QgsProcessingFeatureSourceDefinition(centroids.id(), True),'METHOD':0})
                    output2 = algresult2["OUTPUT"]
                    
                    for feature_dom0 in output2.selectedFeatures():
                        attributes_dom = feature_dom0.attributes()
                        ID0 = attributes_dom[2]
                        team0 = attributes_dom[3]
                        feature_dom = feature_dom0
                        feature_dom.setAttributes([regions_fid, ID0, team0, T0])
                        regions_fid += 1
                        regions_amount += 1
                        dominant_dataprovider.addFeatures([feature_dom])
                        dominant_regions.updateExtents()
                        dominant_regions.updateFields()

print(test)
