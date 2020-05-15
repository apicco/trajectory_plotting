import os
import tkinter as tk
import numpy as np
from skimage.external import tifffile as tiff
from trajalign.traj import Traj
from trajalign.average import load_directory

# to plot image frames
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# Implement the default Matplotlib key bindings.
from matplotlib.figure import Figure
from matplotlib.backend_bases import key_press_handler

def icheck( path_raw_trajectories , path_movies , path_datasets , r = 5 , frame_col = 0 , coord_col = ( 2 , 3 ) , comment_char = '#' , pattern = '.txt$' , coord_unit = 'pxl' ) :
	"""
	icheck(  path_raw_trajectories , path_movies , r = 5 , frame_col = 0 , coord_col = ( 2 , 3 ) , 
		comment_char = '#' , pattern = '.txt$' , coord_unit = 'pxl' ) : , load the trajectories in path_trajectories 
	and show how they look like in their respective movies listed in path_movies, by showing a crop of 
	radius "r" around their centroid positoin. 
	If .annotations()[ 'datasetID' ] isn't there, the trajectories are mapped to their respective movies 
	with the datasets in path_dataset.
	icheck annotates all the selected and rejected trajectories into a .txt file. Trajectories selected and
	rejected are also annotated ( .annotations()[ "icheck_stamp" ] , which can be either "selected" or "rejected" ) 
	and are saved in two subfolders: "Selected_*" and "Rejected_*". The * is a number that will be updated if
	these subfolders are already present.
	- frame_col and coord_col are the column numbers where the frame and coordinate values are to be found 
	in the trajectory files.
	- pattern is a pattern present in the file names, used to load the trajectories (load_directory input).
	- comment_char is a comment character which might be present in the trajectories.
	- coord_unit is pixel ('pxl') as default. 
	To do not bias the experimenter the trajectory position within the cell is not shown (compatibly with "r").
	"""

	# v is a dict of variables containing all the relevant variables that need to be passed to the 
	# binding functions in tk. You should think of i as a list of pointers. i includes
	# "frame" : the current frame shown in the GUI
	# "frame_min" : the min frame value that can be shown, for that given trajectory. When a trajectory is 
	#				shown for the first time then i["frame"] = i["frame_min"]
	# "frame_max" : the max frame value that can be shown, for that given trajectory
	# "j" : the trajectory id in the trajectory list
	# "r" : the crop radius
	
	v = dict( frame = np.nan , frame_min = np.nan , frame_max = np.nan , j = 0 , r = r , path_movies = path_movies )

	def load_image( t ) : # load the spot image corresponding to the trajectory t
		t.annotations()[ 'dataset' ] 
		return

	def GUI_plot( tt , df ) : # show the frame
		
		# select the trajctory
		t = tt[ v[ 'j' ] ]
		
		# load the rigth movie
		movie_name = t.annotations()[ 'dataset' ][ 5 : -4 ] + '.tif'
		im = tiff.imread( v[ 'path_movies' ] + '/' + movie_name )
	
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
					( v[ "frame" ] < len( im ) ) 
				) : # check that we do not exceed frame_min, frame_max, and movie length
				
					c = [ t.coord()[ 0 ][ i ] , t.coord()[ 1 ][ i ] ] # centroid coordinate

			else :

				v[ "frame" ] = v_frame_old 
				i = v[ "frame" ] - v[ "frame_min" ] # trajectory element
				c = [ t.coord()[ 0 ][ i ] , t.coord()[ 1 ][ i ] ] # centroid coordinate
				break
			
		ax.clear()
		ax.imshow( 
				im[ int( v[ "frame" ] ) , 
					int( -v[ "r" ] + c[0] ) : int( c[0] + v[ "r" ] ) , 
					int(-v[ "r" ] + c[1] ) : int( c[1] + v[ "r" ] ) ] 
				)

		ax.set_xlabel( "Pixels" )
		ax.set_ylabel( "Pixels" )
		ax.set_title( 'Trajectory frame ' + str( i ) )
		canvas.draw()
	
	def LeftKey( event , tt ) :
		
		df = -1 #frame increment to the left in case of nan 	
		GUI_plot( tt , df ) 
			
	def RightKey( event , tt ) :

		df = 1  #frame increment to the right in case of nan	
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
			print( tt[ v[ 'j' ] ].annotations()[ 'file' ] + '-undo-' )
			
			Update_v( tt )
			GUI_plot( tt , 1 )

	HeaderWindow = tk.Tk() # create a Tkinter window
	HeaderWindow.wm_title( 'icheck' )

	# define and show a welcome header with command instructions
	header = "Welcome to icheck! You are going to asses the quality \n of the spots used to derive the trajectories in \n" + path_raw_trajectories + "\n\n " \
			+ "COMMANDS:\n" + \
			"- <Left> and <Right> arrows navigate you within the spot frames\n" + \
			"- the <Up> arrow annotates the trajectory as 'Selected' and saves it in\n" + path_raw_trajectories + "/Selected/\n" +\
			"- the <Down> arrow annotates the trajectory as 'Rejected' and saves it in\n" + path_raw_trajectories + "/Rejected/\n\n"
			"- the <BackSpace> undo the last selection/rejection and annotate the log"
	loading = "LOADING trajectories ASSIGNING their dataset ID..."
	loaded = "trajectories are loaded and assigned to their dataset ID.\n-> PRESS <space> TO CONTINUE <-"
	
	
	print( 'load trajectories...' )
	tt = load_directory(
			path = path_raw_trajectories , 
			pattern = pattern ,
			comment_char = comment_char , 
			coord_unit = coord_unit , 
			frames = frame_col , 
			coord = coord_col )

	print( 'assigning dataset ID...' )
	for i in range( len( tt ) ) :
		if 'dataset' not in tt[ i ].annotations().keys() :
			tt[ i ].assign_datasetID( path_datasets )
			tt[ i ].save( path_raw_trajectories + '/' + tt[ i ].annotations()[ 'file' ] )
	print( '...dataset ID assigned' )

	l = tk.Label( HeaderWindow , text = header + loaded )
	l.pack()
	
	HeaderWindow.bind( '<space>' , ExitHeader )
	HeaderWindow.mainloop()

	# --------------------------------------------------- #

	# Spot selection can be done multiple times to asses its 
	# robustness. If the Selected and Rejected folders exist already, then their name
	# is complemented with an iterated number.
	ps = path_raw_trajectories + '/Selected_0'
	pr = path_raw_trajectories + '/Rejected_0' 
	pi = 0
	while ( os.path.exists( ps ) | os.path.exists( pr ) ) :

		ps = ps[ :-1 ] +  str( pi )
		pr = pr[ :-1 ] + str( pi )
		pi += 1

	os.makedirs( ps )
	os.makedirs( pr ) 

	f = open( ps + '/icheck_log.txt' , 'w+' )

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
	SpotWindow.mainloop()
