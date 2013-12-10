import numpy as np

homedir = '/home/despo/mb3152/gitrepos/studies/Combo_LesionNetworks/'
atlases = ['power', 'shen']
projects = ['lesion', 'sham']
costs = [.05,.1,.15,.2,.25]
modtypes = ['spectral', 'SA']

#load all modularity results into dataframe
for atlas in atlases:
	for project in projects:
		for modtype in modtypes:
			for cost in costs:
				data_file = homedir + 'corr_%s_%s/%s_output/avgblock_avgsubj/modval_S0_b0_%s.npy' %(project,atlas,modtype,cost)
				data = np.load(data_file)
				print 'modularity for ' + atlas,project,str(modtype),str(cost) + ' is: ' + str(data)

lesion_shen_SA = []
lesion_power_SA = []
lesion_shen_spectral = []
lesion_power_spectral = []
sham_shen_SA = []
sham_power_SA = []
sham_shen_spectral = []
sham_power_spectral = []

for atlas in atlases:
	for project in projects:
		for modtype in modtypes:
			for cost in costs:
				data_file = homedir + 'corr_%s_%s/%s_output/avgblock_avgsubj/modval_S0_b0_%s.npy' %(project,atlas,modtype,cost)
				data = np.load(data_file)
				('%s_%s_%s'%(project,atlas,modtype)).append(data)

for atlas in atlases:
	for project in projects:
		for modtype in modtypes:
			print 'mean of: ' + ('%s_%s_%s'%(atlas,project,modtype)) + 'is: ' + np.mean('%s_%s_%s'%(atlas,project,modtype))