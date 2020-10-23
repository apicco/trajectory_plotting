import os
import tkinter as tk
import numpy as np
from matplotlib.colors import Normalize as norm
import matplotlib.pyplot as plt
from skimage.external import tifffile as tiff
from trajalign.traj import Traj
from trajalign.average import load_directory

# to plot image frames
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ----------------------
# DEFINE THE OBJECT Repr
class Repr() :

	def __init__( self , trajlist , j , r , master , cmap , buffer_frames , offset , marker , markersize , saturation,  path_movie = '' , path_movies = '' ) :
	
		# trajectory data
		self.tlist = trajlist

		# trajectory parameters
		self.j = j
		self.offset = offset 
		self.trajectory = None # self.tlist[ self.j ]
		self.fmin = None # np.nanmin( self.trajectory.frames() )
		self.fmax = None # np.nanmax( self.trajectory.frames() )
		self.f = None # self.fmin # frame

		# image data 
		self.path_movies = path_movies 
		self.path_movie = path_movie
		# if there is only one movie (i.e. path_movie not = '' )
		# then that is also the name of the movie
		if ( ( self.path_movie != '' ) & ( self.path_movies == '' ) ) :
			self.im_name = self.path_movie
		elif ( ( self.path_movie == '' ) & ( self.path_movies != '' ) ) :
			self.im_name = None # im_name
		else :
			raise AttributeError( 'You must specify either the path to a movie (path_movie), or the path to a folder containing several movies (path_movies)' )
		self.image = None # tiff.imread( self.im_name ) 
		self.lb = None
		self.ub = None
		self.r = r # zoom radius

		# artist's canvas
		self.bff = buffer_frames
		self.cmap = cmap
		self.figure = plt.figure( figsize = ( 5 , 4 ) , dpi = 100 )
		self.canvas = FigureCanvasTkAgg( self.figure , master = master ) 

		# plotting parameters
		self.marker = marker
		self.markersize = markersize
		self.saturation = saturation

	def initiate( self , j = None ) :

		# initiate the trajectory parameters in the Repr object
		if not j :

			self.trajectory = self.tlist[ self.j ]

		else :

			self.j = j
			self.trajectory = self.tlist[ self.j ]
		
		# translate the trajectory by the offset, if any
		self.trajectory.translate( self.offset ) 

		# initiate the new image, if needed

		if self.path_movies : 
			
			im_name = self.trajectory.annotations()[ 'dataset' ][ 5 : -4 ] + '.tif'
		
			if self.im_name != im_name:
	
				print( '-- loading new movie ' + str( im_name ) )
				self.im_name = im_name
				self.image = tiff.imread( self.path_movies + '/' + self.im_name )

		else :
			
			self.image = tiff.imread( self.im_name )

		# initiate fmin and fmax
		self.fmin = np.nanmin( self.trajectory.frames() )
		self.fmax = np.nanmax( self.trajectory.frames() )

		# start from self.buffer_frames before the start of the trajectory
		# if the trajectory is too close to the beginning of the movie, then
		# start from zero
		self.f = max( 0 , self.fmin - self.bff )
	
		# define the lower and upper boundary of the Representation 
		self.lb = max( 0 , self.fmin - self.bff )						# lower boundary
		self.ub = min( self.fmax + self.bff , self.image.shape[ 0 ] )	# upper boundary
		
	def df( self , d ) : # increment frames by d
	
		c = [ np.nan , np.nan ] # initiate a nan centroid coordinate
								# to enter the while loop
		
		old_frame = self.f		# store the old frame, in case there are
								# only nan until the end of the trajectory
								# file
		while c[ 0 ] != c[ 0 ] :
				
			# if self.f + d is comprised in the lower and upperboundaries
			# then do the incrememtn and compute the centroid, otherwise
			# stall.
			if ( ( self.f + d >= self.lb ) & ( self.f + d <= self.ub ) ) :
	
				self.f = self.f + d
				c = self.centroid()

			elif ( self.f + d < self.lb ) :
				
				self.f = self.lb 
				break

			elif ( self.f + d > self.ub ) :
				
				self.f = self.ub 
				break
	
	def saturate( self , increment ) :

		new_saturation =  self.saturation + increment

		#saturation cannot exceed 0 and 1 boundaries
		if ( ( new_saturation >= 0 ) & ( new_saturation <= 1 ) ) :

			self.saturation = new_saturation

	def zoom( self , r ) :
		
		# zoom increment
		self.r = self.r + r 

	def centroid( self ) :

		# output the centroid coordinates of the trajectory, if the trajectory exists on
		# the self.f frame. Otherwise output the centroid coordinate from the nearest frame
		# within the trajectory
		if ( ( self.f >= self.fmin ) & ( self.f <= self.fmax ) ) :

			return [ self.trajectory.coord()[ 0 ][ self.f - self.fmin ] , self.trajectory.coord()[ 1 ][ self.f - self.fmin ] ] #i-th element in centrod coord is f - fmin

		elif ( self.f < self.fmin ) :

			return [ self.trajectory.coord()[ 0 ][ 0 ] , self.trajectory.coord()[ 1 ][ 0 ] ] #i-th element in centrod coord is f - fmin

		elif ( self.f > self.fmax ) :

			return [ self.trajectory.coord()[ 0 ][ len( self.trajectory ) - 1 ] , self.trajectory.coord()[ 1 ][ len( self.trajectory ) - 1 ] ] #i-th element in centrod coord is f - fmin
	def lims( self ) :

		return dict( xlims = [ max( 0 , int( - self.r + self.centroid()[0] ) ) , min( int( self.centroid()[0] + self.r ) , len( self.image[ 0 , 1 , : ] ) - 1 ) ] , ylims = [ max( 0 , int( -self.r + self.centroid()[1] ) ) , min( int( self.centroid()[1] + self.r ) , len( self.image[ 0 , : , 1 ] ) - 1 ) ] )

	def clear( self ) :
		
		# clear the figure content 
		plt.clf()
		
	def render( self ) : # render the image and centroid coordinate

		# load the region of interest within the image
		img = self.image[ int( self.f ) , self.lims()[ 'ylims'][ 0 ] : self.lims()[ 'ylims'][ 1 ] , self.lims()[ 'xlims' ][ 0 ] : self.lims()[ 'xlims' ][ 1 ] ]
	
		# show the image, aximg is outputed to refresh its content
		# in order to navigate faster within the frames
		aximg = plt.imshow( 
				img ,
				norm = norm( vmin = np.amin( self.image ) , vmax = ( np.amax( self.image ) - self.saturation * ( np.amax( self.image ) - np.amin( self.image )) ) ) , # intensity normalization
				cmap = self.cmap
				)											
		
		# plot centroid
		axcentroid = plt.plot( self.centroid()[ 0 ] - self.lims()[ 'xlims' ][ 0 ] , self.centroid()[ 1 ] - self.lims()[ 'ylims' ][ 0 ] , marker = self.marker , markersize = self.markersize , color = 'red' , markerfacecolor = 'none') 
		
		# graphical parameters
		plt.xlabel( "Pixels" )
		plt.ylabel( "Pixels" )

		plt.title( self.trajectory.annotations()[ 'file' ] + ' ' + '\n' + \
				'trajectory ' + str( self.j + 1 ) + '/' + str( len( self.tlist ) ) + '; ' + 'frame ' + str( self.f - self.fmin ) + '/' + str( self.fmax - self.fmin ) + '; ' + \
				r'$r=$' + str( self.r ) + '; ' + \
				r'$s=$' + str( round( self.saturation , 2 ) ) )
		
		self.canvas.draw()
		
		return [ aximg , axcentroid[ 0 ] ]

	def update( self , ax ) : # update the image and centroid already rendered
	
		img = self.image[ int( self.f ) , self.lims()[ 'ylims'][ 0 ] : self.lims()[ 'ylims'][ 1 ] , self.lims()[ 'xlims' ][ 0 ] : self.lims()[ 'xlims' ][ 1 ] ]  # image 
		ax[0].set_array( img )
	
		# plot centroid
		ax[1].set_data( self.centroid()[ 0 ] - self.lims()[ 'xlims' ][ 0 ] , self.centroid()[ 1 ] - self.lims()[ 'ylims' ][ 0 ] )
		
		plt.title( self.trajectory.annotations()[ 'file' ] + ' ' + '\n' + \
				'trajectory ' + str( self.j + 1 ) + '/' + str( len( self.tlist ) ) + '; ' + 'frame ' + str( self.f - self.fmin ) + '/' + str( self.fmax - self.fmin ) + '; ' + \
				r'$r=$' + str( self.r ) + '; ' + \
				r'$s=$' + str( round( self.saturation , 2 ) ) )
			
		self.canvas.draw()

# -----------------------------------------------------
# DEFINE THE FUNCTION ICHECK WHICH USES THE OBJECT Repr
def icheck( tt , path_movies = '' , path_datasets = '' , path_movie = '' , r = 7 , cmap = 'gray' , path_output = './' , marker = 's' , markersize = 25 , buffer_frames = 0 , offset = ( 0 , 0 ) , movie_appendix = '.tif' , saturation = 0 ) :
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

	def ArrowKey( event , frame , increment , ax ) :

		frame.df( increment ) 
		frame.update( ax )
		
		#frm.canvas.get_tk_widget().pack( side = tk . TOP , fill=tk.BOTH , expand = 1 )

	def SaturateKey( event , frame , increment , ax ) :

		frame.clear()
		frame.saturate( increment )

		new_ax = frame.render()
		ax[ 0 ] = new_ax[ 0 ]
		ax[ 1 ] = new_ax[ 1 ]

	def ZoomOut( event , frame , increment , ax ) :
	 
		frame.clear()

		frame.zoom( increment ) 
		
		new_ax = frame.render()
		ax[ 0 ] = new_ax[ 0 ]
		ax[ 1 ] = new_ax[ 1 ]
	
	def ZoomIn( event , frame , increment , ax ) :
	
		frame.clear()
		
		frame.zoom( increment )
		
		new_ax = frame.render()
		ax[ 0 ] = new_ax[ 0 ]
		ax[ 1 ] = new_ax[ 1 ]
			
	def UpKey( event , frame , path , f , ax ) :

		# load the trajectory info, update it, and save the trajectory
		t = frame.trajectory
		t.annotations()[ "icheck_stamp" ] = "Selected" 
		t.save( path + '/' + t.annotations()[ "file" ] )

		# save log
		s_log = t.annotations()[ "file" ] + "\t-selected-" 
		f.write( s_log + '\n' )

		# print log
		print( s_log )
			
		if frame.j == ( len( frame.tlist ) - 1 ) :

			f.close()
			SpotWindow.destroy()

		else :
			
			# move to the next trajectory
			frame.initiate( frame.j + 1 ) 
			
			# clear the figure
			frame.clear()
			
			# render the new figure
			new_ax = frame.render()
			ax[ 0 ] = new_ax[ 0 ]
			ax[ 1 ] = new_ax[ 1 ]
		
	def DownKey( event , frame , path , f , aximg ) :
		
		# load the trajectory info, update it, and save the trajectory
		t = frame.trajectory
		t.annotations()[ "icheck_stamp" ] = "Rejected" 
		t.save( path + '/' + t.annotations()[ "file" ] )

		# save log
		s_log = t.annotations()[ "file" ] + "\t-rejected-" 
		f.write( s_log + '\n' )

		# print log
		print( s_log )
			
		if frame.j == ( len( frame.tlist ) - 1 ) :

			f.close()
			SpotWindow.destroy()

		else :
			
			# move to the next trajectory
			frame.initiate( frame.j + 1 ) 

			# clear the figure
			frame.clear()
		
			# render the new figure
			new_ax = frame.render()
			ax[ 0 ] = new_ax[ 0 ]
			ax[ 1 ] = new_ax[ 1 ]

	def ExitHeader( event ) :

		HeaderWindow.destroy()

	def BackKey( event , frame , path_sel , path_rej , ax ) :

		if frame.j > 0 :

			frame.j = frame.j - 1
			try : 
				os.remove( path_sel + '/' + frame.tlist[ frame.j ].annotations()[ 'file' ] )
			except :
				os.remove( path_rej + '/' + frame.tlist[ frame.j ].annotations()[ 'file' ] )
			print( frame.tlist[ frame.j ].annotations()[ 'file' ] + '\t-undo-' )
	
		# clear the figure
		frame.clear()
	
		# initiate the j-th trajectory
		frame.initiate()

		# render the new figure
		new_ax = frame.render()
		ax[ 0 ] = new_ax[ 0 ]
		ax[ 1 ] = new_ax[ 1 ]
		
	HeaderWindow = tk.Tk() # create a Tkinter window
	HeaderWindow.wm_title( 'icheck' )

	# define and show a welcome header with command instructions
	header = "Welcome to icheck! You are going to asses the quality \n of the spots used to derive the trajectory list input\n" \
			+ "COMMANDS:\n" + \
			"- <Left> and <Right> arrows navigate you within the spot frames\n" + \
			"- <Shift-Left> and <Shift-Right> arrows navigate you within the spot frames \n" +"by increments of 10 frames\n" + \
			"- the <Up> arrow annotates the trajectory as 'Selected' and saves it in\n" + path_output + "/Selected/\n" +\
			"- the <Down> arrow annotates the trajectory as 'Rejected' and saves it in\n" + path_output + "/Rejected/\n" +\
			"- the <BackSpace> undo the last selection/rejection and annotate the log\n" +\
			"- the <+> and <-> zoom in and out the image\n" +\
			"- the <s> and <d> increase and decrease the image saturation\n" +"Saturation is shown as parameter " +r"s in [0,1)" + " in plot title\n\n" +\
			"-> NOTE THAT iCheck USES THE CONVENTION img[ z , y , x ]!  <-\n" +\
			"->     For example, you will need to swap x and y coordinates     <-\n" +\
			"->     if you use an old version of ParticleTracker.                        <-\n\n"
	loading = "LOADING trajectories ASSIGNING their dataset ID..."
	loaded = "trajectories are loaded and assigned to their dataset ID.\n-> PRESS <space> TO CONTINUE <-"
	
	# --------------------------------------------------- #

	# Spot selection can be done multiple times to asses its 
	# robustness. If the Selected and Rejected folders exist already, then their name
	# is complemented with an iterated number.
	pi = 0
	pd = path_output + '/FullDataset'
	ps = path_output + f'/Selected_{pi:02}'
	pr = path_output + f'/Rejected_{pi:02}' 

	while ( os.path.exists( ps ) | os.path.exists( pr ) ) :

		pi += 1
	
		ps = path_output + f'/Selected_{pi:02}'
		pr = path_output + f'/Rejected_{pi:02}' 
	
	os.makedirs( ps )
	os.makedirs( pr )

	if not os.path.exists( pd ) : 
	
		os.makedirs( pd )

	if not path_movie :

		print( 'assigning dataset ID... this might take some time, be patient' )
		
		if path_datasets == '' :

			raise AttributeError( 'in icheck, path_datasets should not be empty. Please, assign a dataset path' )

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

	f = open( path_output + f'/icheck_log_{pi:02}.txt' , 'w+' )

	SpotWindow = tk.Tk()
	SpotWindow.wm_title( 'icheck' )
	
	frm = Repr( tt , 0 , r , path_movies = path_movies , path_movie = path_movie , master = SpotWindow , cmap = cmap , buffer_frames = buffer_frames , offset = offset , marker = marker , markersize = markersize , saturation = saturation)
	
	frm.initiate()

	ax = frm.render()

	frm.canvas.get_tk_widget().pack( side = tk . TOP , fill=tk.BOTH , expand = 1 )

	# bind command controls to the SpotWindow
	SpotWindow.bind( "<Left>" , lambda event , frame = frm , increment = -1 , ax = ax : ArrowKey( event , frame , increment , ax ) )
	SpotWindow.bind( "<Shift-Left>" , lambda event , frame = frm , increment = -10 , ax = ax : ArrowKey( event , frame , increment , ax ) )
	SpotWindow.bind( "<Right>" , lambda event , frame = frm , increment = 1 , ax = ax : ArrowKey( event , frame , increment , ax ) )
	SpotWindow.bind( "<Shift-Right>" , lambda event , frame = frm , increment = 10 , ax = ax : ArrowKey( event , frame , increment , ax ) )
	SpotWindow.bind( "<Up>" , lambda event , frame = frm , path = ps , f = f , ax = ax : UpKey( event , frame , path , f , ax ) )
	SpotWindow.bind( "<Down>" , lambda event , frame = frm , path = pr , f = f , ax = ax : DownKey( event , frame , path , f , ax ) )
	SpotWindow.bind( "<BackSpace>" , lambda event , frame = frm , path_sel = ps , path_rej = pr , ax = ax : BackKey( event , frame , path_sel , path_rej , ax ) )
	SpotWindow.bind( "-" , lambda event , frame = frm , increment = 1 , ax = ax : ZoomOut( event , frame , increment , ax ) )
	SpotWindow.bind( "+" , lambda event , frame = frm , increment = -1 , ax = ax : ZoomIn( event , frame , increment , ax ) )
	SpotWindow.bind( "<s>" , lambda event , frame = frm , increment = 0.05 , ax = ax : SaturateKey( event , frame , increment , ax ) )
	SpotWindow.bind( "<d>" , lambda event , frame = frm , increment = -0.05 , ax = ax : SaturateKey( event , frame , increment , ax ) )
	
	SpotWindow.mainloop()
