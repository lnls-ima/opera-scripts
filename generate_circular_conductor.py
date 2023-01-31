# Generates conductors with constant linear cross-section.
# If an angle is set, the conductor is curved around a given positive
#     (0, +rotation_center_y, 0) point by that ammount.
# The conductor generation script is saed on the clipboard (requires pyperclip)
# note: results are not good for angle > 45°
import numpy as np
import importlib.util

if importlib.util.find_spec('pyperclip') is not None:
    import pyperclip
    to_clipboard = True
else:
    to_clipboard = False

sqr = np.sqrt(2)/2

# --- INPUTS ----------------------------------------------------------#
a
# Set length (from 0 to (0,0,length)).
length = 450
# OR rotation center (in y axis, rotation around x) and angle (in degrees).
rotation_center_y = None
angle = None
# Note: angle==None controls which type of conductor is created.

# Wire radius and current density.
radius = 0.64
current_dens = 1
# Further parameters.
tolerance = 0.001
drive_label = 'Default_Drive'
coordinate_system = 'coil1_p8'

# --- GENERATE POINTS -------------------------------------------------#

if angle is None:

    face1_corners = np.array([[sqr*radius, sqr*radius, 0],
                            [sqr*radius, -sqr*radius, 0],
                            [-sqr*radius, -sqr*radius, 0],
                            [-sqr*radius, sqr*radius, 0]])
    face1_extremes = np.array([[radius,0,0],
                            [0,-radius,0],
                            [-radius,0,0],
                            [0,radius,0]])

    face2_corners = face1_corners + np.array([0,0,length/2])
    face3_corners = face1_corners + np.array([0,0,length])
    face3_extremes = face1_extremes + np.array([0,0,length])

else:

    cosd = lambda x: np.cos(np.radians(x))
    sind = lambda x: np.sin(np.radians(x))
    rotx = np.array([[ 1            , 0            ,  0            ],
                    [ 0.           , cosd(-angle/2), -sind(-angle/2)],
                    [ 0            , sind(-angle/2),  cosd(-angle/2)]])

    face1_corners = np.array([[sqr*radius, sqr*radius, 0],
                            [sqr*radius, -sqr*radius, 0],
                            [-sqr*radius, -sqr*radius, 0],
                            [-sqr*radius, sqr*radius, 0]])
    face1_extremes = np.array([[radius,0,0],
                            [0,-radius,0],
                            [-radius,0,0],
                            [0,radius,0]])

    face1_corners = face1_corners - np.array([0,rotation_center_y,0])
    face1_extremes = face1_extremes - np.array([0,rotation_center_y,0])

    face2_corners = np.zeros((4,3))
    face3_corners = np.zeros((4,3))
    face3_extremes = np.zeros((4,3))

    for i in range(4):
        face2_corners[i] = rotx @ face1_corners[i]
        face3_corners[i] = rotx @ face2_corners[i]
        face3_extremes[i] = rotx @ (rotx @ face1_extremes[i])

    face1_corners = face1_corners + np.array([0,rotation_center_y,0])
    face1_extremes = face1_extremes + np.array([0,rotation_center_y,0])
    face2_corners = face2_corners + np.array([0,rotation_center_y,0])
    face3_corners = face3_corners + np.array([0,rotation_center_y,0])
    face3_extremes = face3_extremes + np.array([0,rotation_center_y,0])

# --- CREATE COMMAND --------------------------------------------------#

all_points = np.concatenate([face1_corners,
                            face3_corners,
                            face1_extremes,
                            face2_corners,
                            face3_extremes])

comi = "BRICK20 OPTION=NEW -KEEP "

for point_number, point_coordinates in zip(range(1,21), all_points):
    print('Point', point_number, ':', point_coordinates)
    x,y,z = point_coordinates
    comi += f"XP{point_number:d}={x:.8f} "
    comi += f"YP{point_number:d}={y:.8f} "
    comi += f"ZP{point_number:d}={z:.8f} "

comi += "INCIRCUIT=NO CIRCUITELEMENT= "
comi += f"CURD={current_dens} TOLERANCE={tolerance} DRIVELABEL='{drive_label}' "
comi += "THETA2=0 PHI2=0 PSI2=0 XCEN2=0 YCEN2=0 ZCEN2=0 "
comi += f"LCNAME='{coordinate_system}' RXY=0 RYZ=0 RZX=0 SYMMETRY=1 MODELCOMPONENT=NO"
comi += f"RXY=0 RYZ=0 RZX=0 SYMMETRY=1 MODELCOMPONENT=NO"

# --- OUTPUT ----------------------------------------------------------#

for point_number, point_coordinates in zip(range(1,21), all_points):
    print('Point', point_number, ':', point_coordinates)

if to_clipboard:
    pyperclip.copy(comi)
    print('comi code exported to clipboard')
else:
    print('comi code not exported to clipboard, pyperclip library not found')

