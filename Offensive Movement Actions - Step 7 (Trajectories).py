import math
from qgis.core import *
import processing

lines = QgsVectorLayer("linestring", "Trajectories", "memory")
lines_wrt = lines.dataProvider()
lines_wrt.addAttributes([QgsField("Game", QVariant.String), QgsField("ID", QVariant.Int), QgsField("Result", QVariant.Int), QgsField("T_Stamp", QVariant.Int), QgsField("SV", QVariant.Double), QgsField("Goal", QVariant.Int)])
lines.updateFields()

Regions = QgsProject.instance().mapLayersByName("Statistics")[0]

regions_per_game = {}
trajectories_per_game = {}
regions_trajectories = {}

test = 0
test1 = 0

for region in Regions.getFeatures():
    
    if region["Game"] not in regions_per_game:
        regions_per_game[region["Game"]] = {}
        regions_trajectories[region["Game"]] = {}
    
    if region["ID"] not in regions_per_game[region["Game"]]:
        regions_per_game[region["Game"]][region["ID"]] = []
        regions_trajectories[region["Game"]][region["ID"]] = {}
    
    regions_per_game[region["Game"]][region["ID"]].append(int(region["T Stamp"]))
    regions_trajectories[region["Game"]][region["ID"]][region["T Stamp"]] = region


for game in regions_per_game:
    
    trajectories_per_game[game] = {}
    
    for ID in regions_per_game[game]:
        
        trajectories_per_game[game][ID] = {}
        
        regions_per_game[game][ID].sort()
        
        previous_T = 0
        
        for T in regions_per_game[game][ID]:
            T_start = T
            
            if previous_T == 0:
                previous_T = T
            
            if T - previous_T < 10000:
                T_start = previous_T
            else:
                previous_T = T
            
            if T_start in trajectories_per_game[game][ID]:
                trajectories_per_game[game][ID][T_start].append(T)
            else:
                trajectories_per_game[game][ID][T_start] = [T]
            
            


print(trajectories_per_game)

for game_1 in trajectories_per_game:
    
    if game_1[6] == "1":
        addition = "Firsthalf"
    else:
        addition = "Secondhalf"
    
    Name = game_1[:3].capitalize() + game_1[3:6].capitalize()
    
    tracking = QgsProject.instance().mapLayersByName(Name + " Tracking" + addition)[0]
    players = QgsProject.instance().mapLayersByName(Name + " Players")[0]
    player_list = []
    for player in players.getFeatures():
        player_list.append(int(player.attributes()[0]))
    
    for ID_1 in trajectories_per_game[game_1]:
        if int(ID_1) in player_list:
            for T_1 in trajectories_per_game[game_1][ID_1]:
                trajectory_ft = QgsFeature()
                
                point_list = []
                
                bound = 6000
                for unit in trajectories_per_game[game_1][ID_1][T_1][0:6]:
                    bound -= 1000
                
                lower_bound = trajectories_per_game[game_1][ID_1][T_1][0] - bound
                upper_bound = trajectories_per_game[game_1][ID_1][T_1][-1] + bound
                
                for feature in tracking.getFeatures():
                    if feature["T"] > lower_bound:

                        if feature["T"] < upper_bound:

                            X = feature[str(ID_1) + "_X"]
                            Y = feature[str(ID_1) + "_Y"]
                            if type(X) != QVariant:
                                X = float(X) / 100
                                
                                if type(Y) != QVariant:
                                    Y = float(Y) / 100
                                    
                                    point_xy = QgsPointXY(X, Y)
                                    point_list.append(point_xy)
                        
                        else:
                            break
                
                trajectory_ft.setGeometry(QgsGeometry.fromPolylineXY(point_list))
                
                trajectory_ft.setAttributes([game_1, ID_1, regions_trajectories[game_1][ID_1][T_1]["Result"], T_1, regions_trajectories[game_1][ID_1][T_1]["Sum xG"], regions_trajectories[game_1][ID_1][T_1]["Goal"]])
                
                lines_wrt.addFeature(trajectory_ft)
                lines.updateExtents()
                lines.updateFields()


print(test1)
print(test)
QgsProject.instance().addMapLayer(lines)
    
    