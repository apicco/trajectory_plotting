import os
import tkinter as tk
import numpy as np
from matplotlib.colors import Normalize as norm
from matplotlib.figure import Figure 
import matplotlib.pyplot as plt
from skimage.external import tifffile as tiff
from trajalign.traj import Traj
from trajalign.average import load_directory

# to plot image frames
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# frames before and after as input parameters.

class Repr( Figure ) :

	def __init__( self , trajlist , j , r , im , master , cmap ) :
		
		# trajectory data
		self.j = j
		self.tlist = trajlist
		self.trajectory = self.tlist[ self.j ]
		self.fmin = np.nanmin( self.trajectory.frames() )
		self.fmax = np.nanmax( self.trajectory.frames() )
		self.f = self.fmin # frame

		# image data 
		self.image = im # image
		self.r = r # zoom radius

		# artist's canvas
		self.cmap = cmap
		self.figure = plt.figure( figsize = ( 5 , 4 ) , dpi = 100 )
		self.canvas = FigureCanvasTkAgg( self.figure , master = master ) 

	def df( self , d ) : # increment frames by d

		c = [ np.nan , np.nan ] # initiate a nan centroid coordinate
								# to enter the while loop
		
		old_frame = self.f		# store the old frame, in case there are
								# only nan until the end of the trajectory
								# file
		while c[ 0 ] != c[ 0 ] :
					
			if ( ( self.f + d >= self.fmin ) & ( self.f + d <= self.fmax ) ) :
		
				self.f = self.f + d
				c = self.centroid()

			else :
				
				self.f = old_frame
				break

	def zoom( self , r ) :

		self.r = self.r + r 

	def centroid( self ) :

		return [ self.trajectory.coord()[ 0 ][ self.f - self.fmin ] , self.trajectory.coord()[ 1 ][ self.f - self.fmin ] ] #i-th element in centrod coord is f - fmin

	def lims( self ) :

		return dict( xlims = [ max( 0 , int( - self.r + self.centroid()[0] ) ) , min( int( self.centroid()[0] + self.r ) , len( self.image[ 0 , 1 , : ] ) - 1 ) ] , ylims = [ max( 0 , int( -self.r + self.centroid()[1] ) ) , min( int( self.centroid()[1] + self.r ) , len( self.image[ 0 , : , 1 ] ) - 1 ) ] )

	def clear( self ) :
		
		plt.clf()
		
	def render( self ) : # rende the image 

		# load the region of interest within the image
		img = self.image[ int( self.f ) , self.lims()[ 'ylims'][ 0 ] : self.lims()[ 'ylims'][ 1 ] , self.lims()[ 'xlims' ][ 0 ] : self.lims()[ 'xlims' ][ 1 ] ]
	
		# show the image, aximg is outputed to refresh its content
		# in order to navigate faster within the frames
		aximg = plt.imshow( 
				img ,
				norm = norm( vmin = np.amin( self.image ) , vmax = np.amax( self.image ) ) , # intensity normalization
				cmap = self.cmap
				)											
		
		# graphical parameters
		plt.xlabel( "Pixels" )
		plt.ylabel( "Pixels" )
		plt.title( self.trajectory.annotations()[ 'file' ] + ' ' + '\n' + \
				'trajectory ' + str( self.j + 1 ) + '/' + str( len( self.tlist ) ) + '; ' + 'frame ' + str( self.f - self.fmin ) + '/' + str( self.fmax - self.fmin ) + '; ' + \
				r'$r=$' + str( self.r ) )
		
		self.canvas.draw()
		
		return aximg

	def update( self , aximg ) :
	
		img = self.image[ int( self.f ) , self.lims()[ 'ylims'][ 0 ] : self.lims()[ 'ylims'][ 1 ] , self.lims()[ 'xlims' ][ 0 ] : self.lims()[ 'xlims' ][ 1 ] ]  # image 
		aximg.set_array( img )
		plt.title( self.trajectory.annotations()[ 'file' ] + ' ' + '\n' + \
				'trajectory ' + str( self.j + 1 ) + '/' + str( len( self.tlist ) ) + '; ' + 'frame ' + str( self.f - self.fmin ) + '/' + str( self.fmax - self.fmin ) + '; ' + \
				r'$r=$' + str( self.r ) )
		self.canvas.draw()

def icheck( tt , path_movies = '' , path_datasets = '' , path_movie = '' , r = 7 , cmap = 'gray' , path_output = './' , marker = 's' , markersize = 25 , offset = ( 0 , 0 ) , anticipate = 0 ) :
	"""
	icheck( tt , path_movies = '' , path_datasets = '' , path_movie = '' , r = 7 , cmap = 'gray' ) :
		load the trajectories in path_trajectories 
	and show how they look like in their respective movies listed in path_movies, by showing a crop of 
	radius "r" around their centroid positoin. 
	If .annotations()[ 'datasetID' ] isn't there, the trajectories are mapped to their respective movies 
	with the datasets in path_dataset.
	icheck annotates all the selected and rejected trajectories into a .txt file. Trajectories selected and
	rejected are also annotated ( .annotations()[ "icheck_stamp" ] , which can be either "selected" or "rejected" ) 
	and are saved in two subfolders: "Selected_*" and "Rejected_*". The * is a number that will be updated if
	these subfolders are already present.
	in the trajectory files.
	- pattern is a pattern present in the file names, used to load the trajectories (load_directory input).
	- comment_char is a comment character which might be present in the trajectories.
	- coord_unit is pixel ('pxl') as default. 
	To do not bias the experimenter the trajectory position within the cell is not shown (compatibly with "r").
	"""

	def LoadMovie( path_movies , path_movie , t ) : 
		
		if path_movies : 
	
			movie_name = t.annotations()[ 'dataset' ][ 5 : -4 ] + '.tiff' 
			return tiff.imread( path_movies + '/' + movie_name )

		else : 

			return tiff.imread( path_movie )

	def LeftKey( event , frame , increment , aximg ) :
		
		frame.df( increment ) #frame increment to the left in case of nan
		frame.update( aximg[0] )

	def RightKey( event , frame , increment , aximg ) :

		frame.df( increment ) 
		frame.update( aximg[0] )
		
		frm.canvas.get_tk_widget().pack( side = tk . TOP , fill=tk.BOTH , expand = 1 )

	def ZoomOut( event , frame , increment , aximg ) :
	 
		frame.clear()

		frame.zoom( increment ) 
		aximg[0] = frame.render()
	
	def ZoomIn( event , frame , increment , aximg ) :
	
		frame.clear()
		
		frame.zoom( increment )
		
		aximg[0] = frame.render()
			
	def UpKey( event , frame , path , f ) :
	
		t = frame.trajectory()
		t.annotations()[ "icheck_stamp" ] = "Selected" 
		t.save( path + '/' + t.annotations()[ "file" ] )

		s_log = t.annotations()[ "file" ] + "\t-selected-" 
		f.write( s_log + '\n' )
		print( s_log )
			
#		if j == ( len( tt ) - 1 ) :
#
#			f.close()
#			SpotWindow.destroy()
#
#		else :
#			
#			# move to the next trajectory
#			v[ 'j' ] = v[ 'j' ] + 1 
#			Update_v( tt )
#			
#			GUI_plot( tt , 1 )
		
	def DownKey( event , tt , path , f ) :
		
		# select the trajctory
		t = frame.trajectory()
		
		t.annotations()[ "icheck_stamp" ] = "Rejected" 
		t.save( path + '/' + t.annotations()[ "file" ] )

		s_log = t.annotations()[ "file" ] + "\t-rejected-" 
		f.write( s_log + '\n' )
		print( s_log )
	
#		if v[ 'j' ] == ( len( tt ) - 1 ) :
#			f.close()
#			SpotWindow.destroy()
#		else :
#			# move to the next trajectory
#			v[ 'j' ] = v[ 'j' ] + 1 
#			Update_v( tt )
#			GUI_plot( tt , 1 )

	def ExitHeader( event ) :

		HeaderWindow.destroy()

#	def BackKey( event , tt , path_sel , path_rej ) :
#
#		if v[ 'j' ] > 0 :
#
#			v[ 'j' ] = v[ 'j' ] - 1
#			try : 
#				os.remove( path_sel + '/' + tt[ v[ 'j' ] ].annotations()[ 'file' ] )
#			except :
#				os.remove( path_rej + '/' + tt[ v[ 'j' ] ].annotations()[ 'file' ] )
#			print( tt[ v[ 'j' ] ].annotations()[ 'file' ] + '\t-undo-' )
#			
#			Update_v( tt )
#			GUI_plot( tt , 1 )
		
	HeaderWindow = tk.Tk() # create a Tkinter window
	HeaderWindow.wm_title( 'icheck' )

	# define and show a welcome header with command instructions
	header = "Welcome to icheck! You are going to asses the quality \n of the spots used to derive the trajectory list input " \
			+ "COMMANDS:\n" + \
			"- <Left> and <Right> arrows navigate you within the spot frames\n" + \
			"- the <Up> arrow annotates the trajectory as 'Selected' and saves it in\n" + path_output + "/Selected/\n" +\
			"- the <Down> arrow annotates the trajectory as 'Rejected' and saves it in\n" + path_output + "/Rejected/\n" +\
			"- the <BackSpace> undo the last selection/rejection and annotate the log\n" +\
			"- the <+> and <-> zoom in and out the image\n\n" +\
			"-> NOTE THAT iCheck USES THE CONVENTION img[ z , y , x ]!  <-\n" +\
			"->     For example, you will need to swap x and y coordinates     <-\n" +\
			"->     if you use an old version of ParticleTracker.                        <-\n\n"
	loading = "LOADING trajectories ASSIGNING their dataset ID..."
	loaded = "trajectories are loaded and assigned to their dataset ID.\n-> PRESS <space> TO CONTINUE <-"
	
	# --------------------------------------------------- #

	# Spot selection can be done multiple times to asses its 
	# robustness. If the Selected and Rejected folders exist already, then their name
	# is complemented with an iterated number.
	ps = path_output + '/Selected_0'
	pr = path_output + '/Rejected_0' 
	pd = path_output + '/FullDataset'
	pi = 0
	while ( os.path.exists( ps ) | os.path.exists( pr ) ) :

		ps = ps[ :-1 ] +  str( pi )
		pr = pr[ :-1 ] + str( pi )
		pi += 1

	os.makedirs( ps )
	os.makedirs( pr )
	if not os.path.exists( pd ) : 
		os.makedirs( pd )

	if not path_movie :

		print( 'assigning dataset ID...' )
		
		for i in range( len( tt ) ) :
			
			if 'dataset' not in tt[ i ].annotations().keys() :
				tt[ i ].assign_datasetID( path_datasets )
				tt[ i ].save( pd + '/' + tt[ i ].annotations()[ 'file' ] )
		
		print( '...dataset ID assigned' )
	
	# --------------------------------------------------- #
	
	l = tk.Label( HeaderWindow , text = header + loaded )
	l.pack()
	
	HeaderWindow.bind( '<space>' , ExitHeader )
	HeaderWindow.mainloop()

	f = open( path_output + '/icheck_log_' + str( pi ) + '.txt' , 'w+' )

	SpotWindow = tk.Tk()
	SpotWindow.wm_title( 'icheck' )

	frm = Repr( tt , 0 , r , LoadMovie( path_movies , path_movie , tt[ 0 ] ) , master = SpotWindow , cmap = cmap )

	aximg = [ frm.render() ]
	
	frm.canvas.get_tk_widget().pack( side = tk . TOP , fill=tk.BOTH , expand = 1 )
#
	SpotWindow.bind( "<Left>" , lambda event , frame = frm , increment = -1 , aximg = aximg : LeftKey( event , frame , increment , aximg ) )
	SpotWindow.bind( "<Right>" , lambda event , frame = frm , increment = 1 , aximg = aximg : RightKey( event , frame , increment , aximg ) )
#	#SpotWindow.bind( "<Up>" , lambda event , frame = frm , path = ps , f = f : UpKey( event , tt , path , f ) )
#	#SpotWindow.bind( "<Down>" , lambda event , tt = tt , path = pr , f = f : DownKey( event , tt , path , f ) )
##	SpotWindow.bind( "<BackSpace>" , lambda event , tt = tt , path_sel = ps , path_rej = pr : BackKey( event , tt , path_sel , path_rej ) )
	SpotWindow.bind( "-" , lambda event , frame = frm , increment = 1 , aximg = aximg : ZoomOut( event , frame , increment , aximg ) )
	SpotWindow.bind( "+" , lambda event , frame = frm , increment = -1 , aximg = aximg : ZoomIn( event , frame , increment , aximg ) )
#	
	SpotWindow.mainloop()
