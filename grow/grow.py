import sys
import scipy
from scipy import io
from networkx import chordal_alg
import random
import networkx as nx
import numpy as np
import os
import pickle
import csv
import random as Random
from time import time, sleep
from py2neo import neo4j, rel, node
import pandas as pd
import pickle
from oct2py import Oct2Py
from oct2py import octave
import matplotlib.pylab as plt
 

#this does the whole shebang!
def grow(csvfile, reverserandom=False, outgoingrandom = True, incomingrandom = False, totalrandom = False,getgraph = True, drawspectral = True, force_connected = True, usenx= True, sparse = True, plot = False, directed = True, wholegrowth=False,growthfactor=100, num_measurements = 10, verbose = True, plotx = 'nodegrowth', ploty = 'maxclique', ploty2 = 'modval',drawgraph = 'triangulated', draw= True):
	"""
	This function will load your graph and grow it. 
	It takes in the same parameters as load_graph and grow_graph, and does it all at once.

	Returns:

	If you pass it the option to grow a random graph, it returns the graph, the random graph, and the data
	If you pass it no random options, it returns the graph and the data.
	
	"""
	load_graph(csvfile = csvfile)
	if reverserandom or outgoingrandom or incomingrandom or totalrandom == True:
		graph, randomgraph, data = grow_graph(reverserandom=reverserandom, outgoingrandom = outgoingrandom, incomingrandom = incomingrandom, totalrandom = totalrandom, usenx= usenx, getgraph = getgraph, drawspectral = drawspectral, force_connected = force_connected, sparse = sparse, plot = plot, directed = directed, wholegrowth=wholegrowth,growthfactor=growthfactor, num_measurements = num_measurements, verbose = verbose, plotx = plotx, ploty = ploty, ploty2 = ploty2, drawgraph = drawgraph, draw= draw)
		return graph, randomgraph, data
	else: 
		graph, data = grow_graph(reverserandom=reverserandom, outgoingrandom = outgoingrandom, incomingrandom = incomingrandom, totalrandom = totalrandom, usenx= usenx, getgraph = getgraph, drawspectral = drawspectral, force_connected = force_connected, sparse = sparse, plot = plot, directed = directed, wholegrowth=wholegrowth,growthfactor=growthfactor, num_measurements = num_measurements, verbose = verbose, plotx = plotx, ploty = ploty, ploty2 = ploty2, drawgraph = drawgraph, draw= draw)
		return graph, data

def get_nodename(node):
    node = node.get_properties()
    node = node.get('name')
    node = node.encode()
    return str(node)

#initializes database
def database():
	"""
	Initializes the database where the graph is stored

	The User should not use this, it is only referenced in other functions
	"""

	tries = 0
	connected = False
	while connected == False and tries < 5:
		try:
			try:
				os.system('neo4j stop')
			except:
				pass
			os.system('neo4j start-no-wait')
			sleep(5)
			graph_db = neo4j.GraphDatabaseService()
			return graph_db
			connected = True
		except:
			print 'Trouble connecting, trying again!'
			connected = False
			tries = tries + 1


#loads in the csv file into the database.
def load_graph(csvfile):	
	"""
	Load your graph into the database. This function allows you to load any graph
	into memory and then you can use the grow_graph function to grow and measure it.
	You must load a graph in this way to use the grow_graph function.

	Simply pass in your CSV file. It assumes the 0 column is the parent node, and 1
	is the child node. Each line is an edge.

	It will save a pickled file in the nodes it added to the database for later use.
	This means that you need to be running this function and the graph_grow function
	from the same directory.

	If you want to delete the database,
	$ cd /usr/local/Cellar/neo4j/1.9.4/libexec/data
	$ os.command(rm -R graph_db)

	Parameters:

	csvfile: load in your csvfile that is the edges in your graph.

	"""

	# get the graph database server going.
	graph_db = database()
	print 'started new graph database'

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

#this does all the growth and measurement stuff.
def grow_graph(reverserandom = False, outgoingrandom = False, incomingrandom = False, totalrandom = False, usenx= True, force_connected = True, sparse = True, plot = False, directed = True, wholegrowth=False,growthfactor=100, num_measurements = 100, verbose = True, plotx = 'nodegrowth', ploty = 'maxclique', ploty2 = 'modval',drawgraph = 'triangulated', draw= True, drawspectral = True, getgraph = True):
	"""
	This function takes a graph that was loaded using load_graph and grows it,
	meauring modularity and clique size. Modularity is found via a partition using 
	the Louvain algorithm--Blondel, V.D. et al. Fast unfolding of communities in large networks. J. Stat. Mech 10008, 1-12(2008)--
	and the Modularity value is Newman's Q--Newman, M.E.J. & Girvan, M. Finding and evaluating community structure in networks. Physical Review E 69, 26113(2004).

	Parameters:
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


	Returns:

	the grown graph, the random growth graph(only if one is grown), dataframe of measurements

	"""
	Errors = 0
	try:# I do this so if the computation is taking a long time you can exit out but save all the previous data that was being collected; the except is way at the bottom! 
		random = False #set as false, gets made to truth later if the user passes a type of random graph they want

		#make sure user does not want to draw and plot at the same time. 
		if plot == True:
			draw = False
		if draw == True:
			plot = False
		#you cannot plot and draw at the same time

		# initialize database 
		graph_db = database()

		#get the pickled dictionary of nodes and node names (for the database) that is made while the csv file is loaded.
		try:
			nodes = open('nodes.p','r')
			nodes = pickle.load(nodes)
		except:
			print 'Your graph is empty. Please load a graph into the database.'
			1/0
		data = []
		if graph_db.size < 2:
			print 'Your graph is empty. Please load a graph into the database.'
			1/0
		# this will grow the whole graph. Takes a while for big ones! 
		if wholegrowth == True:
		    growthfactor = len(nodes)

		#make a list of all the nodes in the database to randomly choose from, but only if force connected graph option is false. 
		if force_connected == False:
			possiblenodes = nodes
			print 'Graph will not be fully connected, use "force_connected = True" if you want it to be fully connected'

		# here we figure out at what points to measure if the user wants a spare measumement or to measure every time a node is added. This speeds up big graph growths a lot! 
		if sparse == True:
		    sparsemeasurements = [growthfactor]
		    measurements = np.logspace(1, (int(len(str(growthfactor)))), num=num_measurements)
		    for x in measurements:
		        sparsemeasurements.append(int(x))
			for x in sparsemeasurements:
				if x > (growthfactor+1):
					sparsemeasurements.remove(x) #logspace is hard to build on the fly, so sometimes it has values over the growthfactor, so we remove them.

		else:
			sparsemeasurements = range(10,growthfactor)
		print 'Measuring graph at: ' + str(sparsemeasurements) 
		# this will actually only work for directed graph because we are moralizing, but I want to leave the option for later. Perhaps I can just skip moralization for undirected graphs.
		if directed:
			graph = nx.DiGraph()
		else:
			graph = nx.graph()

		# pick an initial node to start growing the graph from
		initial_node = np.random.choice(nodes.keys()) #randomly get a node to add from dictionary
		if verbose:
		    print 'Starting from ' + initial_node
		initial_used = 0 #keep track of how many times the initial node was used
		nodegrowth = graph.number_of_nodes()
		edgegrowth = graph.number_of_edges()
		
		nodes_in_graph = [] #this keeps track of nodes added to graph so we don't add one more than once(even though it doesn't mess things up, it slows things down to add nodes that already exist in graph)
		
		while nodegrowth < growthfactor: # make sure we aren't above how many nodes we want to measure in the graph    
			#start off finding a node to add to the graph.
			if force_connected == True: #this means that we must search for a new new based on finding an edge from a node in the graph to a node that is not in the graph yet.
				try:
					possiblenodes = graph.nodes() # get all nodes in graph.
					fromnode = Random.choice(possiblenodes) #pick random node in graph to grow from(add one of its nieghbors). This uses the random module, not np.random
					if verbose:
					    print 'Using ' + str(fromnode) + ' to find new node'
				except: #this is because you can't do random from one node at the start.
				    fromnode = initial_node
				    graph.add_node(fromnode)
				    if verbose:
				        print 'using initial node'
				        initial_used = initial_used+1
				        if initial_used > 5:
				        	1/0

				fromnode = nodes[fromnode] #get DB version of the node.
				#get all relationships in graph DB for that node so we can pick 
				tries = 0
				while tries < 5:
					try:
						new_node_rels = list(graph_db.match(end_node = fromnode, bidirectional=True))
						tries = 5
					except:
						tries = tries + 1 
				new_rel = Random.choice(new_node_rels) #randomly pick one of them, thus picking a node to add to graph. This uses the random module, not np.random

				# is the new node a parent or child of the node we are growing from?
				if new_rel.end_node == fromnode:
				    new_node = new_rel.start_node
				if new_rel.start_node == fromnode:
				    new_node = new_rel.end_node
			
			if force_connected == False: # if not connected, we can just pick from the pickled dictionary of nodes in the database
				new_node = np.random.choice(possiblenodes.values())
			
			if new_node not in nodes_in_graph: #check to see if the node it found is already in graph already. Add it if it is not in there.
				#add the nodes to the graph, connecting it to nodes in the graph that it is connected to.
			    # go through the list of edges that have the new node as a part of it, and only add the edge if they are between the new node and a node in the graph already.
				tries = 0
				while tries < 5:
					try:
						rels = list(graph_db.match(start_node=new_node)) #query graph for edges from that node
						tries = 5
					except:
						tries = tries + 1 
				for edge in rels:
					#get the string name of the node
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
				tries = 0
				while tries < 5:
					try:
						rels = list(graph_db.match(end_node=new_node)) #query graph for edges to that node
						tries = 5
					except:
						tries = tries + 1
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
						#measure the nodegrowth and edge growth
				nodegrowth = len(graph.nodes())
				edgegrowth = len(graph.edges())
				if verbose:
					print 'Graph has ' + str(nodegrowth) + ' nodes.'
				if verbose:
				    print 'Graph has ' + str(edgegrowth) + ' edges.'

					
			#here is where we measure everything about the graph 
			if nodegrowth in sparsemeasurements: #won't work for graphs smaller than 3.
				#here I make a few random graphs to compare the growth of the real graph. They are all the same size and same edges, but different controls.
				# Reverse the direction of the edges. The in-degree distribution in this graph is power-law, but the out-degree is exponential tailed. So this is just a check that degree distribution is irrelevant.
				if reverserandom == True: 
					random_graph =  graph.reverse()
					random = True
				# Keep the number of outgoing links for each node the same, but randomly allocating their destinations. This should break modularity, put preserves out-degree.
				if outgoingrandom == True:
					random_graph = graph.copy()
					for edge in random_graph.edges():
						parent = edge[0]
						child = edge[1]
						random_graph.remove_edge(parent,child)
						newchild = parent
						while newchild == parent: #so that we don't get a self loop.
							newchild = np.random.choice(graph.nodes())
						random_graph.add_edge(parent,newchild)
						random = True
				# Same thing, but this time fixing the number of incoming links and randomly allocating their origins. Likewise, but preserves in-degree.
				if incomingrandom ==True:
					random_graph = graph.copy()
					for edge in random_graph.edges():
						parent = edge[0]
						child = edge[1]
						random_graph.remove_edge(parent,child)
						newparent = child
						while newparent == child:
							newparent = np.random.choice(graph.nodes())
						random_graph.add_edge(newparent,child)
						random = True
				#gives a graph picked randomly out of the set of all graphs with n nodes and m edges. This preserves overall degree, and number of nodes/edges, but is completeley random to outdegree/indegree. 
				if totalrandom == True:
					numrandomedges = graph.number_of_edges()
					numrandomnodes = graph.number_of_nodes()
					random_graph = nx.dense_gnm_random_graph(numrandomnodes, numrandomedges)
					random_graph = random_graph.to_directed()
					random = True

				start_time = time()
				# if nodegrowth > 5: #poin
				# 	#calculate modularity
				modgraph = nx.Graph(graph) #make it into a undirected networkx graph. This measures moduilarity on undirected version of graph! 
				partition = best_partition(modgraph) #find the partition with maximal modularity
				modval = modularity(partition,modgraph) #calculate modularity with that partition
				sleep(2)
				if random == True:
					random_modgraph = random_graph.to_undirected() #make it into a undirected networkx graph. This measures moduilarity on undirected version of graph! 
					random_partition = best_partition(random_modgraph) #find the partition with maximal modularity
					random_modval = modularity(random_partition,random_modgraph) #calculate modularity with that partition
				#option to use python nx to moralize and triangulate
				if usenx == True:
					moralized = moral_graph(graph)
					if random == True:
						random_moralized = moral_graph(random_graph)
				
				else: #use Octave to run Matlab Bayes Net Toolbox, NOT SET UP FOR RANDOM GRAPHS YET.
					moralized = nx.to_numpy_matrix(graph) # make nx graph into a simple matrix
					ismoral = False
					tries = 0
					while ismoral == False and tries < 5: #sometimes oct2py takes too long to return I think
					    try:
					        moralized, moral_edges = octave.moralize(moralized)
					        ismoral = True
					    except:
					        ismoral = False
					        print 'Octave Error, trying again!'
					        tries = tries + 1
				
				#the triangulation works better if you pass it an order of the nodes based on minimal degree. 
				#netowk x can make the matrix in any node order, so I made the matrix in order of minimal degree
				#then, below I just use an order of 1 to the length of the matrix, which is fine because the matrix is already in the right order for triangulation
				# I use this in both the random and real graphs to make the matrixes to pass to MATLAB functions
				degrees = graph.degree()
				order =[]
				for x in range(len(degrees)):
					for key in degrees.keys():
				          if degrees[key] == x:
				            order.append(key)

				triorder = range(len(moralized)+1) # BNT needs order of nodes to triangulate
				triorder = triorder[1:]
				
				if random == True:
					random_order = range(len(random_moralized)+1) # BNT needs order of nodes to triangulate
					random_order = random_order[1:] # I think you have to shift the space because you are going from 0 index to 1 idndex
				
				istriangulated = False
				tries = 0
				while istriangulated == False and tries < 5: #sometimes oct2py takes too long to return I think
					try:
					    moralized = nx.to_numpy_matrix(moralized,order)  # have to make it into matrix.
					    triangulated, cliques, fill_ins = octave.triangulate(moralized,triorder)
					    if random == True:
					    	random_moralized = nx.to_numpy_matrix(random_moralized,order) # have to make it into matrix.
					    	random_triangulated, random_cliques, random_fill_ins = octave.triangulate(random_moralized, triorder)
					    istriangulated = True
					    tries = 5
					except:
					    istriangulated = False
					    print 'Octave Error, trying again!'
					    tries = tries + 1 
				#loop through cliques and get the size of them
				cliquesizes = [] #empty array to keep clique sizes in
				for x in cliques:
				    size = len(x)
				    cliquesizes.append(size)
				maxclique = max(cliquesizes) #get the biggest clique
				avgclique = np.mean(cliquesizes) # get the mean of the clique sizes

				#do the same for random graph cliques
				if random == True:
					random_cliquesizes = [] #empty array to keep clique sizes in
					#loop through cliques and get the size of them
					for x in random_cliques:
						size = len(x)
						random_cliquesizes.append(size)
					random_maxclique = max(random_cliquesizes) #get the biggest clique
					random_avgclique = np.mean(random_cliquesizes) # get the mean of the clique sizes
			
				end_time = time() #get end time 
				run_time = end_time - start_time #time how long all the took
				
				#store the data! 

				if random == True:
					data.append([nodegrowth, edgegrowth, modval, random_modval, maxclique, random_maxclique, avgclique, random_avgclique, run_time]) #store results

				if random == False:
					data.append([nodegrowth, edgegrowth, modval, maxclique,avgclique,run_time]) #store results
				
				sparsemeasurements.remove(nodegrowth) #so we don't calculate clique size more than once!
				if verbose:
				    print 'took ' + str(run_time) + ' to run last computation'
				
				#this will always print, basic status update everytime clique size is measured.
				if random == True:
					print str(nodegrowth) + ' nodes, ', str(edgegrowth) + ' edges; ' + 'Modularity: ' + str(modval) + ', Random Modularity: ' +str(random_modval) + ', Largest Clique: ' + str(maxclique) + ', Largest Random Clique: ' + str(random_maxclique)
				if random == False:
					print str(nodegrowth) + ' nodes, ', str(edgegrowth) + ' edges; ' + 'Modularity: ' + str(modval) + ', Largest Clique: ' + str(maxclique)
				

				#this will redraw the plot everytime a computation is done.
				if plot == True:
					if random == False:
						df = pd.DataFrame(data, columns= ('nodegrowth','edgegrowth', 'modularity','maxclique','avgclique','run_time'))
						plt.close()
						plt.ion()
						fig = plt.figure(figsize=(24,16))
						ax = fig.add_subplot(1,1,1)
						ax2 = ax.twinx()
						y1 = df[ploty] #user input, default to clique size
						y2 = df[ploty2] #user input, default to modularity
						x = df[plotx] #user input, default to nodes in graph.
						ax.set_xlabel('%s in Graph' %(plotx),fontsize=20)
						line1, = ax.plot(x, y1, label = ploty)
						line2, = ax2.plot(x, y2, label = ploty2, color = 'red')
						ax.set_ylabel(ploty,fontsize=20)
						ax2.set_ylabel(ploty2, fontsize=20)
						plt.suptitle('Graph Growth', fontsize=30)
						plt.legend((line1,line2),(ploty , ploty2), loc='upper center', frameon=False, fontsize=20)
						plt.show()
						plt.draw()

					if random == True:
						df = pd.DataFrame(data, columns= ('nodegrowth', 'edgegrowth', 'modval','random_modval', 'maxclique', 'random_maxclique', 'avgclique', 'random_avgclique', 'run_time'))
						plt.close()
						plt.ion()
						fig = plt.figure(figsize=(18,10))
						ax = fig.add_subplot(1,1,1)
						ax2 = ax.twinx()
						ticks = [0,.1,.2,.3,.4,.5,.6,.7,.8,.9,1]
						ax2.set_yticks(ticks)
						y1 = df[ploty]
						y2 = df[ploty2]
						y3def = str('random_'+ploty) # i just add random to whatever the user inputs as the y stuff they want to plot
						y3 = df[y3def]
						y4def = str('random_'+ploty2)
						y4 = df[y4def]
						x = df[plotx]
						ax.set_xlabel('%s in Graph' %(plotx),fontsize=20)
						line1, = ax.plot(x, y1, label = ploty, color = 'blue')
						line2, = ax2.plot(x, y2, label = ploty2, color = 'green')
						line3, = ax.plot(x,y3, label = y3def, color = 'red')
						line4, = ax2.plot(x,y4, label = y4def, color = 'cyan')
						ax.set_ylabel(ploty,fontsize=20)
						ax2.set_ylabel(ploty2, fontsize=20)
						plt.suptitle('Graph Growth', fontsize=30)
						plt.legend((line1,line2,line3,line4), (ploty,ploty2,y3def,y4def),loc='upper center', frameon=False, fontsize=20)#
						plt.show()
						plt.draw()
				#draw the graph 
				if draw == True:
					if drawgraph == 'triangulated':
						G = nx.from_numpy_matrix(triangulated)
					elif drawgraph == 'moralized':
						G = nx.from_numpy_matrix(moralized)
					elif drawgraph == 'directed':
						G = graph
					plt.close()
					
					if drawspectral == True:
						nx.draw_random(G, prog='neato')
					else:
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
						plt.suptitle(drawgraph + ' graph')
						nx.draw_networkx_edges(G,pos,nodelist=[ncenter],alpha=0.2)
						nx.draw_networkx_nodes(G,pos,nodelist=p.keys(),
						                       node_size=20,
						                       node_color=p.values(),
						                       cmap=plt.cm.Reds_r)

						plt.xlim(-0.05,1.05)
						plt.ylim(-0.05,1.05)
						plt.axis('off')
					plt.show()
		if random == True:
			df = pd.DataFrame(data, columns= ('nodegrowth', 'edgegrowth', 'modval','random_modval', 'maxclique', 'random_maxclique', 'avgclique', 'random_avgclique', 'run_time'))
			return(graph, random_graph, df)
		if random == False:
			df = pd.DataFrame(data, columns= ('nodegrowth','edgegrowth', 'modval','maxclique','avgclique','run_time'))
			return (graph, df)
	# I do this so if the computation is takign a long time you can exit out but save all the previous data that was being collected
	except KeyboardInterrupt:
		if random == True:
			df = pd.DataFrame(data, columns= ('nodegrowth', 'edgegrowth', 'modval','random_modval', 'maxclique', 'random_maxclique', 'avgclique', 'random_avgclique', 'run_time'))
			return(graph, random_graph, df)
		if random == False:
			df = pd.DataFrame(data, columns= ('nodegrowth','edgegrowth', 'modval','maxclique','avgclique','run_time'))
			return (graph, df)

def build(return_partition=True, return_modval = True, return_graph= True, verbose = True):
	"""
	This build the entire graph from the database and returns the partition and modularity value.

	Parameters
	return_partition = True
	return_modval = True
	return_partition = True

	"""
	graph_db = database()
	#get the pickled dictionary of nodes and node names (for the database) that is made while the csv file is loaded.
	try:
		nodes = open('nodes.p','r')
		nodes = pickle.load(nodes)
	except:
		print 'Your graph is empty. Please load a graph into the database.'
		1/0
	graph = nx.DiGraph()
	for node in nodes:
		new_node = node
		new_node = nodes[new_node]
		rels = list(graph_db.match(start_node=new_node)) #query graph for edges from that node
		for edge in rels:
			#get the string name of the node
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
				#measure the nodegrowth and edge growth
		nodegrowth = len(graph.nodes())
		edgegrowth = len(graph.edges())
		if verbose:
			print 'Graph has ' + str(nodegrowth) + ' nodes.'
		if verbose:
		    print 'Graph has ' + str(edgegrowth) + ' edges.'
	modgraph = nx.Graph(graph) #make it into a undirected networkx graph. This measures moduilarity on undirected version of graph! 
	partition = best_partition(modgraph) #find the partition with maximal modularity
	modval = modularity(partition,modgraph) #calculate modularity with that partition
	return graph, partition, modval

#________________________________________________________________________________________________________________________________________________________
# this is the community finding stuff and networkx bayes stuff. I did not write ANY this...


def markov_blanket(G, n):
    """
    Returns the Markov blanket of `n`.

    The Markov blanket consists of the parents of `n`, the children of `n`, and
    any other parents of the children of `n`.

    Parameters
    ----------
    G : DiGraph
        A direct acyclic graph.
    n : node
        A node in `G`.

    Returns
    -------
    blanket : set
        The Markov blanket of `n`.

    Notes
    -----
    The procedure works for any directed graph, but the interpretation of the
    result is valid only when `G` is a DAG.

    """
    blanket = set(G.pred[n])
    children = list(G.succ[n].keys())
    blanket.update(children)
    for child in children:
        blanket.update(G.pred[child])
    return blanket

def moral_graph(G):
    """
    Returns the moral graph of `G`.

    The moral graph is an undirected graph where every node in `G` is connected
    to its Markov blanket.

    Parameters
    ----------
    G : DiGraph
        A direct acyclic graph.

    Returns
    -------
    MG : Graph
        The moral graph of `G`.

    """
    MG = nx.Graph()
    for u in G:
        blanket = markov_blanket(G, u)
        MG.add_edges_from([(u, v) for v in blanket if v != u])
    return MG

def maximum_spanning_tree(G, weight='weight'):
    """
    Return a maximum spanning tree or forest of an undirected, weighted graph.

    Parameters
    ----------
    G : Graph
        An undirected, weighted graph.
    weight : str
        The attribute used as weights.

    Returns
    -------
    T : Graph
       A minimum spanning tree or forest.

    Notes
    -----
    The maximum spanning tree is unique only if every weight is unique.

    See Also
    --------
    nx.minimum_spanning_tree

    """
    # Leave the original graph untouched.
    G = G.copy()

    # Negate all the weights.
    for u, v, data in G.edges_iter(data=True):
        data[weight] = -data.get(weight, 1)

    # Build the minimum spanning tree.
    T = nx.minimum_spanning_tree(G, weight)

    # Un-negate all the weights.
    for u, v, data in T.edges_iter(data=True):
        data[weight] = -data.get(weight, 1)

    return T

### This is networkx.algorithms.clique.make_max_clique_graph but modified
### to include weights according to the intersection of the cliques.
def clique_graph(G, create_using=None, name=None):
    """Create the maximal clique graph of a graph.

    Finds the maximal cliques and treats these as nodes.
    The nodes are connected if they have common members in
    the original graph.  Theory has done a lot with clique
    graphs, but I haven't seen much on maximal clique graphs.

    Notes
    -----
    This should be the same as make_clique_bipartite followed
    by project_up, but it saves all the intermediate steps.
    """
    cliq = list(map(set, nx.find_cliques(G)))
    if create_using:
        B = create_using
        B.clear()
    else:
        B = nx.Graph()
    if name is not None:
        B.name = name

    to_node = lambda cl: tuple(sorted(cl))
    for i, cl in enumerate(cliq):
        u = to_node(cl)
        B.add_node(u)
        for j, other_cl in enumerate(cliq[:i]):
            intersect = cl & other_cl
            if intersect:     # Not empty
                B.add_edge(u, to_node(other_cl), weight=len(intersect))
    return B

def junction_tree(G):
    """Return a junction tree of `G`.

    A junction tree of `G` is a maximal weight spanning tree of the clique
    graph of `G`.  Its width is the size of the largest clique of `G` minus
    one, and is minimal.

    Parameters
    ----------
    G : DiGraph
        A direct acyclic graph.

    Returns
    -------
    J : Graph
        A junction tree.

    """
    CG = clique_graph(G)
    J = maximum_spanning_tree(CG)
    return J


__PASS_MAX = -1
__MIN = 0.0000001

import networkx as nx
import sys
import types
import array


def partition_at_level(dendogram, level) :
    """Return the partition of the nodes at the given level

    A dendogram is a tree and each level is a partition of the graph nodes.
    Level 0 is the first partition, which contains the smallest communities, and the best is len(dendogram) - 1.
    The higher the level is, the bigger are the communities

    Parameters
    ----------
    dendogram : list of dict
       a list of partitions, ie dictionnaries where keys of the i+1 are the values of the i.
    level : int
       the level which belongs to [0..len(dendogram)-1]

    Returns
    -------
    partition : dictionnary
       A dictionary where keys are the nodes and the values are the set it belongs to

    Raises
    ------
    KeyError
       If the dendogram is not well formed or the level is too high

    See Also
    --------
    best_partition which directly combines partition_at_level and generate_dendogram to obtain the partition of highest modularity

    Examples
    --------
    >>> G=nx.erdos_renyi_graph(100, 0.01)
    >>> dendo = generate_dendogram(G)
    >>> for level in range(len(dendo) - 1) :
    >>>     print "partition at level", level, "is", partition_at_level(dendo, level)
    """
    partition = dendogram[0].copy()
    for index in range(1, level + 1) :
        for node, community in partition.iteritems() :
            partition[node] = dendogram[index][community]
    return partition


def modularity(partition, graph) :
    """Compute the modularity of a partition of a graph

    Parameters
    ----------
    partition : dict
       the partition of the nodes, i.e a dictionary where keys are their nodes and values the communities
    graph : networkx.Graph
       the networkx graph which is decomposed

    Returns
    -------
    modularity : float
       The modularity

    Raises
    ------
    KeyError
       If the partition is not a partition of all graph nodes
    ValueError
        If the graph has no link
    TypeError
        If graph is not a networkx.Graph

    References
    ----------
    .. 1. Newman, M.E.J. & Girvan, M. Finding and evaluating community structure in networks. Physical Review E 69, 26113(2004).

    Examples
    --------
    >>> G=nx.erdos_renyi_graph(100, 0.01)
    >>> part = best_partition(G)
    >>> modularity(part, G)
    """
    if type(graph) != nx.Graph :
        raise TypeError("Bad graph type, use only non directed graph")

    inc = dict([])
    deg = dict([])
    links = graph.size(weight='weight')
    if links == 0 :
        raise ValueError("A graph without link has an undefined modularity")

    for node in graph :
        com = partition[node]
        deg[com] = deg.get(com, 0.) + graph.degree(node, weight = 'weight')
        for neighbor, datas in graph[node].iteritems() :
            weight = datas.get("weight", 1)
            if partition[neighbor] == com :
                if neighbor == node :
                    inc[com] = inc.get(com, 0.) + float(weight)
                else :
                    inc[com] = inc.get(com, 0.) + float(weight) / 2.

    res = 0.
    for com in set(partition.values()) :
        res += (inc.get(com, 0.) / links) - (deg.get(com, 0.) / (2.*links))**2
    return res


def best_partition(graph, partition = None) :
    """Compute the partition of the graph nodes which maximises the modularity
    (or try..) using the Louvain heuristices

    This is the partition of highest modularity, i.e. the highest partition of the dendogram
    generated by the Louvain algorithm.

    Parameters
    ----------
    graph : networkx.Graph
       the networkx graph which is decomposed
    partition : dict, optionnal
       the algorithm will start using this partition of the nodes. It's a dictionary where keys are their nodes and values the communities

    Returns
    -------
    partition : dictionnary
       The partition, with communities numbered from 0 to number of communities

    Raises
    ------
    NetworkXError
       If the graph is not Eulerian.

    See Also
    --------
    generate_dendogram to obtain all the decompositions levels

    Notes
    -----
    Uses Louvain algorithm

    References
    ----------
    .. 1. Blondel, V.D. et al. Fast unfolding of communities in large networks. J. Stat. Mech 10008, 1-12(2008).

    Examples
    --------
    >>>  #Basic usage
    >>> G=nx.erdos_renyi_graph(100, 0.01)
    >>> part = best_partition(G)

    >>> #other example to display a graph with its community :
    >>> #better with karate_graph() as defined in networkx examples
    >>> #erdos renyi don't have true community structure
    >>> G = nx.erdos_renyi_graph(30, 0.05)
    >>> #first compute the best partition
    >>> partition = community.best_partition(G)
    >>>  #drawing
    >>> size = float(len(set(partition.values())))
    >>> pos = nx.spring_layout(G)
    >>> count = 0.
    >>> for com in set(partition.values()) :
    >>>     count = count + 1.
    >>>     list_nodes = [nodes for nodes in partition.keys()
    >>>                                 if partition[nodes] == com]
    >>>     nx.draw_networkx_nodes(G, pos, list_nodes, node_size = 20,
                                    node_color = str(count / size))
    >>> nx.draw_networkx_edges(G,pos, alpha=0.5)
    >>> plt.show()
    """
    dendo = generate_dendogram(graph, partition)
    return partition_at_level(dendo, len(dendo) - 1 )


def generate_dendogram(graph, part_init = None) :
    """Find communities in the graph and return the associated dendogram

    A dendogram is a tree and each level is a partition of the graph nodes.  Level 0 is the first partition, which contains the smallest communities, and the best is len(dendogram) - 1. The higher the level is, the bigger are the communities


    Parameters
    ----------
    graph : networkx.Graph
        the networkx graph which will be decomposed
    part_init : dict, optionnal
        the algorithm will start using this partition of the nodes. It's a dictionary where keys are their nodes and values the communities

    Returns
    -------
    dendogram : list of dictionaries
        a list of partitions, ie dictionnaries where keys of the i+1 are the values of the i. and where keys of the first are the nodes of graph

    Raises
    ------
    TypeError
        If the graph is not a networkx.Graph

    See Also
    --------
    best_partition

    Notes
    -----
    Uses Louvain algorithm

    References
    ----------
    .. 1. Blondel, V.D. et al. Fast unfolding of communities in large networks. J. Stat. Mech 10008, 1-12(2008).

    Examples
    --------
    >>> G=nx.erdos_renyi_graph(100, 0.01)
    >>> dendo = generate_dendogram(G)
    >>> for level in range(len(dendo) - 1) :
    >>>     print "partition at level", level, "is", partition_at_level(dendo, level)
    """
    if type(graph) != nx.Graph :
        raise TypeError("Bad graph type, use only non directed graph")

    #special case, when there is no link
    #the best partition is everyone in its community
    if graph.number_of_edges() == 0 :
        part = dict([])
        for node in graph.nodes() :
            part[node] = node
        return part

    current_graph = graph.copy()
    status = Status()
    status.init(current_graph, part_init)
    mod = __modularity(status)
    status_list = list()
    __one_level(current_graph, status)
    new_mod = __modularity(status)
    partition = __renumber(status.node2com)
    status_list.append(partition)
    mod = new_mod
    current_graph = induced_graph(partition, current_graph)
    status.init(current_graph)

    while True :
        __one_level(current_graph, status)
        new_mod = __modularity(status)
        if new_mod - mod < __MIN :
            break
        partition = __renumber(status.node2com)
        status_list.append(partition)
        mod = new_mod
        current_graph = induced_graph(partition, current_graph)
        status.init(current_graph)
    return status_list[:]


def induced_graph(partition, graph) :
    """Produce the graph where nodes are the communities

    there is a link of weight w between communities if the sum of the weights of the links between their elements is w

    Parameters
    ----------
    partition : dict
       a dictionary where keys are graph nodes and  values the part the node belongs to
    graph : networkx.Graph
        the initial graph

    Returns
    -------
    g : networkx.Graph
       a networkx graph where nodes are the parts

    Examples
    --------
    >>> n = 5
    >>> g = nx.complete_graph(2*n)
    >>> part = dict([])
    >>> for node in g.nodes() :
    >>>     part[node] = node % 2
    >>> ind = induced_graph(part, g)
    >>> goal = nx.Graph()
    >>> goal.add_weighted_edges_from([(0,1,n*n),(0,0,n*(n-1)/2), (1, 1, n*(n-1)/2)])
    >>> nx.is_isomorphic(int, goal)
    True
    """
    ret = nx.Graph()
    ret.add_nodes_from(partition.values())

    for node1, node2, datas in graph.edges_iter(data = True) :
        weight = datas.get("weight", 1)
        com1 = partition[node1]
        com2 = partition[node2]
        w_prec = ret.get_edge_data(com1, com2, {"weight":0}).get("weight", 1)
        ret.add_edge(com1, com2, weight = w_prec + weight)

    return ret


def __renumber(dictionary) :
    """Renumber the values of the dictionary from 0 to n
    """
    count = 0
    ret = dictionary.copy()
    new_values = dict([])

    for key in dictionary.keys() :
        value = dictionary[key]
        new_value = new_values.get(value, -1)
        if new_value == -1 :
            new_values[value] = count
            new_value = count
            count = count + 1
        ret[key] = new_value

    return ret


def __load_binary(data) :
    """Load binary graph as used by the cpp implementation of this algorithm
    """
    if type(data) == types.StringType :
        data = open(data, "rb")

    reader = array.array("I")
    reader.fromfile(data, 1)
    num_nodes = reader.pop()
    reader = array.array("I")
    reader.fromfile(data, num_nodes)
    cum_deg = reader.tolist()
    num_links = reader.pop()
    reader = array.array("I")
    reader.fromfile(data, num_links)
    links = reader.tolist()
    graph = nx.Graph()
    graph.add_nodes_from(range(num_nodes))
    prec_deg = 0

    for index in range(num_nodes) :
        last_deg = cum_deg[index]
        neighbors = links[prec_deg:last_deg]
        graph.add_edges_from([(index, int(neigh)) for neigh in neighbors])
        prec_deg = last_deg

    return graph


def __one_level(graph, status) :
    """Compute one level of communities
    """
    modif = True
    nb_pass_done = 0
    cur_mod = __modularity(status)
    new_mod = cur_mod

    while modif  and nb_pass_done != __PASS_MAX :
        cur_mod = new_mod
        modif = False
        nb_pass_done += 1

        for node in graph.nodes() :
            com_node = status.node2com[node]
            degc_totw = status.gdegrees.get(node, 0.) / (status.total_weight*2.)
            neigh_communities = __neighcom(node, graph, status)
            __remove(node, com_node,
                    neigh_communities.get(com_node, 0.), status)
            best_com = com_node
            best_increase = 0
            for com, dnc in neigh_communities.iteritems() :
                incr =  dnc  - status.degrees.get(com, 0.) * degc_totw
                if incr > best_increase :
                    best_increase = incr
                    best_com = com
            __insert(node, best_com,
                    neigh_communities.get(best_com, 0.), status)
            if best_com != com_node :
                modif = True
        new_mod = __modularity(status)
        if new_mod - cur_mod < __MIN :
            break


class Status :
    """
    To handle several data in one struct.

    Could be replaced by named tuple, but don't want to depend on python 2.6
    """
    node2com = {}
    total_weight = 0
    internals = {}
    degrees = {}
    gdegrees = {}

    def __init__(self) :
        self.node2com = dict([])
        self.total_weight = 0
        self.degrees = dict([])
        self.gdegrees = dict([])
        self.internals = dict([])
        self.loops = dict([])

    def __str__(self) :
        return ("node2com : " + str(self.node2com) + " degrees : "
            + str(self.degrees) + " internals : " + str(self.internals)
            + " total_weight : " + str(self.total_weight))

    def copy(self) :
        """Perform a deep copy of status"""
        new_status = Status()
        new_status.node2com = self.node2com.copy()
        new_status.internals = self.internals.copy()
        new_status.degrees = self.degrees.copy()
        new_status.gdegrees = self.gdegrees.copy()
        new_status.total_weight = self.total_weight

    def init(self, graph, part = None) :
        """Initialize the status of a graph with every node in one community"""
        count = 0
        self.node2com = dict([])
        self.total_weight = 0
        self.degrees = dict([])
        self.gdegrees = dict([])
        self.internals = dict([])
        self.total_weight = graph.size(weight = 'weight')
        if part == None :
            for node in graph.nodes() :
                self.node2com[node] = count
                deg = float(graph.degree(node, weight = 'weight'))
                if deg < 0 :
                    raise ValueError("Bad graph type, use positive weights")
                self.degrees[count] = deg
                self.gdegrees[node] = deg
                self.loops[node] = float(graph.get_edge_data(node, node,
                                                 {"weight":0}).get("weight", 1))
                self.internals[count] = self.loops[node]
                count = count + 1
        else :
            for node in graph.nodes() :
                com = part[node]
                self.node2com[node] = com
                deg = float(graph.degree(node, weigh = 'weight'))
                self.degrees[com] = self.degrees.get(com, 0) + deg
                self.gdegrees[node] = deg
                inc = 0.
                for neighbor, datas in graph[node].iteritems() :
                    weight = datas.get("weight", 1)
                    if weight <= 0 :
                        raise ValueError("Bad graph type, use positive weights")
                    if part[neighbor] == com :
                        if neighbor == node :
                            inc += float(weight)
                        else :
                            inc += float(weight) / 2.
                self.internals[com] = self.internals.get(com, 0) + inc



def __neighcom(node, graph, status) :
    """
    Compute the communities in the neighborood of node in the graph given
    with the decomposition node2com
    """
    weights = {}
    for neighbor, datas in graph[node].iteritems() :
        if neighbor != node :
            weight = datas.get("weight", 1)
            neighborcom = status.node2com[neighbor]
            weights[neighborcom] = weights.get(neighborcom, 0) + weight

    return weights


def __remove(node, com, weight, status) :
    """ Remove node from community com and modify status"""
    status.degrees[com] = ( status.degrees.get(com, 0.)
                                    - status.gdegrees.get(node, 0.) )
    status.internals[com] = float( status.internals.get(com, 0.) -
                weight - status.loops.get(node, 0.) )
    status.node2com[node] = -1


def __insert(node, com, weight, status) :
    """ Insert node into community and modify status"""
    status.node2com[node] = com
    status.degrees[com] = ( status.degrees.get(com, 0.) +
                                status.gdegrees.get(node, 0.) )
    status.internals[com] = float( status.internals.get(com, 0.) +
                        weight + status.loops.get(node, 0.) )


def __modularity(status) :
    """
    Compute the modularity of the partition of the graph faslty using status precomputed
    """
    links = float(status.total_weight)
    result = 0.
    for community in set(status.node2com.values()) :
        in_degree = status.internals.get(community, 0.)
        degree = status.degrees.get(community, 0.)
        if links > 0 :
            result = result + in_degree / links - ((degree / (2.*links))**2)
    return result


def main() :
    """Main function to mimic C++ version behavior"""
    try :
        filename = sys.argv[1]
        graphfile = __load_binary(filename)
        partition = best_partition(graphfile)
        print >> sys.stderr, str(modularity(partition, graphfile))
        for elem, part in partition.iteritems() :
            print str(elem) + " " + str(part)
    except (IndexError, IOError):
        print "Usage : ./community filename"
        print "find the communities in graph filename and display the dendogram"
        print "Parameters:"
        print "filename is a binary file as generated by the "
        print "convert utility distributed with the C implementation"


