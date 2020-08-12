import math
from qgis.core import *
import processing

#INPUT

HalfStr = "XxxXxx1"

#END INPUT

track_points = QgsProject.instance().mapLayersByName(HalfStr + " - tracking")[0]
middlepoints = QgsProject.instance().mapLayersByName(HalfStr + " - middlepoints")[0]
dominant_regions = QgsProject.instance().mapLayersByName(HalfStr + " - dominant regions")[0]

xG_Left = QgsProject.instance().mapLayersByName("xg curve left")[0]
xG_Right = QgsProject.instance().mapLayersByName("xg curve right")[0]

#OUTPUT
temp_lines = QgsVectorLayer("linestring", "lines", "memory")
lines_data = temp_lines.dataProvider()
lines_data.addAttributes([QgsField("T_Stamp", QVariant.Int), QgsField("height", QVariant.Double)])
temp_lines.updateFields()

temp_points = QgsVectorLayer("point", HalfStr + " - real xg points", "memory")
temp_data = temp_points.dataProvider()
temp_data.addAttributes([QgsField("xG", QVariant.Double), QgsField("T_Stamp", QVariant.Int)])
temp_points.updateFields()

#needed for geometry calculations
d = QgsDistanceArea()
d.setEllipsoid('WGS84 / Plate Carree')

#Ball physics
max_ballV0 = 100 #km/h
max_ballV = max_ballV0/3.6 #m/s

T_List = []
T_Possession = {}

for dominant_region_feature in dominant_regions.getFeatures():
    dominant_attr = dominant_region_feature.attributes()
    if dominant_attr[3] not in T_List:
        T_List.append(dominant_attr[3])
        T_Possession[dominant_attr[3]] = dominant_attr[2]

for T0 in T_List:
    
    Line_list = {}
    Line_time = {}
    
    dominant_regions.selectByExpression('"T Stamp" = ' + str(T0) + " and Team = " + "'" + str(T_Possession[T0]) + "'")
    
    for dom_region in dominant_regions.selectedFeatures():
        if dom_region.geometry().centroid().asPoint()[0] < 0:
            PlayDir = {dom_region.attributes()[2]: -1, 'Opponent': 1}
        elif dom_region.geometry().centroid().asPoint()[0] > 0:
            PlayDir = {dom_region.attributes()[2]: 1, 'Opponent': -1}

    if PlayDir[T_Possession[T0]] == 1:
        Curve = xG_Right
    else:
        Curve = xG_Left
    
    algresult0 = processing.run("native:selectbylocation", {'INPUT': Curve,'PREDICATE':[6],'INTERSECT':QgsProcessingFeatureSourceDefinition(dominant_regions.id(), True),'METHOD':0})
    output0 = algresult0["OUTPUT"]
    
    List_0 = []
    for feature0 in output0.selectedFeatures():
        List_0.append(feature0)
    
    if len(List_0) > 0:
        track_points.selectByExpression('"T Stamp" = ' + str(T0) + " and ID = 101")
        ball = track_points.selectedFeatures()[0].geometry().asPoint()
        
        xG_eta = {}
        for xG_point1 in List_0:
            xG_eta[xG_point1] = {}
        
        middlepoints.selectByExpression('"T Stamp" = ' + str(T0) + " and T < 30")
        for middlepoint in middlepoints.selectedFeatures():
            point_xy = middlepoint.geometry().asPoint()
            if True:
                attr0 = middlepoint.attributes()
                team_point = attr0[2]
                for xG_point2 in xG_eta:
                    
                    if team_point not in xG_eta[xG_point2]:
                        xG_eta[xG_point2][team_point] = 40
                    
                    distance0 = d.measureLine(xG_point2.geometry().asPoint(), point_xy)
                    
                    if distance0 < attr0[5]:

                        if attr0[4] < xG_eta[xG_point2][team_point]:
                            xG_eta[xG_point2][team_point] = attr0[4]
        
        point_to_line = {}
        
        for xG_point3 in xG_eta:
            point_to_line[xG_point3] = []
            eta = xG_eta[xG_point3][T_Possession[T0]] * 0.25
            last_point = ball
            distance1 = d.measureLine(ball, xG_point3.geometry().asPoint())
            ball_velocity = distance1/eta
            
            while ball_velocity > max_ballV:
                eta += 0.25
                ball_velocity = distance1/eta
            
            direction = math.atan2(ball[1] - xG_point3.geometry().asPoint()[1], ball[0] - xG_point3.geometry().asPoint()[0])
            
            max_height = 9.81 * (0.5 * eta) ** 2
            V = 0.5 * 9.81 * eta
            
            T_step = 0
            max_dist = 0.25 * ball_velocity
            while distance1 > max_dist:
                point_a = QgsPointXY(last_point[0] + math.cos(3.14 - direction) * max_dist, last_point[1] + math.sin(-direction) * max_dist)
                line1 = QgsFeature()
                line1.setGeometry(QgsGeometry.fromPolylineXY([last_point, point_a]))
                t3 = T_step * 0.25 + 0.125
                avg_h = V * t3 - 0.5 * 9.81 * t3 ** 2
                line1.setAttributes([T_step, avg_h])
                point_to_line[xG_point3].append(line1)
                lines_data.addFeatures([line1])
                if avg_h < 2:
                    if T_step in Line_list:
                        Line_list[T_step].append(line1)
                    else:
                        Line_list[T_step] = [line1]
                
                T_step += 1
                last_point = point_a
                distance1 -= max_dist
            
            if distance1 > 0.1:
                line1 = QgsFeature()
                point_a = QgsPointXY(last_point[0] + math.cos(3.14 - direction) * distance1, last_point[1] + math.sin(-direction) * distance1)
                line1.setGeometry(QgsGeometry.fromPolylineXY([last_point, point_a]))
                t3 = T_step * 0.25 + 0.125
                avg_h = V * t3 - 0.5 * 9.81 * t3 ** 2
                line1.setAttributes([T_step, avg_h])
                point_to_line[xG_point3].append(line1)
                lines_data.addFeatures([line1])
                if avg_h < 2:
                    if T_step in Line_list:
                        Line_list[T_step].append(line1)
                    else:
                        Line_list[T_step] = [line1]
        
        for middlepoint1 in middlepoints.selectedFeatures():
            attr1 = middlepoint1.attributes()
            if attr1[3] != T_Possession[T0]:
                point_xy1 = middlepoint.geometry().asPoint()
                
                for line_key in Line_list:
                    for line2 in Line_list[line_key]:
                        line_centroid = line2.geometry().centroid().asPoint()
                        distance3 = d.measureLine(line_centroid, point_xy1)
                        if distance3 > attr1[5]:
                            if line2 in Line_time:
                                Line_time[line2] = min(Line_time[line2], attr1[4] * 0.25)
                            else:
                                Line_time[line2] = attr1[4] * 0.25
        
        int_time = {}
        
        for line_key1 in Line_list:
            for line3 in Line_list[line_key1]:
                if line3 in Line_time:
                    int_time[line3] = line_key1 * 0.25 - Line_time[line3]
                else:
                    int_time[line3] = 0
        
        
        for xG_point4 in xG_eta:
            attr5 = xG_point4.attributes()
            interception_chance = 1
            for line4 in point_to_line[xG_point4]:
                if line4 in int_time:
                    interception_chance = interception_chance * (1 - min(1, int_time[line4]))
            real_xg = interception_chance * attr5[2]
            temp_point = QgsFeature()
            temp_point.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(xG_point4.geometry().asPoint())))
            temp_point.setAttributes([real_xg, T0])
            temp_data.addFeature(temp_point)
            temp_points.updateExtents()

print(len(T_List))
QgsProject.instance().addMapLayer(temp_points)
#QgsProject.instance().addMapLayer(temp_lines)


