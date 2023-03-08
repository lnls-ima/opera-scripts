'''
Example of graph generation using Python in Opera2d.

- The analysis considers a solution with various cases.
- Cases might represent different times at a transient solution.

The following actions are performed by the script:

- The line (post-process body) for field evaluation is created.
- Buffers of B and J data along line is calculated for various cases.
. For each buffer a graph line of (X)x(By) is created.
- The lines are added to a graph.
- The buffers are exported to CSV files.
 '''

import numpy as np
from operapy import opera2d

model = opera2d.get_model_interface()
post = opera2d.get_post_processing_interface(model)
graph = opera2d.get_graphing_interface(model)

# --- INPUTS ----------------------------------------------------------#

initial_case = 29
final_case = 43

graph_name = 'By_plot_after_pulse'
buffer_name_preffix = 'fields_at_'
graph_line_name_preffix = 'line_at_'

points_in_buffer = 100
fields_in_buffer = ['X', 'Y', 'Th', 'R',
			'B', 'Bx', 'By', 'Bz', 'J', 'Jx', 'Jy', 'Jz']
plot_x_column = 'x'
plot_y_column = 'By'

buffer_filename_prefix = 'fields_at_' # if None, buffers are not exported.

# --- POST-PROCESS BODY -----------------------------------------------#

post_polyline = model.create_polyline([(-13, 0), (13., 0)], pp_body=True)

# --- BUFFER CALCULATION, GRAPHING AND EXPORTING ----------------------#

graph.create_graph(graph_name)

for n in range(initial_case, final_case+1):

	# Case-specific names.
	buffer_name = buffer_name_preffix+str(n)
	line_name = graph_line_name_preffix+str(n)
	if buffer_filename_prefix is not None:
		buffer_filename = buffer_filename_prefix + str(n) + '.csv'

	# Load case.
	post.load_case_number(n)

	# Calculate buffer at previously created line.
	my_buffer = graph.create_buffer_from_fields_on_edges(
						name=buffer_name,
						edges=post_polyline.edges,
						point_count=points_in_buffer, fields=fields_in_buffer)

	# Create line and add it to previously created graph.
	my_line = graph.create_line_from_buffer(
						name=line_name,
						buffer_name=buffer_name,
						x_array_name=plot_x_column,
						y_array_name=plot_y_column)
	graph.plot_line(my_line, graph_name)

	# Get data from buffer and export to file.
	buffer_column_names = graph.get_buffer_column_names(buffer_name)
	buffer_data_rows = [graph.get_column_data(buffer_name, buffer_column_name)
				   for buffer_column_name in buffer_column_names]
	np.savetxt(buffer_filename,
			   np.array(buffer_data_rows).T,
			   delimiter=',',
			   newline='\n',
			   header=','.join(buffer_column_names))
