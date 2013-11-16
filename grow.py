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




def get_nodename(node):
    node = node.get_properties()
    node = node.get('name')
    node = node.encode()
    return str(node)


def database():
	try:
		os.system('neo4j stop')
	except:
		pass
	os.system('neo4j start-no-wait')
	sleep(5)
	graph_db = neo4j.GraphDatabaseService()
	return graph_db


def load(csvfile,verbose = True):	
	graph_db = database()
	if verbose:
		print 'started new graph database'
	# get the graph database server going.
	
	#if you want to delete the database!
	# cd /usr/local/Cellar/neo4j/1.9.4/libexec/data
	# os.command(rm -R graph_db)

	# this will store in usr/local/Cellar/neo4j/community-1.9.2-unix/libexec/data
	#make sure graph DB initialized 
	print 'Graph Version: ' + str(graph_db.neo4j_version)
	csvfile = open(csvfile)
	reader = csv.reader(csvfile,delimiter=',')
	nodes = {} # keep track of nodes already in graph_db.
	def get_or_create_node(graph_db, name):
	    if name not in nodes:
	        nodes[name], = graph_db.create(node(name=name)) #make the node if it doesn't exist 
	    return nodes[name] #return the node
	print 'Loading graph into database...'
	for row in reader:
	    parent = get_or_create_node(graph_db, row[0])
	    child = get_or_create_node(graph_db, row[1])
	    parent_child, = graph_db.create(rel(parent, "--", child)) 
	print 'Loaded graph into database'
	pickle.dump(nodes, open("nodes.p", "wb" ) )


def growgraph(sparse = True, Directed = True, randomgrowth=False, wholegrowth=False,growthfactor=100, num_measurements = 10, verbose = True,connected = True):
	bnt = Oct2Py()
	graph_db = database()
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
		sparsemeasurements = range(4,growthfactor)

	if Directed:
		graph = nx.DiGraph()
	else:
		graph = nx.graph()

	nodegrowth = 0
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
	        newnode = new_node #different than above because it's already in graph db format
	        rels = list(graph_db.match(start_node=newnode)) #query graph for edges to and from that node
	        for edge in rels:
	            newnodename = edge.start_node.get_properties()
	            newnodename = newnodename.get('name')
	            newnodename = newnodename.encode()
	            endnodename = edge.end_node.get_properties()
	            endnodename = endnodename.get('name')
	            endnodename = endnodename.encode()
	            if newnodename not in graph: #check to see if new node is in graph
	                graph.add_node(newnodename) # add if not
	                nodegrowth = nodegrowth + 1
	                if verbose:
	                    print 'added ' + str(newnodename)
	            if endnodename in graph: #check to see if end node is in graph
	                graph.add_edge(newnodename, endnodename) #add it if it is
	                if verbose:
	                    print 'connected ' + newnodename +' to '+ endnodename
	        
	        rels = list(graph_db.match(end_node=newnode)) #query graph for edges to and from that node
	        for edge in rels:
	            newnodename = edge.end_node.get_properties()
	            newnodename = newnodename.get('name')
	            newnodename = newnodename.encode()
	            startnodename = edge.start_node.get_properties()
	            startnodename = startnodename.get('name')
	            startnodename = startnodename.encode()
	            if newnodename not in graph: #check to see if new node is in graph
	                graph.add_node(newnodename) # add if not
	                nodegrowth = nodegrowth + 1
	                if verbose:
	                    print 'added ' + str(newnodename)
	            if startnodename in graph: #check to see if end node is in graph
	                graph.add_edge(startnodename, newnodename) #add it if it is
	                if verbose:
	                    print 'connected ' + startnodename +' to '+ newnodename
	        if nodegrowth in sparsemeasurements: 
				start_time = time()
				modgraph = nx.Graph(graph) #make it into a networkx graph
				partition = community.best_partition(modgraph) #find the partition with maximal modularity
				modularity = community.modularity(partition,modgraph) #calculate modularity with that partition 
				moral = nx.to_numpy_matrix(graph)
				ismoral = False
				while ismoral == False: #sometimes oct2py takes too long to return I think
				    try:
				        moral = bnt.moralize(moral)
				        ismoral = True
				    except:
				        ismoral = False
				        print 'BNT Error'
				order = range(len(moral)+1)
				order = order[1:]
				istriangulated = False
				while istriangulated == False: #sometimes oct2py takes too long to return I think
				    try:
				        triangulated = bnt.triangulate(moral,order)
				        istriangulated = True
				    except:
				        istriangulated = False
				        print 'BNT Error'
				triangulated2 = nx.from_numpy_matrix(triangulated)
				cliques = nx.find_cliques(triangulated2)
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
	df = pd.DataFrame(data, columns= ('nodegrowth','edgegrowth', 'modularity','maxclique','avgclique','run_time'))
	return(df)

def plot(x=maxclique,y=edgegrowth,x2=modularity):
	x1 = df[x]
	x2 = df['modularity']
	y = df[y]
	fig = plt.figure(figsize=(24,16))
	ax = fig.add_subplot(1,1,1)
	ax2 = ax.twinx()
	line1, = ax.plot( y, x1, label = 'Random Largest Clique')
	# line2, = ax.plot(y, x2, label = 'Computation Time')
	line3, = ax2.plot(y, x3, label = 'Random Modularity', color = 'red')
	# line4, = ax2.plot(y2, x4, label = 'Real Modularity', color ='purple')
	ax.set_xlabel('Nodes in Graph',fontsize=20)
	ax.set_ylabel('Clique Size',fontsize=20)
	ax2.set_ylabel('Modularity', fontsize=20)
	plt.suptitle('Random Graph Growth', fontsize=30)
	plt.legend((line1,line3),('Largest Clique', 'Modularity'), loc='upper center', frameon=False, fontsize=20)
	plt.show()











