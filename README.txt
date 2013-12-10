This package allows for graph theory analyses of how a network grows.

This module can analyze any network (in csv form), regardless of size, because it uses a graph theory database to store the network.

It can then grow the network, starting with one node, ending with the entire networt or the number of nodes the user sets.

It can measure various graph theory properties as the network grows, including modularity, number of communities, and clique sizes.

It has the option of growing various random but controlled graphs for comparison.

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
