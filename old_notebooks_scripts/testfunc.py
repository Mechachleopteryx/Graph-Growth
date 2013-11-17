import sys
import scipy
from scipy import io
import community #module I built from networkX stuff. 
from networkx import chordal_alg
import random
import networkx as nx
import numpy as np
import os
import pickle
import csv
import random
from time import time, sleep
from py2neo import neo4j, rel, node
import pandas as pd
import pickle
from oct2py import Oct2Py
from oct2py import octave
import grow
import matplotlib.pylab as plt

sparse = True
directed = True
randomgrowth=False
wholegrowth=False
growthfactor= 3000
num_measurements = 10
verbose = True
connected = True



bnt = Oct2Py()
# graph_db = grow.database()
graph_db = neo4j.GraphDatabaseService()

try:
	nodes = open('nodes.p','r')
	nodes = pickle.load(nodes)
except:
	print 'Your graph is empty. Please loab a graph into the database.'
	1/0
data = []
if graph_db.size < 2:
	print 'Your graph is empty. Please load a graph into the database.'
	1/0
if sparse == True:
    sparsemeasurements = [6,7,8,9,growthfactor]
    measurements = np.logspace(1, (int(len(str(growthfactor))))-1, num_measurements)
    for x in measurements:
        sparsemeasurements.append(int(x))
else:
	sparsemeasurements = range(2,growthfactor)

if directed:
	graph = nx.DiGraph()
else:
	graph = nx.graph()

nodegrowth = graph.size()

edgegrowth = 0
if wholegrowth == True:
    growthfactor = len(nodes)


initial_node = random.choice(nodes.keys()) #randomly get a node to add from dictionary
if verbose:
    print 'Starting from ' + initial_node
while nodegrowth < growthfactor:
        if nodegrowth > 1:
            possiblenodes = graph.nodes() # get all nodes in graph.
            fromnode = random.choice(possiblenodes) #pick random node in graph to grow from.
            if verbose:
                print 'Using ' + str(fromnode) + ' to find new node'
        else: #this is because you can't do random from one node at the start.
            fromnode = initial_node
            if verbose:
                print 'using initial node'
        
        fromnode = nodes[fromnode] #get DB version of the node.
        #get all relatinpships in graph DB for that node
        new_node_rels = list(graph_db.match(end_node = fromnode, bidirectional=True))
        new_rel = random.choice(new_node_rels)
        
        # is the new node a part or child of the node we are growing from?
        if new_rel.end_node == fromnode:
            new_node = new_rel.start_node
        if new_rel.start_node == fromnode:
            new_node = new_rel.end_node
        assert new_node != fromnode 


        rels = list(graph_db.match(start_node=new_node)) #query graph for edges from that node
        for edge in rels:
            newnodename = edge.start_node.get_properties()
            newnodename = newnodename.get('name')
            newnodename = newnodename.encode()
            endnodename = edge.end_node.get_properties()
            endnodename = endnodename.get('name')
            endnodename = endnodename.encode()
            if newnodename not in graph: #check to see if new node is in graph
                graph.add_node(newnodename) # add if not
                if verbose:
                    print 'added ' + str(newnodename)
            if endnodename in graph: #check to see if end node is in graph
                graph.add_edge(newnodename, endnodename) #add it if it is
                if verbose:
                    print 'connected ' + newnodename +' to '+ endnodename
        
        rels = list(graph_db.match(end_node=new_node)) #query graph for edges to that node
        for edge in rels:
            newnodename = edge.end_node.get_properties()
            newnodename = newnodename.get('name')
            newnodename = newnodename.encode()
            startnodename = edge.start_node.get_properties()
            startnodename = startnodename.get('name')
            startnodename = startnodename.encode()
            if newnodename not in graph: #check to see if new node is in graph
                graph.add_node(newnodename) # add if not
                if verbose:
                    print 'added ' + str(newnodename)
            if startnodename in graph: #check to see if end node is in graph
                graph.add_edge(startnodename, newnodename) #add it if it is
                if verbose:
                    print 'connected ' + startnodename +' to '+ newnodename
        nodegrowth = len(graph.nodes())
        if verbose:
        	print 'Graph has ' + str(nodegrowth) + ' nodes.'
        edgegrowth = len(graph.edges())
        if verbose:
        	print 'Graph has ' + str(edgegrowth) + ' edges.'

        if nodegrowth in sparsemeasurements: 
			start_time = time()
			try:
				modgraph = nx.Graph(graph) #make it into a networkx graph
				partition = community.best_partition(modgraph) #find the partition with maximal modularity
				modularity = community.modularity(partition,modgraph) #calculate modularity with that partition
			except:
				modularity = 0.0 
			moral = nx.to_numpy_matrix(graph)
			moralized, moral_edges = octave.moralize(moral)
			# ismoral = False
			# while ismoral == False: #sometimes oct2py takes too long to return I think
			#     try:
			#         moralized, moral_edges = octave.moralize(moral)
			#         ismoral = True
			#     except:
			#         ismoral = False
			#         print 'BNT Error'
			#         1/0
			order = range(len(moralized)+1)
			order = order[1:]
			triangulated, cliques, fill_ins = octave.triangulate(moralized,order)
			# istriangulated = False
			# while istriangulated == False: #sometimes oct2py takes too long to return I think
			#     try:
			#         triangulated, cliques, fill_ins = octave.triangulate(moralized,order)
			#         istriangulated = True
			#     except:
			#         istriangulated = False
			#         print 'BNT Error'
			#         1/0
			triangulated2 = nx.from_numpy_matrix(triangulated)
			nxcliques = nx.find_cliques(triangulated2)
			cliquesizes = []
			for x in cliques:
			    size = len(x)
			    cliquesizes.append(size)
			maxclique = max(cliquesizes)
			avgclique = np.mean(cliquesizes)
			end_time = time()
			run_time = end_time - start_time
			data.append([nodegrowth, len(graph.edges()), modularity, maxclique,avgclique,run_time])
			sparsemeasurements.remove(nodegrowth) #so we don't calculate clique size more than once!
			if verbose:
			    print 'took ' + str(run_time) + ' to run last computation'
			print 'Growing graph with ' + str(nodegrowth) + ' nodes, ' + 'max clique of ' + str(maxclique) + ', ' + str(len(graph.edges())) + ' edges.'
			df = pd.DataFrame(data, columns= ('nodegrowth','edgegrowth', 'modularity','maxclique','avgclique','run_time'))
			plt.close()
			x1 = df['maxclique']
			x2 = df['modularity']
			y = df['nodegrowth']
			fig = plt.figure(figsize=(24,16))
			ax = fig.add_subplot(1,1,1)
			ax2 = ax.twinx()
			line1, = ax.plot( y, x1, label = 'Largest Clique')
			line3, = ax2.plot(y, x2, label = 'Modularity', color = 'red')
			ax.set_xlabel('Nodes in Graph',fontsize=20)
			ax.set_ylabel('Clique Size',fontsize=20)
			ax2.set_ylabel('Modularity', fontsize=20)
			plt.suptitle('Graph Growth', fontsize=30)
			plt.legend((line1,line3),('Largest Clique', 'Modularity'), loc='upper center', frameon=False, fontsize=20)
			plt.show()







