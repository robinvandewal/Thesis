import math
from qgis.core import *
import processing


#INPUT
#The input is a string consisting of 6 letters and a number
#It refers to half of a match and is used to find the correct layers, loaded in QGIS

HalfStr = "XxxXxx0"

#END INPUT


if HalfStr[6] == "1":
    addition = "Firsthalf"
elif HalfStr[6] == "2":
    addition = "Secondhalf"

Players = QgsProject.instance().mapLayersByName(HalfStr[:6] + " Players")[0]
Tracking1 = QgsProject.instance().mapLayersByName(HalfStr[:6] + " Tracking" + addition)[0]

#OUTPUT
T_List = []
T_Dict = {}
T_possession = {}
T_attackers = {}

tracking_points = QgsVectorLayer("point", HalfStr + " - tracking", "memory")
tracking_data = tracking_points.dataProvider()
tracking_data.addAttributes([QgsField("T Stamp", QVariant.Int), QgsField("ID", QVariant.Int), QgsField("Team", QVariant.String), QgsField("Velocity", QVariant.Double), QgsField("Direction", QVariant.Double)])

point_layer = QgsVectorLayer("point", HalfStr + " - Intersections", "memory")
point_data = point_layer.dataProvider()
point_data.addAttributes([QgsField("FID", QVariant.Int), QgsField("ID", QVariant.Int), QgsField("Team", QVariant.String), QgsField("T", QVariant.Int), QgsField("E1", QVariant.String), QgsField("T Stamp", QVariant.Int), QgsField("FID_2", QVariant.Int), QgsField("ID_2", QVariant.Int), QgsField("Team_2", QVariant.String), QgsField("T_2", QVariant.Int), QgsField("E2", QVariant.String), QgsField("T Stamp_2", QVariant.Int)])
point_layer.updateFields()

line_layer = QgsVectorLayer("linestring", HalfStr + " - Intersection Lines", "memory")
line_data = line_layer.dataProvider()
line_data.addAttributes([QgsField("Player1", QVariant.String), QgsField("Player_2", QVariant.String), QgsField("T Stamp", QVariant.Int)])
line_layer.updateFields()

centroid_layer = QgsVectorLayer("point", HalfStr + " - Centroids", "memory")
centroid_dataprovider = centroid_layer.dataProvider()
centroid_dataprovider.addAttributes([QgsField("ID", QVariant.Int), QgsField("T Stamp", QVariant.Int)])
centroid_layer.updateFields()

Middlepoints = QgsVectorLayer("point", HalfStr + " - Middlepoints", "memory")
Middlepoints_dataprovider = Middlepoints.dataProvider()
Middlepoints_dataprovider.addAttributes([QgsField("ID", QVariant.Int), QgsField("Team", QVariant.String), QgsField("T", QVariant.Double), QgsField("Extent", QVariant.Double), QgsField("T Stamp", QVariant.Int)])

Possible_regions = QgsVectorLayer("polygon", HalfStr + " - Possible Regions", "memory")
Possible_regions_dataprovider = Possible_regions.dataProvider()
Possible_regions_dataprovider.addAttributes([QgsField("ID", QVariant.Int), QgsField("Team", QVariant.String), QgsField("T", QVariant.Int), QgsField("Extent", QVariant.Double), QgsField("T Stamp", QVariant.Int)])

dominant_regions = QgsVectorLayer("polygon", HalfStr + " - Dominant Regions", "memory")
dominant_dataprovider = dominant_regions.dataProvider()
dominant_dataprovider.addAttributes([QgsField("ID", QVariant.Int), QgsField("Team", QVariant.String), QgsField("T Stamp", QVariant.Int)])
dominant_regions.updateFields()

#needed for geometry calculations
d = QgsDistanceArea()
d.setEllipsoid('WGS84 / Plate Carree')

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

fields1 = Tracking1.fields()

#Playerlist
PlayerList = {"ball": "None"}
TeamList = []
for object in Players.getFeatures():
    attr = object.attributes()
    PlayerList[int(attr[0])] = attr[5]
    if attr[5] not in TeamList:
        TeamList.append(attr[5])

#Playing Direction
Playing_Direction = {} # * this to always go right (positive)
collumn = 4
for feature in Tracking1.getFeatures():
    if feature.attributes()[0] == 0:
        attr1 = feature.attributes()
        while attr1[collumn] < 10 and attr1[collumn] > -10:
            collumn += 2
        if attr1[collumn] < 0:
            kickoff_dir = 1
        else:
            kickoff_dir = -1
        ID_kickoff = int(str(fields1[collumn])[11:17])
        Playing_Direction[PlayerList[ID_kickoff]] = kickoff_dir
        for Team in TeamList:
            if Team not in Playing_Direction:
                Playing_Direction[Team] = kickoff_dir * -1
        break


#Which T's are worth looking at?
test = 0
for feature2 in Tracking1.getFeatures():
    striker_check = False
    ball_check = False
    attr2 = feature2.attributes()
    if attr2[1] in TeamList:
        collumn = 4
        dir_mod = Playing_Direction[attr2[1]]
        if attr2[2] * dir_mod > 0:
            player_list2 = [[101, "None", attr2[2], attr2[3]]]
            attacker_temp = []
            ball_point = QgsPointXY(attr2[2], attr2[3])
            ball_distance = 100
            while collumn < len(attr2):
                ID = int(str(fields1[collumn])[11:17])
                Team = PlayerList[ID]
                X = attr2[collumn]
                Y = attr2[collumn + 1]
                player_list2.append([ID, Team, X, Y])
                if PlayerList[int(str(fields1[collumn])[11:17])] == attr2[1] and X: #If player in team_possession
                    distance1 = d.measureLine(QgsPointXY(X, Y), ball_point)
                    if distance1 < ball_distance:
                        ball_distance = distance1
                        pos_player = ID
                    if attr2[collumn] * dir_mod > Pitch_length * 1/4:
                        striker_check = True
                        attacker_temp.append(ID)
                collumn += 2
            if ball_distance <= 1:
                ball_check = True
        if striker_check and ball_check:
            T_List.append(int(attr2[0]))
            T_Dict[int(attr2[0])] = player_list2
            T_possession[int(attr2[0])] = attr2[1]
            if pos_player in attacker_temp:
                attacker_temp.remove(pos_player)
            T_attackers[int(attr2[0])] = attacker_temp

T_List



for T0 in T_List:
    #velocity setup
    t = T0
    tv = t - 100
    T_string = str(t)
    Tvstr = str(tv)

    #Populating snapshot layer
    Tracking1.selectByExpression('"T" = ' + T_string, QgsVectorLayer.SetSelection)
    selectionT = Tracking1.selectedFeatures()

    Tracking1.selectByExpression('"T" = ' + Tvstr, QgsVectorLayer.SetSelection)
    selectionV = Tracking1.selectedFeatures()
    for thing in selectionV:
        attrV = thing.attributes()

    for thing in selectionT:
        attr = thing.attributes()
        collumn = 2
        while collumn < len(fields1):
            x = attr[collumn]
            if x:
                x = x/100
                y = attr[collumn + 1]/100
                Tpoint = QgsPointXY(x, y)
                Vpoint = QgsPointXY(attrV[collumn]/100, attrV[collumn + 1]/100)
                ID_str = str(fields1[collumn])[11:17]
                if ID_str[0] == "b":
                    ID = 101
                    Team = "Ball"
                else:
                    ID = int(ID_str)
                    Team = PlayerList[ID]
                velocity = d.measureLine(Tpoint, Vpoint) * 10
                direction = math.atan2((attrV[collumn + 1]/100 - attr[collumn + 1]/100), (attrV[collumn]/100 - attr[collumn]/100))
                
                tracking_point = QgsFeature()
                tracking_point.setGeometry(QgsGeometry.fromPointXY(Tpoint))
                tracking_point.setAttributes([t, ID, Team, velocity, direction])
                tracking_data.addFeatures([tracking_point])
                tracking_points.updateFields()
                tracking_points.updateExtents()
                
                if ID != 101:
                    for contour in contours:
                        point1 = QgsFeature()
                        x1 = x + (math.cos(3.14-direction)*((1-math.exp(- labda*contour*contour_time))/labda)*velocity)
                        y1 = y + (math.sin(-direction)*((1-math.exp(- labda*contour*contour_time))/labda)*velocity)
                        point1.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(x1, y1)))
                        
                        radius = top_speed * (contour*contour_time - ((1-math.exp(-labda*contour*contour_time))/labda))
                        point1.setAttributes([ID, Team, contour, radius, t])
                        Middlepoints_dataprovider.addFeatures([point1])
                        Middlepoints.updateExtents()
                        Middlepoints.updateFields()
            collumn += 2

algresult1 = processing.run("native:buffer", {'INPUT':Middlepoints,'DISTANCE':QgsProperty.fromExpression('"Extent"'),'SEGMENTS':100,'END_CAP_STYLE':0,'JOIN_STYLE':0,'MITER_LIMIT':2,'DISSOLVE':False,'OUTPUT':'TEMPORARY_OUTPUT'})
output1 = algresult1["OUTPUT"]
for feature1 in output1.getFeatures():
    Possible_regions_dataprovider.addFeatures([feature1])
    Possible_regions.updateExtents()
    Possible_regions.updateFields()

#ADD LAYERS
QgsProject.instance().addMapLayer(Middlepoints)
QgsProject.instance().addMapLayer(Possible_regions)
QgsProject.instance().addMapLayer(line_layer)
QgsProject.instance().addMapLayer(centroid_layer)
QgsProject.instance().addMapLayer(dominant_regions)
QgsProject.instance().addMapLayer(tracking_points)

#print(T_List)
#print(T_possession)
print(T_attackers)
print(Playing_Direction)
print(test)



