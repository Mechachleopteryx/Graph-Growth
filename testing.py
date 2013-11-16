import grow
# graphfile = 'edgeFileWords.csv'
# grow.load(graphfile)
data = grow.growgraph(growthfactor=3000, plot = True, plotx = 'edgegrowth', ploty2 = 'run_time', num_measurements = 100)

## make random growthfactor.
## make plotting with graph visualization as it grows. 