import grow
# graphfile = 'edgeFileWords.csv'
# grow.load(graphfile)
data = grow.growgraph(force_connected = True, growthfactor=20, plot = False, plotx = 'edgegrowth', ploty2 = 'run_time', num_measurements = 100)

## make random growthfactor.
## make plotting with graph visualization as it grows.