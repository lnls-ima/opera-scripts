'''
halbach_2d_cylinders.py
Script for generating a 2D cylinders-based Halbach array model.
'''

from time import time
import numpy as np
from operapy import opera2d
from operapy import canvas

# ------------------------------------------------------ #
# --- INPUTS ------------------------------------------- #
# ------------------------------------------------------ #

# Base parameters for cylinders distribution.
# The cylinders diameter will be automatically calculated based on these
# two parameters and on the three gap parameters bellow.
n_blocks = 12
bore_diameter = 270
# Gap between cylinders (gap_blocks) and additional thicknesses inside
# and outside the cylinders region. These parameters represent the
# space needed for the material supporting the cylinders.
# They are given as percentages of the cylinders diameter.
# e.g. core_inner_thickness=0.1 means the cylinders region inner radius
#      will be 0.5*bore_diameter + 10% of the cylinder radius.
gap_blocks = 0.10
core_inner_thickness = 0.10
core_outer_thickness = 0.10

# Radius of good field region circle (half DSV) and number of points
# for calculating field on its boundary.
gfr_radius = 20
gfr_points = 3600

# Size of circles compounding the background. Each element in this
# list represents one layer of background and its value is given as a
# percentage of the total device radius.
# e.g. if the list is [1.25, 2.00] the background will be formed by an
#      inner circle whose radius is 125% of the total device radius and
#      a second circle with radius 200% of the total device radius.
# Note that the total device radius is calculated automatically and
# depends on the bore_diameter, number of cylinders, gap between blocks
# and inner/outer core thicknesses.
bgs_factor = [1.1, 1.2, 1.4, 1.8, 2.6, 5.0]

# Mesh size for blocks and for core (the space between blocks given by
# core_inner_thickness and core_inner_thickness.
mesh_blocks = bore_diameter/80
mesh_core = bore_diameter/80
# Mesh sizes for background. Must be of the same length as bgs_factor.
bgs_mesh = [bore_diameter/80,
            bore_diameter/40,
            bore_diameter/20,
            bore_diameter/10,
            bore_diameter/5,
            bore_diameter/5]
# Overall configuration for maximum mesh size.
mesh_max = 32

# Prefix name for output files, including solved .op2_h5 solved model
# and .dat file wih field data at the good field region boundary.
model_name_prefix = 'halbach'

# ------------------------------------------------------ #
# --- INTERFACES AND GENERAL SETTINGS ------------------ #
# ------------------------------------------------------ #

model = opera2d.get_model_interface()
post = opera2d.get_post_processing_interface(model)
graph = opera2d.get_graphing_interface(model)

model.use_si_units()
model.use_unit(opera2d.Unit.Length.Millimetre)

model.analysis_settings.physics_type = opera2d.PhysicsType.Magnetostatic
model.analysis_settings.transient_em_settings.is_nonlinear = True

model.general_settings.mesh_size = mesh_max

# ------------------------------------------------------ #
# --- MATERIALS ---------------------------------------- #
# ------------------------------------------------------ #

material_aluminium = model.create_material("Aluminium")
material_aluminium.color = '#a39aaf'

bh_data_ndfeb = np.loadtxt('N45SH_ndfebo.bh', skiprows=1)
bh_curve_ndfeb = model.create_bh_curve("NdFeB")
bh_curve_ndfeb.set_bh_values(opera2d.ModelValueVector(tuple(bh_data_ndfeb.T[0]), opera2d.Unit.MagneticFluxDensity.Tesla),
                             opera2d.ModelValueVector(tuple(bh_data_ndfeb.T[1]), opera2d.Unit.MagneticFieldStrength.AmperePerMetre))
material_ndfeb = model.create_material("NdFeB")
material_ndfeb.permeability_type = opera2d.MaterialPermeabilityType.Nonlinear
material_ndfeb.color = '#05e679'
material_ndfeb.bh_curve = bh_curve_ndfeb

# ------------------------------------------------------ #
# --- CONSTRUCT HALBACH DIPOLE ------------------------- #
# ------------------------------------------------------ #

# Determine other base device dimensions.
s = np.sin(np.pi/n_blocks)
block_diameter = bore_diameter*s/(1 - s - 2*core_inner_thickness*s + gap_blocks)
device_diameter = bore_diameter \
                  + 2*block_diameter \
                  + 2*core_inner_thickness*block_diameter \
                  + 2*core_outer_thickness*block_diameter

core_base = model.create_circle(opera2d.ModelPointValue((0.0, 0.0), opera2d.Unit.Length.Millimetre),
                                opera2d.ModelValue(0.5*device_diameter, opera2d.Unit.Length.Millimetre),
                                split=True)

core_cut_1 = model.create_circle(opera2d.ModelPointValue((0.0, 0.0), opera2d.Unit.Length.Millimetre),
                                 opera2d.ModelValue(0.5*bore_diameter, opera2d.Unit.Length.Millimetre),
                                 split=True)
core_full = model.boolean_subtraction(core_base, [core_cut_1])
core_cut_2 = model.create_rectangle(opera2d.ModelPointValue((0.0, 0.0), opera2d.Unit.Length.Metre),
                                    opera2d.ModelPointValue((device_diameter, device_diameter), opera2d.Unit.Length.Metre),
                                    split=True)
core_quarter_1 = model.boolean_intersection(core_full, [core_cut_2])
core_quarter_2,  = model.copy_bodies([core_quarter_1], mirror=opera2d.ModelValue(90.0, opera2d.Unit.Angle.Degree))
core_quarter_12 = model.boolean_nonregular_union(core_quarter_1, [core_quarter_2])
core_quarter_34,  = model.copy_bodies([core_quarter_12], mirror=opera2d.ModelValue(0.0, opera2d.Unit.Angle.Degree))
core = model.boolean_nonregular_union(core_quarter_12, [core_quarter_34])
core.name = 'core'
for region in core.regions:
    region.material = material_aluminium
    region.mesh_size = mesh_core

upper_block = model.create_circle(opera2d.ModelPointValue((0.0, 0.5*bore_diameter+core_inner_thickness*block_diameter+0.5*block_diameter), opera2d.Unit.Length.Millimetre),
                                  radius=opera2d.ModelValue(0.5*block_diameter, opera2d.Unit.Length.Millimetre),
                                  split=True)
blocks = [upper_block] + model.copy_bodies([upper_block],
                                            rotation_copies=n_blocks-1,
                                            rotation_angle=opera2d.ModelValue(360/n_blocks, opera2d.Unit.Angle.Degree))
properties = [model.create_properties(f'easy-axis_{i:d}') for i in range(n_blocks)]
for i, (block, property) in enumerate(zip(blocks, properties)):
    block.name = f'block_{i:d}'
    property.rotation_angle = opera2d.ModelValue(90+(i*720/n_blocks)%360, opera2d.Unit.Angle.Degree)
    for region in block.regions:
        region.material = material_ndfeb
        region.properties = property
        region.mesh_size = mesh_blocks

# ------------------------------------------------------ #
# --- BACKGROUND AND BOUNDARY CONDITIONS --------------- #
# ------------------------------------------------------ #

bgs = []
for i, (bg_factor, bg_mesh) in enumerate(zip(bgs_factor, bgs_mesh)):
    bgs += [model.create_circle(opera2d.ModelPointValue((0.0, 0.0), opera2d.Unit.Length.Millimetre),
                                radius=opera2d.ModelValue(0.5*device_diameter*bg_factor, opera2d.Unit.Length.Millimetre),
                                name=f'bg{i:d}', split=True)]
    for region in bgs[i].regions:
        region.mesh_size = bg_mesh
for bg in bgs:
    model.send_to_back(bg)

tan_boundary_condition = model.create_boundary_condition("tangent_magnetic")
tan_boundary_condition.set_tangential_field_magnetic()
for edge in bgs[-1].edges:
    edge.boundary_condition = tan_boundary_condition
for vertex in bgs[-1].vertices:
    vertex.boundary_condition = tan_boundary_condition

# ------------------------------------------------------ #
# --- MESHING, SOLVE AND SCRIPT END -------------------- #
# ------------------------------------------------------ #

t0 = time()
model.generate_mesh()
t1 = time()
model.solve(model_name_prefix + '.op2_h5', overwrite=True)
t2 = time()

time_mesh = t1 - t0
time_solve = t2 - t1

# ------------------------------------------------------ #
# --- POST-PROCESSING ---------------------------------- #
# ------------------------------------------------------ #


post_circle = model.create_circle(opera2d.ModelPointValue((0, 0), opera2d.Unit.Length.Millimetre),
                                radius=opera2d.ModelValue(gfr_radius, opera2d.Unit.Length.Millimetre), pp_body=True)

graph.create_graph('graph_gfr_field_amplitude')

buffer_gfr_fields = graph.create_buffer_from_fields_on_edges(
                    name='buffer_gfr_fields',
                    edges=post_circle.edges,
                    point_count=gfr_points,
                    fields=['B', 'Bx', 'By', 'Bz'])

line = graph.create_line_from_buffer(
                    name='line_gfr_field_amplitude',
                    buffer_name='buffer_gfr_fields',
                    x_array_name='Th',
                    y_array_name='B')
graph.plot_line(line, 'graph_gfr_field_amplitude')
graph.set_line_properties('line_gfr_field_amplitude', 'graph_gfr_field_amplitude',
                        style=opera2d.PenStyle.NoPen,
                        symbol=opera2d.SymbolStyle.Circle,
                        symbol_size=4)

buffer_column_names = graph.get_buffer_column_names('buffer_gfr_fields')
buffer_data_rows = [graph.get_column_data('buffer_gfr_fields', buffer_column_name)
                    for buffer_column_name in buffer_column_names]

bmin = min(buffer_data_rows[buffer_column_names.index('B')])
bmax = max(buffer_data_rows[buffer_column_names.index('B')])
b0_object = post.calculate_field_at_point((0.0, 0.0), 'B')
b0 = b0_object.field_expression_result
hom = 1e6*(bmax - bmin)/(2*b0)

# File output.
header = ''
header += f'{"n_blocks":<25}: {n_blocks}\n'
header += f'{"bore_diameter (mm)":<25}: {bore_diameter}\n'
header += f'{"gap_blocks":<25}: {gap_blocks}\n'
header += f'{"gap_blocks (mm)":<25}: {gap_blocks*block_diameter}\n'
header += f'{"core_inner_thickness":<25}: {core_inner_thickness}\n'
header += f'{"core_inner_thickness (mm)":<25}: {core_inner_thickness*block_diameter}\n'
header += f'{"core_outer_thickness":<25}: {core_outer_thickness}\n'
header += f'{"core_outer_thickness (mm)":<25}: {core_outer_thickness*block_diameter}\n'
header += f'{"gfr_radius (mm)":<25}: {gfr_radius}\n'
header += f'{"gfr_points":<25}: {gfr_points}\n'
header += f'{"mesh_blocks (mm)":<25}: {mesh_blocks}\n'
header += f'{"mesh_core (mm)":<25}: {mesh_core}\n'
header += f'{"bgs_factor":<25}: {str(bgs_factor)}\n'
header += f'{"bgs_mesh (mm)":<25}: {str(bgs_mesh)}\n'
header += f'{"mesh_max (mm)":<25}: {mesh_max}\n'
header += f'{"Block diameter (mm)":<25}: {block_diameter}\n'
header += f'{"Device diameter (mm)":<25}: {device_diameter}\n'
header += f'{"Meshing time (s)":<25}: {time_mesh}\n'
header += f'{"Solving time (s)":<25}: {time_solve}\n'
header += f'{"Central field (T)":<25}: {b0:.12f}\n'
header += f'{"GFR radius (mm)":<25}: {bmin:.12f}\n'
header += f'{"GFR boundary max. B (T)":<25}: {bmin:.12f}\n'
header += f'{"GFR boundary min. B (T)":<25}: {bmax:.12f}\n'
header += f'{"GFR homogeneity (p.p.m.)":<25}: {hom:.2f}\n'
header +=','.join(buffer_column_names)
np.savetxt(model_name_prefix + '_gfr_fields.dat',
            np.array(buffer_data_rows).T,
            delimiter=',',
            newline='\n',
            header=header)

# Console output.
print('-'*40)
print(f'{"Bore diameter":<23}: {bore_diameter:.3f} mm')
print(f'{"Cylinders diameter:":<23}: {block_diameter:.3f} mm')
print(f'{"Gap cyl-cyl":<23}: {gap_blocks*block_diameter:.4f} mm')
print(f'{"Gap cyl-inner":<23}: {core_inner_thickness*block_diameter:.4f} mm')
print(f'{"Gap cyl-outer":<23}: {core_outer_thickness*block_diameter:.4f} mm')
print(f'{"Outer device diameter":<23}: {device_diameter:.4f} mm')
print(f'{"Meshing time":<23}: {time_mesh:.3f} s')
print(f'{"Solving time":<23}: {time_solve:.3f} s')
print('-'*40)
print(f'{"GFR radius":<23}: {gfr_radius:.4f} mm')
print(f'{"Central field":<23}: {b0:.12f} T')
print(f'{"B min. at GFR boundary":<23}: {bmin:.12f} T')
print(f'{"B max. at GFR boundary":<23}: {bmax:.12f} T')
print(f'{"GFR field homogeneity":<23}: {hom:.2f} ppm')
print('-'*40)

# ------------------------------------------------------ #
# --- VIEW, FLLUX LINES AND SCRIPT END ----------------- #
# ------------------------------------------------------ #

view = canvas.get_view()
view.zoom_fit()
view.show_outlines = True
view.show_mesh = False

default_color_map = model.get_color_map('Color (default)')
post.calculate_contour_map(name='Flux Lines',
                           regions=[],
                           field_expression='Potential',
                           contour_count=60, type=opera2d.ContourMapType.Lines,
                           color_map=default_color_map,
                           transparency=1,
                           display_material_boundaries=False,
                           exclude_air=False,
                           display_on_rotational_replications=False,
                           field_calculation_method=opera2d.FieldCalculationMethod.Nodal,
                           phase_angle=0,
                           harmonic_display_option=opera2d.HarmonicDisplayOption.Instantaneous)
