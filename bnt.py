#This is the function we will call to run the BNT.
from oct2py import Oct2Py #this is not built in.
from oct2py import octave as bnt

def run(command,numtries=5):
	tries = 0
	c = 'bnt.' + str(command)
	exec(c)
	# while tries < numtries: 
	# 	try:
	# 		print 'Executing ' + str(c) + ' in Octave.'
	# 		exec(c)
	# 		tries = numtries
	# 	except:
	# 		tries = tries + 1 
	# 		print 'Octave Error on try %s' % (tries)
	# 		if tries == numtries:
	# 			print 'Terminal Octave Error'
	# 			1/0