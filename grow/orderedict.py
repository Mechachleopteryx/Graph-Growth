import networkx as nx

import pickle
graph = open('graph.p', 'r')
graph = pickle.load(graph)

degrees = graph.degree()
order =[]
for x in range(len(degrees)):
	for key in degrees.keys():
          if degrees[key] == x:
            order.append(key)

