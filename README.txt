This package allows for graph theory analyses of how a network grows.

This module can analyze any network (in csv form), regardless of size, because it uses a graph theory database to store the network.

It can then grow the network, starting with one node, ending with the entire networt or the number of nodes the user sets.

It can measure various graph theory properties as the network grows, including modularity, number of communities, and clique sizes.

It has the option of growing various random but controlled graphs for comparison.

It has the options of true random growth, preferential attachement, and unconnected growth.

It also allows one the option of plotting the graph theory properties or drawing the network as the network grows.

It also allows one to call any Bayes Net Toolbox (MATLAB) function without having to use MATLAB, and you get Python objects back.

This module is dependent on Octave, Oct2py, Neo4j, and py2neo. But don't worry! One line will install everything.

$ python setup.py install

If you want to load in a graph and grow it...

$ import grow
$ graph, randomgraph, data = grow.grow(csvfile = 'graph.csv')

This returns:

The network as a NetworkX graph.
The random graph, if one is grown.
The partition (i.e., communities) of both random and real graphs, as a dictionary of nodes and community number
Pandas Dataframe of:
node growth
edge growth
modularity values (real and random)
number of partitions (real and random)
clique size (real and random)
average clique size (real and random)
run times for each measurement of the graphs

Parameters:

csvfile: str of the cvs file your graph is represented in, with each line an edge, with the 0 column being the parent.

growthfactor: int, How many nodes do you want to grow your graph to? Default: 100

wholegrowth: Boolean, This will grow the entire graph. Default: False

verbose: Boolean, Do you want to see what's going on while it grows? Default: True
	
sparse: Boolean, Do you want to measure sparely? This can really speed things up for a larger graph. It measures on a log scale, e.g., 1, 3, 9, 27...Default: True

num_measurements: int, How many times do you want to measure the graph? Default: 10

preferential, Boolean, if True, the source nodes are more likely to have higher degree during growth.
	
force_connected: Boolean, Do you want the graph to remain connected as it grows? Default: True

directed: Boolean, Is your graph directed? Right now, this only supports directed graphs. Default: True

draw: Boolean, Do you want to see the graph as it grows? Default: False, note: You cannot plot and draw at the same time. It will default to plot if you have both True.

drawgraph: str, What graph do you want to draw? Options: 'triangulated', 'moralized', 'directed'

drawspectral: Boolean, This will draw a spectral layout of the graph instead of a random one. Default: False

plot: Boolean, Do you want to plot the growth measurements as the graph grows? Default: False

plotx: str, What x axis do you want to plot? Options: 'nodegrowth', 'edgegrowth', 'maxclique', 'modval', 'run_time', 'avgclique', Default: 'nodegrowth'

ploty: str, What y axis do you want to plot? Options: 'nodegrowth', 'edgegrowth', 'maxclique', 'modval', 'run_time', 'avgclique', Default: 'maxclique'

ploty2: str, What 2nd y axis do you want to plot? Options: 'nodegrowth', 'edgegrowth', 'maxclique', 'modularity', 'run_time', 'avgclique', Default: 'modval'

reverserandom: Boolean, This will reverse the direction of edges and grow that as a "random" graph alongside the real graph.

outgoingrandom: Boolean, This will shuffle all the outgoing edges, keeping the out-degree the same, and grow that as a "random" graph alongside the real graph.

incomingrandom = Boolean, This will shuffle all the incoming edges, keeping the in-degree the same, and grow that as a "random" graph alongside the real graph.

totalrandom = Boolean, This uses a graph picked randomly out of the set of all graphs with the same number of nodes and edges as the real graph, and then grow that as a "random" graph alongside the real graph. This preserves overall degree, and number of nodes/edges.

super_modular = Boolean, This will create the most modular version of your graph that is still fully connected. It takes edges that exist between the communities and adds them within communities, preserving edge and node number. This is interesting for Bayesian Analysis and Fodorian ideas about modularity and inference.

random_modular = Boolean, This will make a very modular version of your graph. It takes edges that exist between the communities and adds them within communities, preserving edge and node number. This is interesting for Bayesian Analysis and Fodorian ideas about modularity and inference.
	
