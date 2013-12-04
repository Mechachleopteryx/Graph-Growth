import grow
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

csvfile = 'conceptnet.csv'
graph_db = grow.database() # I could set this up to support multiple databases and graphs...maybe just ask for a graph name.
print 'Started new graph database'
indexcol= True
#make sure graph DB initialized 
print 'Graph Database  Version: ' + str(graph_db.neo4j_version)
csvfile = open(csvfile)
reader = csv.reader(csvfile,delimiter=',')
nodes = {} # keep track of nodes already in graph_db.
def get_or_create_node(graph_db, name):
    if name not in nodes:
        nodes[name], = graph_db.create(node(name=name)) #make the node if it doesn't exist 
    return nodes[name] #return the node
print 'Loading graph into database...'
for row in reader:
    parent = get_or_create_node(graph_db, row[1])
    child = get_or_create_node(graph_db, row[2])
    print 'parent: ' + row[1] + ', child is: ' + row[2]
    parent_child, = graph_db.create(rel(parent, "--", child))
print 'Loaded graph into database with.'
pickle.dump(nodes, open("nodes.p", "wb" ) )