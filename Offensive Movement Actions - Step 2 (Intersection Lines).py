import math
from qgis.core import *
import processing

#INPUT

HalfStr = "XxxXxx1"


#T_attackers is an output of step 1 and consists of a dictionary of Timestamps (keys) and a list of the ID's of all relevant attackers
T_attackers = {}

#END INPUT

T_List = []
T_possession = {}

Players = QgsProject.instance().mapLayersByName(HalfStr[:6] + " Players")[0]


fid_Int_Lines = 1
fid_Centroid = 1

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

layer = QgsProject.instance().mapLayersByName(HalfStr + " - possible lines")[0]
possible_regions = QgsProject.instance().mapLayersByName(HalfStr + " - possible regions")[0]

#OUTPUT
line_layer = QgsProject.instance().mapLayersByName(HalfStr + " - intersection lines")[0]
line_data = line_layer.dataProvider()

centroid_layer = QgsProject.instance().mapLayersByName(HalfStr + " - centroids")[0]
centroid_dataprovider = centroid_layer.dataProvider()

#UPDATING FIDS
for fid_feature_line in line_layer.getFeatures():
   fid_Int_Lines += 1
   fid_attr = fid_feature_line.attributes()
   if fid_attr[3] in T_List:
        T_List.remove(fid_attr[3])

for fid_feature_centroid in centroid_layer.getFeatures():
    fid_Centroid += 1

centroid_TList = {}
intersection_list = {}

test = 0

for T3 in T_List:
    intersection_list[T3] = {}
    for player_intersection1 in PlayerList2:
        intersection_list[T3][player_intersection1] = {}
        for player_intersection2 in PlayerList2:
            if player_intersection1 != player_intersection2:
                intersection_list[T3][player_intersection1][player_intersection2] = []

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

print(len(T_List))
T_List = T_List[:250]

contours.append(12)
contours.append(16)
contours.append(20)
contours.append(39)
contours.append(40)
contours_amount += 5

for T1 in T_List:
    layer.selectByExpression('"T Stamp" = ' + str(T1))
    algresult0 = processing.run("native:lineintersections", {"INPUT" : QgsProcessingFeatureSourceDefinition(layer.id(), True), 'INPUT_FIELDS' : [], 'INTERSECT' : QgsProcessingFeatureSourceDefinition(layer.id(), True), 'INTERSECT_FIELDS' : [], 'INTERSECT_FIELDS_PREFIX' : '', 'OUTPUT' : 'TEMPORARY_OUTPUT'})
    output0 = algresult0["OUTPUT"]
    for point in output0.getFeatures():
        intersection_attributes = point.attributes()
        #IF T (contour) == T (contour)
        if intersection_attributes[3] == intersection_attributes[9]:
            ID_intersection_1 = intersection_attributes[1]
            ID_intersection_2 = intersection_attributes[7]
            
            intersection_list[T1][ID_intersection_1][ID_intersection_2].append(point)
    layer.removeSelection()

for T0 in T_List:
    centroid_TList[T0] = {}
    for player1 in PlayerList2:
        if player1 in T_attackers[T0]:
            centroid_from = contours[-1]
            for player2 in PlayerList2:
                    if player2 != player1:
                        point_dict = {}
                        for point1 in intersection_list[T0][player1][player2]:
                            point_attr = point1.attributes()

                            point1geom = point1.geometry().asPoint()
                            point1XY = QgsPointXY(point1geom)
                            T_key = point_attr[3]
                            if T_key in point_dict:
                                list_variable = point_dict[T_key]
                                list_variable.append(point1XY)
                                point_dict[T_key] = list_variable
                            else:
                                point_dict[T_key] = [point1XY]
                        
                        if contours[-1] in point_dict:
                            test += 1
                            line = QgsFeature()
                            startpoint = point_dict[contours[-1]][0]
                            point_sequence = [startpoint]
                            
                            count = contours[-1]
                            point_Tlist = []
                            while count >= 0:
                                if count in point_dict:
                                    point_Tlist.append(count)
                                count -= 1
                            
                            if point_Tlist[-1] < centroid_from:
                                centroid_from = point_Tlist[-1]
                            
                            last_point = startpoint
                            indexes_list = {contours[-1]:0}
                            
                            for point_T in point_Tlist[1::]:
                                measureline0 = d.measureLine(last_point, point_dict[point_T][0])
                                measureline1 = d.measureLine(last_point, point_dict[point_T][1])
                                if measureline0 < measureline1:
                                    indexes_list[point_T] = 0
                                    point_sequence.append(point_dict[point_T][0])
                                    last_point = point_dict[point_T][0]
                                else:
                                    indexes_list[point_T] = 1
                                    point_sequence.append(point_dict[point_T][1])
                                    last_point = point_dict[point_T][1]
                            
                            for point_T1 in point_Tlist[-1::-1]:
                                point_sequence.append(point_dict[point_T1][not indexes_list[point_T1]])
                            
                            line.setGeometry(QgsGeometry.fromPolylineXY(point_sequence))
                            line.setAttributes([fid_Int_Lines, player1, player2, T0])
                            line_data.addFeatures([line])
                            line_layer.updateExtents()
                            line_layer.updateFields()
                            
                            fid_Int_Lines += 1
                            
                            point_Tlist.clear()
                            point_sequence.clear()
                            indexes_list.clear()
                        
                        point_dict.clear()
            
            centroid_TList[T0][player1] = centroid_from



