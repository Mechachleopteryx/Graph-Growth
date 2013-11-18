from grow import *

usenx= True
force_connected = True
sparse = True
plot = True
directed = True
randomgrowth=False
wholegrowth=True
growthfactor=100
num_measurements = 10
verbose = True
connected = True
plotx = 'nodegrowth'
ploty = 'maxclique'
ploty2 = 'modularity'
drawgraph = 'triangulated'
draw= False
drawspectral = False
getgraph = True
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
    sparsemeasurements = [6,7,8,9,growthfactor]
    measurements = np.logspace(1, (int(len(str(growthfactor))))-1, num_measurements)
    for x in measurements:
        sparsemeasurements.append(int(x))
else:
	sparsemeasurements = range(2,growthfactor)

# this will actually only work for directed graph because we are moralizing, but I want to leave the option for later. Perhaps I can just skip moralization for undirected graphs.
if directed:
	graph = nx.DiGraph()
else:
	graph = nx.graph()




# pick an initial node to start from
initial_node = random.choice(nodes.keys()) #randomly get a node to add from dictionary
if verbose:
    print 'Starting from ' + initial_node
initial_used = 0 #keep track of how many times the initial node was used
nodegrowth = len(graph.nodes())
edgegrowth = len(graph.edges())
while nodegrowth < growthfactor: # make sure we aren't above how many nodes we want to measure in the graph    
	#start off finding a node to add to the graph.
	if force_connected == True:
		try:
			possiblenodes = graph.nodes() # get all nodes in graph.
			fromnode = random.choice(possiblenodes) #pick random node in graph to grow from(add one of its nieghbors)
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
		new_node_rels = list(graph_db.match(end_node = fromnode, bidirectional=True))
		new_rel = random.choice(new_node_rels) #randomly pick one of them, thus picking a node to add to graph.

		# is the new node a parent or child of the node we are growing from?
		if new_rel.end_node == fromnode:
		    new_node = new_rel.start_node
		if new_rel.start_node == fromnode:
		    new_node = new_rel.end_node
		assert new_node != fromnode
	
	if force_connected == False: # if not connected, we can just pick from the pickled dictionary of nodes in the database
		new_node = random.choice(possiblenodes.values())
		
	print 'adding' + str(new_node)
	#add the nodes to the graph, connecting it to nodes in the graph that it is connected to.
    # go through the list of edges that have the new node as a part of it, and only add the edge if they are between the new node and a node in the graph already.
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

	    #here is where we measure everything about the graph 
	if nodegrowth in sparsemeasurements: #we only measure every now and then in sparse.
		start_time = time()
		# try: #modularity
		if nodegrowth > 5:
			modgraph = nx.Graph(graph) #make it into a networkx graph
			partition = best_partition(modgraph) #find the partition with maximal modularity
			modval = modularity(partition,modgraph) #calculate modularity with that partition
		# except: #can't calculate modularity on super small graphs.
		# 	modularity = 0.0 
		#option to use python nx to moralize and triangulate
		if usenx == True:
			moralized = moral_graph(graph)
		else: #use Octave to run Matlab Bayes Net Toolbox
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
		order = range(len(moralized)+1) # BNT needs order of nodes to triangulate
		order = order[1:]
		# order = np.random.shuffle(order) #then shuffle it 
		istriangulated = False
		tries = 0
		while istriangulated == False and tries < 5: #sometimes oct2py takes too long to return I think
		    try:
		        moralized = nx.to_numpy_matrix(moralized) 
		        triangulated, cliques, fill_ins = octave.triangulate(moralized,order)
		        istriangulated = True
		        tries = 5
		    except:
		        istriangulated = False
		        print 'Octave Error, trying again!'
		        tries = tries + 1 
		cliquesizes = [] #empty array to keep clique sizes in
		#loop through cliques and get the size of them
		for x in cliques:
		    size = len(x)
		    cliquesizes.append(size)
		maxclique = max(cliquesizes) #get the biggest clique
		avgclique = np.mean(cliquesizes) # get the mean of the clique sizes
		end_time = time()
		run_time = end_time - start_time #time how long all the took
		data.append([nodegrowth, len(graph.edges()), modval, maxclique,avgclique,run_time]) #store results
		sparsemeasurements.remove(nodegrowth) #so we don't calculate clique size more than once!
		if verbose:
		    print 'took ' + str(run_time) + ' to run last computation'
		#this will always print, basic status update everytime clique size is measured.
		print 'Growing graph with ' + str(nodegrowth) + ' nodes, ' + str(modval) + ' modularity, max clique of ' + str(maxclique) + ', ' + str(len(graph.edges())) + ' edges.'
		#this will redraw the plot everytime a computation is done.
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
df = pd.DataFrame(data, columns= ('nodegrowth','edgegrowth', 'modularity','maxclique','avgclique','run_time'))