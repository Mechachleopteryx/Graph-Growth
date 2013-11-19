This module will load very large graphs into a database and then grow that graph and measure important properties as it grows, with the option to grow a number of different random graph alongside it for comparison.
You have the option to draw the graphs as they grow, or plot the graph measurements as the graphs grow.

It is written in Python. It uses py2neo and neo4j to store the graph as a database, allowing for very large graphs. All functions were written by Maxwell Bertolero(2013), except for the Bayes Network Toolbox stuff, which is run via Octave and oct2py. 

All of the functions and dependencies can be set up with one line, in the grow directory:
$ python setup.py install  

Please see the tutorials folder for the IPython notebook tutorial.  

Here are the different options you can pass the load_graph and grow_graph functions.

csvfile: Simply pass in your CSV file. It assumes the 0 column is the parent node, and 1 is the child node. Each line is an edge.

growthfactor: int, How many nodes do you want to grow your graph to? Default: 100

wholegrowth: Boolean, This will grow the entire graph. Default: False

verbose: Boolean, Do you want to see what's going on while it grows? Default: True

sparse: Boolean, Do you want to measure sparely? This can really speed things
up for a larger graph. It measures on a log scale, e.g., 1, 3, 9, 27...
Default: True

num_measurements: int, How many times do you want to measure the graph? Default: 10

force_connected: Boolean, Do you want the graph to remain connected as it grows? Default: True

directed: Boolean, Is your graph directed? Right now, this only supports directed graphs. Default: True

draw: Boolean, Do you want to see the graph as it grows? Default: False
You cannot plot and draw at the same time. It will default to plot if you have both True.

drawgraph: str, What graph do you want to draw? Options: 'triangulated', 'moralized', 'directed'

drawspectral: Boolean, This will draw a spectral layout of the graph instead of a random one. Default: False

plot: Boolean, Do you want to plot the growth measurements as the graph grows? Default: False

plotx: str, What x axis do you want to plot? Options: 'nodegrowth', 'edgegrowth', 'maxclique', 'modval', 'run_time', 'avgclique', Default: 'nodegrowth'
ploty: str, What y axis do you want to plot? Options: 'nodegrowth', 'edgegrowth', 'maxclique', 'modval', 'run_time', 'avgclique', Default: 'maxclique'
ploty2: str, What 2nd y axis do you want to plot? Options: 'nodegrowth', 'edgegrowth', 'maxclique', 'modularity', 'run_time', 'avgclique', Default: 'modval'

reverserandom: Boolean, This will reverse the direction of edges and grow that as a "random" graph alongside the real graph.
outgoingrandom: Boolean, This will shuffle all the outgoing edges, keeping the out-degree the same, and grow that as a "random" graph alongside the real graph.
incomingrandom = Boolean, This will shuffle all the incoming edges, keeping the in-degree the same, and grow that as a "random" graph alongside the real graph.
totalrandom = Boolean, This uses a graph picked randomly out of the set of all graphs with the same number of nodes and edges as the real graph, and then
grow that as a "random" graph alongside the real graph. This preserves overall degree, and number of nodes/edges

usenx: Boolean, This uses python code wherever possible, instaeding of making use of the Matlab Bayes Net Toolbox. Default: True
