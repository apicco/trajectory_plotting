import os
import tkinter as tk
import numpy as np
from  matplotlib.colors import Normalize as norm
from skimage.external import tifffile as tiff
from trajalign.traj import Traj
from trajalign.average import load_directory

# to plot image frames
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# Implement the default Matplotlib key bindings.
from matplotlib.figure import Figure
from matplotlib.backend_bases import key_press_handler

def icheck( tt , path_movies = '' , path_datasets = '' , path_movie = '' , r = 7 , cmap = 'gray' , path_output = './' ) :
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

	def GUI_plot( tt , df , ms = 25 ) : # show the frame

		# select the trajctory
		t = tt[ v[ 'j' ] ]
		t_name = t.annotations()[ 'file' ]
		
		# identify which centroid coordinate to associate with the frame
		# start with nan centroid, centroid coordines must not be nan, therefore
		# search for the first not nan and increment i "frame" accordingly
		c = [ np.nan , np.nan ]
		v_frame_old = v[ 'frame' ]  # used to stall the movie in case v[ "frame" ] reaches
									# frame_min, frame_max, or movie length
		while c[ 0 ] != c[ 0 ] :

			v[ "frame" ] = v[ "frame" ] + df
			i = v[ "frame" ] - v[ "frame_min" ] # trajectory element
			if ( 
					( v[ "frame" ] >= v[ "frame_min" ] ) & 
					(  v[ "frame" ] <= v[ "frame_max" ] ) & 
					( v[ "frame" ] < len( v[ 'image' ] ) ) 
				) : # check that we do not exceed frame_min, frame_max, and movie length
				
					c = [ t.coord()[ 0 ][ i ] , t.coord()[ 1 ][ i ] ] # centroid coordinate

			else :

				v[ "frame" ] = v_frame_old 
				i = v[ "frame" ] - v[ "frame_min" ] # trajectory element
				c = [ t.coord()[ 0 ][ i ] , t.coord()[ 1 ][ i ] ] # centroid coordinate
				break

		ax.clear()

		# Plot image. Note: +1 in centroid positions is to center the spot in the quadrant. 
		# I suspect probem between PT and python nomenclatures 
		# (one starts at 1 the other at 0) 
	
		xlims = [ max( 0 , int( -v[ "r" ] + c[0] ) ) ,
			min( int( c[0] + v[ "r" ] ) , len( v[ 'image'][ 0 , 1 , : ] ) - 1 ) ]
		ylims = [ max( 0 , int( -v[ "r" ] + c[1] ) ) ,
			min( int( c[1] + v[ "r" ] ) , len( v[ 'image'][ 0 , : , 1 ] ) - 1 ) ]

		ax.imshow(	
				v[ 'image' ][ int( v[ "frame" ] ) , 
				ylims[0] : ylims[1] , 
				xlims[0] : xlims[1] ], 
				cmap = v[ 'cmap' ]  , norm = norm(  vmin = np.amin( v[ 'image' ] ) , vmax = np.amax( v[ 'image' ] ) )
				)
		
		ax.plot( c[0] - xlims[ 0 ] ,  c[1] - ylims[ 0 ] , color = 'red' , marker = '+' , mew = 0.5 , ms = ms , fillstyle = 'none' , )
		ax.set_xlabel( "Pixels" )
		ax.set_ylabel( "Pixels" )
		ax.set_title( t_name + ' ' + '\n' + \
				'trajectory ' + str( v[ 'j' ] + 1 ) + '/' + str( len( tt ) ) + '; ' + 'frame ' + str( i ) + '/' + str( v[ "frame_max" ] - v[ "frame_min" ] ) + '; ' + \
				r'$r=$' + str( v[ "r" ] ) )
		canvas.draw()

	def LeftKey( event , tt ) :
		
		df = -1 #frame increment to the left in case of nan 	
		GUI_plot( tt , df ) 
			
	def RightKey( event , tt ) :

		df = 1  #frame increment to the right in case of nan	
		GUI_plot( tt , df )

	def ZoomOut( event , tt ) :
		
		v[ "r" ] = v[ "r" ] + 1
		df = 0
		GUI_plot( tt , df ) 

	def ZoomIn( event , tt ) :
		
		v[ "r" ] = v[ "r" ] - 1
		df = 0
		GUI_plot( tt , df ) 
			
	def UpKey( event , tt , path , f ) :
		
		# select the trajctory
		t = tt[ v[ 'j' ] ]

		t.annotations()[ "icheck_stamp" ] = "Selected" 
		t.save( path + '/' + t.annotations()[ "file" ] )

		s_log = t.annotations()[ "file" ] + "\t-selected-" 
		f.write( s_log + '\n' )
		print( s_log )
			
		if v[ 'j' ] == ( len( tt ) - 1 ) :

			f.close()
			SpotWindow.destroy()

		else :
			
			# move to the next trajectory
			v[ 'j' ] = v[ 'j' ] + 1 
			Update_v( tt )
			
			GUI_plot( tt , 1 )
		
	def DownKey( event , tt , path , f ) :
		
		# select the trajctory
		t = tt[ v[ 'j' ] ]
		
		t.annotations()[ "icheck_stamp" ] = "Rejected" 
		t.save( path + '/' + t.annotations()[ "file" ] )

		s_log = t.annotations()[ "file" ] + "\t-rejected-" 
		f.write( s_log + '\n' )
		print( s_log )
	
		if v[ 'j' ] == ( len( tt ) - 1 ) :
			f.close()
			SpotWindow.destroy()
		else :
			# move to the next trajectory
			v[ 'j' ] = v[ 'j' ] + 1 
			Update_v( tt )
			GUI_plot( tt , 1 )

	def ExitHeader( event ) :

		HeaderWindow.destroy()

	def Update_v( tt ) :
	
		# select the trajctory
		t = tt[ v[ 'j' ] ]
		
		# load the rigth movie
		movie_name = t.annotations()[ 'dataset' ][ 5 : -4 ] + '.tif'
		if v[ "path_movies" ] :
			
			im = tiff.imread( v[ 'path_movies' ] + '/' + movie_name )
		
		elif v[ "path_movie" ] : 

			im = tiff.imread( v[ 'path_movie' ] )

		else :

			raise AttributeError( 'Verify that path_movie, to a single movie tif file, or path_movies, to a folder containing one or more movie tif files, are correct' )

		v[ 'image' ] = im

		v[ "frame_min" ] = np.nanmin( tt[ v[ 'j' ] ].frames() )
		v[ "frame_max" ] = np.nanmax( tt[ v[ 'j' ] ].frames() ) 
		v[ "frame" ] = v[ "frame_min" ] - 1 # the -1 because Update_v is used before 
											# plotting the first frame of a spot.
											# Plotting is done with GUI_plot that does 
											# df increments of magnitude +/- 1. As the 
											# first frame can have nan coordinates, it 
											# is important to use GUI_plot( tt , 1 ) instead
											# of GUI_plot( tt , -1 ). Hence the -1 here.

	def BackKey( event , tt , path_sel , path_rej ) :

		if v[ 'j' ] > 0 :

			v[ 'j' ] = v[ 'j' ] - 1
			try : 
				os.remove( path_sel + '/' + tt[ v[ 'j' ] ].annotations()[ 'file' ] )
			except :
				os.remove( path_rej + '/' + tt[ v[ 'j' ] ].annotations()[ 'file' ] )
			print( tt[ v[ 'j' ] ].annotations()[ 'file' ] + '\t-undo-' )
			
			Update_v( tt )
			GUI_plot( tt , 1 )
		
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
	
	# v is a dict of variables containing all the relevant variables that need to be passed to the 
	# binding functions in tk. You should think of i as a list of pointers. i includes
	# "frame" : the current frame shown in the GUI
	# "frame_min" : the min frame value that can be shown, for that given trajectory. When a trajectory is 
	#				shown for the first time then i["frame"] = i["frame_min"]
	# "frame_max" : the max frame value that can be shown, for that given trajectory
	# "j" : the trajectory id in the trajectory list
	# "r" : the crop radius

	if path_movie : 
	
		v = dict( frame = np.nan , frame_min = np.nan , frame_max = np.nan , j = 0 , r = r , cmap = cmap , path_movies = '' , path_movie = path_movie )

	else :
		
		v = dict( frame = np.nan , frame_min = np.nan , frame_max = np.nan , j = 0 , r = r , cmap = cmap , path_movies = path_movies , path_movie = '' )

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

	Update_v( tt )

	fig = Figure( figsize = (  5 , 4 ) , dpi = 100 )
	ax = fig.add_subplot( 111 )
	canvas = FigureCanvasTkAgg( fig , master = SpotWindow )  # A tk.DrawingArea.

	GUI_plot( tt , 1 )

	canvas.get_tk_widget().pack( side = tk . TOP , fill=tk.BOTH , expand = 1 )

	SpotWindow.bind( "<Left>" , lambda event , tt = tt : LeftKey( event , tt ) )
	SpotWindow.bind( "<Right>" , lambda event , tt = tt : RightKey( event , tt ) )
	SpotWindow.bind( "<Up>" , lambda event , tt = tt , path = ps , f = f : UpKey( event , tt , path , f ) )
	SpotWindow.bind( "<Down>" , lambda event , tt = tt , path = pr , f = f : DownKey( event , tt , path , f ) )
	SpotWindow.bind( "<BackSpace>" , lambda event , tt = tt , path_sel = ps , path_rej = pr : BackKey( event , tt , path_sel , path_rej ) )
	SpotWindow.bind( "-" , lambda event , tt = tt : ZoomOut( event , tt ) )
	SpotWindow.bind( "+" , lambda event , tt = tt : ZoomIn( event , tt ) )
	
	SpotWindow.mainloop()
