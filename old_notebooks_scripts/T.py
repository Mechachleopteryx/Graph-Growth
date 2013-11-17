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
force_connected = True
plot = False
draw = True
drawgraph = 'moral'
plotx = 'nodegrowth'
ploty = 'maxclique'
ploty2 = 'modularity'

# initialize database 
graph_db = neo4j.GraphDatabaseService()

#get the pickled dictionary of nodes and node names that is made while the csv file is loaded.
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
#make a list of all the nodes in the database to randomly choose from, but only if force connected graph option is false. 
if force_connected == False:
	possiblenodes = nodes
	print 'Graph will not be fully connected, use "force_connected = True" if you want it to be fully connected'

# here we figure out at what points to measure if the user wants a spare measumement or to measure every time a node is added. This speeds up big graph growths a lot! 
if sparse == True:
    sparsemeasurements = [6,7,8,9,growthfactor]
    measurements = np.logspace(1, (int(len(str(growthfactor))))-1, num_measurements)
    for x in measurements:
        sparsemeasurements.append(int(x))
else:
	sparsemeasurements = range(2,growthfactor)


# this will actually only work for directed graph because we are moralizing, but I want to leave the option for later. Perhaps I can just skip moralization for undirected graph.
if directed:
	graph = nx.DiGraph()
else:
	graph = nx.graph()


# this will grow the whole graph. Takes a while for big ones! 
if wholegrowth == True:
    growthfactor = len(nodes)

# pick an initial node to start from
initial_node = random.choice(nodes.keys()) #randomly get a node to add from dictionary
if verbose:
    print 'Starting from ' + initial_node
used = 0
#measure the nodegrowth 
nodegrowth = graph.size()
while nodegrowth < growthfactor: # make sure we aren't above how many nodes we want to measure in the graph    
	if force_connected == True:
		if nodegrowth > 1:
			possiblenodes = graph.nodes() # get all nodes in graph.
			fromnode = random.choice(possiblenodes) #pick random node in graph to grow from.
			if verbose:
			    print 'Using ' + str(fromnode) + ' to find new node'
		else: #this is because you can't do random from one node at the start.
		    fromnode = initial_node
		    if verbose:
		        print 'using initial node'
		        used = used+1
		        if used > 5:
		        	1/0

		fromnode = nodes[fromnode] #get DB version of the node.
		#get all relationpships in graph DB for that node
		new_node_rels = list(graph_db.match(end_node = fromnode, bidirectional=True))
		new_rel = random.choice(new_node_rels)

		# is the new node a parentt or child of the node we are growing from?
		if new_rel.end_node == fromnode:
		    new_node = new_rel.start_node
		if new_rel.start_node == fromnode:
		    new_node = new_rel.end_node
		assert new_node != fromnode
	
	if force_connected == False:
		new_node = random.choice(possiblenodes.values())
		
	print 'adding' + str(new_node)
    # go through the list of edges that have the new node as a part of it, and only add the edge if they are between the new node and a node in the graph already.
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
			ismoral = False
			tries = 0
			while ismoral == False and tries < 5: #sometimes oct2py takes too long to return I think
			    try:
			        moralized, moral_edges = octave.moralize(moral)
			        ismoral = True
			    except:
			        ismoral = False
			        print 'Octave Error, trying again!'
			        tries = tries + 1
			order = range(len(moralized)+1)
			order = order[1:]
			triangulated, cliques, fill_ins = octave.triangulate(moralized,order)
			istriangulated = False
			tries = 0
			while istriangulated == False and tries < 5: #sometimes oct2py takes too long to return I think
			    try:
			        triangulated, cliques, fill_ins = octave.triangulate(moralized,order)
			        istriangulated = True
			        tries = 5
			    except:
			        istriangulated = False
			        print 'Octave Error, trying again!'
			        tries = tries + 1 
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
			print 'Growing graph with ' + str(nodegrowth) + ' nodes, ' + str(modularity) + ' modularity, max clique of ' + str(maxclique) + ', ' + str(len(graph.edges())) + ' edges.'
			if plot == True:
				df = pd.DataFrame(data, columns= ('nodegrowth','edgegrowth', 'modularity','maxclique','avgclique','run_time'))
				plt.close()
				fig = plt.figure(figsize=(24,16))
				ax = fig.add_subplot(1,1,1)
				ax2 = ax.twinx()
				y1 = df[ploty]
				y2 = df[ploty2]
				x = df[plotx]
				ax.set_xlabel('%s in Graph' %(plotx),fontsize=20)
				line1, = ax.plot(x, y1, label = ploty)
				line2, = ax2.plot(x, y2, label = ploty2, color = 'red')
				ax.set_ylabel(ploty,fontsize=20)
				ax2.set_ylabel(ploty2, fontsize=20)
				plt.suptitle('Graph Growth', fontsize=30)
				plt.legend((line1,line2),(ploty , ploty2), loc='upper center', frameon=False, fontsize=20)
				plt.show()
			if draw == True:
				if drawgraph == 'triangulated':
					G = nx.from_numpy_matrix(triangulated)
				elif drawgraph == 'moral':
					G = nx.from_numpy_matrix(moralized)
				elif drawgraph == 'directed':
					G = graph()
			# position is stored as node attribute data for random_geometric_graph
				plt.close()
				pos = nx.random_layout(G)
				# find node near center (0.5,0.5)
				dmin=1
				ncenter=0
				for n in pos:
				    x,y=pos[n]
				    d=(x-0.5)**2+(y-0.5)**2
				    if d<dmin:
				        ncenter=n
				        dmin=d

				# color by path length from node near center
				p=nx.single_source_shortest_path_length(G,ncenter)

				plt.figure(figsize=(15,15))
				nx.draw_networkx_edges(G,pos,nodelist=[ncenter],alpha=0.2)
				nx.draw_networkx_nodes(G,pos,nodelist=p.keys(),
				                       node_size=20,
				                       node_color=p.values(),
				                       cmap=plt.cm.Reds_r)

				plt.xlim(-0.05,1.05)
				plt.ylim(-0.05,1.05)
				plt.axis('off')
				plt.show()
df = pd.DataFrame(data, columns= ('nodegrowth','edgegrowth', 'modularity','maxclique','avgclique','run_time'))













