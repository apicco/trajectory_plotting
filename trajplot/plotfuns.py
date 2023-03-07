from trajalign.traj import Traj
from trajalign.average import unified_start, unified_end
from numpy import transpose, concatenate
from matplotlib.patches import Polygon
from matplotlib import pyplot as plt
from matplotlib import cm
import tifffile as tiff
import numpy as np
import os
import re
import copy as cp

def get_values_from_track( t , what , x0 , x_scale , which_coord ) :
	
	x = getattr( t , '_' + what )
	x_err = getattr( t , '_' + what + '_err' )

	if x.ndim > 1 : 

		#then the attribute has more than one dimention, which means it is coord and we are interested
		#only in which_coord.
		
		x = ( x[ which_coord ] - x0 ) * x_scale
		x_err = x_err[ which_coord ] * x_scale

	else :

		x = ( x - x0 ) * x_scale
		x_err = x_err * x_scale

	return x , x_err 

def myplot( obj , t , what , label , col , x0 = 0 , t0 = 0 , x_scale = 1 , lw = 1.5 , ls = '-' , which_coord = 0 , unify_start_end = True , add_CI = True ) :

	"""
	myplot( obj , t , what , label , col , lw = 1.5 , ls = '-' ) : plots
	the attribute 'what' of the trajectory 't' in the matplotlib object 'obj'. It is 
	possible to define a string label with 'label', a color with 'col', the line width 
	with 'lw' ( default is lw = 1.5 ), and the linestyle with 'ls' ( default is ls = '-').
	'ls' can have any of the following arguments:
		'-' solid line
		':' dotted line
		'--' dashed line
		'-.' dash/dotted line
	"""

	if unify_start_end :

		t.start( unified_start( t , add_CI = add_CI ) )
		t.end( unified_end( t , add_CI = add_CI ) )

	x , x_err = get_values_from_track( t , what , x0 , x_scale , which_coord )

	lower_error_boundary =  transpose( [ t.t() - t0 , x - 1.96 * x_err ] )
	upper_error_boundary =  transpose( [ t.t() - t0 , x + 1.96 * x_err ] )
	error_boundary = concatenate( ( lower_error_boundary , upper_error_boundary[ ::-1 ] ) )

	error_area = Polygon( error_boundary , True , color = col , alpha = 0.3 )
	obj.add_patch( error_area )

	#plot the trajectory
	obj.plot( t.t() - t0 , x , linewidth = lw , linestyle = ls , color = col , label = label )

def plot_average( obj , t , what , label , col , x0 = 0 , t0 = 0 , x_scale = 1 , fg_lw = 1.5 , which_coord = 0 , unify_start_end = True , norm_f = True ) :

	tt = cp.deepcopy( t ) 
	bg_lw = fg_lw * 1.5

	if unify_start_end :

		tt.start( unified_start( t ) )
		tt.end( unified_end( t ) )

	if norm_f :

		tt.norm_f()

	x , x_err = get_values_from_track( tt , what , x0 , x_scale , which_coord )

	obj.plot( tt.t() - t0 , x , linewidth = bg_lw , color = "#000000" )
	obj.plot( tt.t() - t0 , x , linewidth = fg_lw , color = col , label = label )
	
	obj.plot( tt.t() - t0 , x + 1.96 * x_err , linewidth = bg_lw * 0.5 , color = "#000000" )
	obj.plot( tt.t() - t0 , x + 1.96 * x_err , linewidth = fg_lw * 0.5 , linestyle = ( 0 , ( 5 , 5 ) ) , color = col )

	obj.plot( tt.t() - t0 , x - 1.96 * x_err , linewidth = bg_lw * 0.5 , color = "#000000" )
	obj.plot( tt.t() - t0 , x - 1.96 * x_err , linewidth = fg_lw * 0.5 , linestyle = ( 0 , ( 5 , 5 ) ) , color = col )
	
def plot_raw( obj , path , what , label , which_coord = 0 , x0 = 0 , t0 = 0 ,  x_scale = 1 , average_trajectory = None , l_col = "#000000" , d_col = "#FF0000" , lw = 2 , ls = '-' , ls_err = ':' , l_alpha = 1 , d_alpha = 0.15 , plot_average_trajectory = True , flip_around = False , unify_start_end = True , trajectory_number_in_legend = False , norm_f = True ) :

	# if x0 is nan and there is an average trajectroy,
	# then define x0 as the x[0] of the average trajectory
	if x0 != x0 : # if x0 is not a number, estimate if from the average trajectory start position
	
		if average_trajectory :
			
			tx = cp.deepcopy( average_trajectory ) 
		
			if unify_start_end :
		
				tx.start( unified_start( tx ) )
				tx.end( unified_end( tx ) )
	
			x0 = tx.coord()[ which_coord ][ 0 ]

		else :

			raise AttributeError( 'plat_raw error: You need and average trajectory to estimate a x0, if x0 input was set to nan' )

	if len( label ) == 0 :

		label_raw = ''
		label_average = ''

	else :

		label_raw = label + '\n'
		label_average = label + '\n'

	all_files = os.listdir( path )
	files = [ f for f in all_files if ( 'alignment_precision' not in f ) & ( 'txt' in f ) ]

	first_fl = True
	for fl in files :

		print( 'load raw trajectory: ' + fl )

		t = Traj()
		t.load( path + '/' + fl )

		if flip_around : 
			t.rotate( np.pi )
		
		x = getattr( t , '_' + what )
	
		if x.ndim > 1 : 
	
			#then the attribute has more than one dimention, which means it is coord and we are interested
			#only in which_coord.

			if average_trajectory :

				try :

					at_floats = []
					at_elements = [ f for f in re.split( '\[|\]|,' , average_trajectory.annotations()[ 'alignment_translation' ] ) ]
						
					for e in at_elements :
	
						try :
	
							at_floats.append( float( e ) )
	
						except :
	
							None
		
					cm_floats = []
					cm_elements = [ f for f in re.split( '\[|\]| ' , average_trajectory.annotations()[ 'starting_center_mass' ] ) ]   
				
					for e in cm_elements :
	
						try :
	
							cm_floats.append( float( e ) )
	
						except :
	
							None
	
					x = ( x[ which_coord ] -  cm_floats[ which_coord ] + at_floats[ which_coord ] - x0 ) * x_scale
					
				except :

					x = ( x[ which_coord ] - x0 ) * x_scale

			
			else :

				x = ( x[ which_coord ] - x0 ) * x_scale

		else :
	
			x = ( x - x0 ) * x_scale

		try :

			lag_elements = [ f for f in re.split( '\[|\]| ' , average_trajectory.annotations()[ 'alignment_lag' ] ) ]   
					
			for e in lag_elements :
		
				try :
		
					lag_float = float( e )
		
				except :
		
					None

		except :

			lag_float = 0

		if first_fl : 	
			
			if trajectory_number_in_legend : 
				
				obj.plot( t.t() - t0 + lag_float , x , 'o' , color = d_col , alpha = d_alpha , label = label_raw + 'n = ' + str( len( files ) ) + ' raw trajectories' )

			else : 
				
				obj.plot( t.t() - t0 + lag_float , x , 'o' , color = d_col , alpha = d_alpha , label = label_raw + 'raw trajectories' )
			
			first_fl = False
		else :

			obj.plot( t.t() - t0 + lag_float , x , 'o' , color = d_col , alpha = d_alpha )

	if ( average_trajectory != None ) & plot_average_trajectory :

		plot_average( obj , average_trajectory , what=what , label=label_average + "average" , col=l_col , x0=x0 , t0=t0 , x_scale=x_scale , which_coord=which_coord , fg_lw = lw , unify_start_end = unify_start_end , norm_f = norm_f )

def trajectories_on_movie( movie_path , output_path , tls , cmaps , scale = np.nan , scale_unit = '' , shift = [ 0 , 0 ] , figsize = ( 10, 8 ) , movie_cmap = 'gray' , marker_size = 3 , line_width = 1 ) : # tls = trajectory_lists , cmaps = colormaps )
	
	def plot_traj( tt , f , cmap , shift , ms , lw ) :

		l = len( tt ) 
		for i in range( l ) :

			c = cm.get_cmap( cmap )

			t = tt [ i ]

			if ( f >= t.frames()[ 0 ] ) & ( f <= t.frames()[ -1 ] ) :

				#select the part of the trajectory to be drawn on the movie
				selected_frames = list( range( t.frames()[ 0 ] , f + 1 ) )
				sel = [ i for i in range( len( selected_frames ) ) if selected_frames[ i ] in t.frames() ]
				u = t.extract( sel )

				plt.plot( u.coord()[ 1 ] + shift[ 0 ] , u.coord()[ 0 ] - shift[ 1 ] , 'o' , color = c( i / l ) , markersize = ms )
				plt.plot( u.coord()[ 1 ] + shift[ 0 ] , u.coord()[ 0 ] - shift[ 1 ] , '-' , color = c( i / l ) , linewidth = lw )

	#--------------------------------------------------

	if ( scale == scale ) & ( len( scale_unit ) == 0 ) :

		print( ' define the unit after the application of the scaling factor ')

	if len( tls ) == len( cmaps ) :
		
		im = tiff.imread( movie_path )
		
		for f in range( len( im ) ) :

			frameName = output_path + 'frame' + '%03d.png' % f 
			output = plt.figure( 1 , figsize = figsize )

			plt.imshow( im[ f , : , : ] , cmap = movie_cmap )
			
			for i in range( len( tls ) ) :

				plot_traj( tls[ i ] , f , cmap = cmaps[ i ] , shift = shift , ms = marker_size , lw = line_width )

			if not scale == scale :

				plt.xlabel( 'Pixel' )
				plt.ylabel( 'Pixel' )

			else :

				xo = [ i for i in range( 0 , im.shape[ 2 ] , 100 ) ]
				plt.xticks( xo , [ scale * i for i in xo ] )
				yo = [ i for i in range( 0 , im.shape[ 1 ] , 100 ) ]
				plt.yticks( yo , [ scale * i for i in yo ] )
				plt.xlabel( scale_unit )
				plt.ylabel( scale_unit )

			print( frameName ) 
			plt.savefig( frameName )
			plt.close()

	else :

		print( 'Specify as many cmaps as there are trajectory lists' )


def show_on_movie( tt , im , path_output , col , mstyl , figsize = ( 8 , 7 ) , ms = 20 , lw = 3 , alpha = 0.5 , ID = False , ID_shift = {} , ID_length = np.nan ) :

	def plot_traj( t , f , c , mstyl , ms , lw , a , ID , ID_shift = [ 4 , 4 ] , ID_length = np.nan ) :
	
		shift = 0# correct PT shift
	
		if ( f + 1 >= t.frames()[ 0 ] ) & ( f + 1 <= t.frames()[ -1 ] ) :

			#selected frames
			sel = [ i for i in range( len( t ) ) if t.frames()[ i ] <= f + 1 ]
	
			u = t.extract( sel )

			plt.plot( u.coord()[ 1 ][ -1 ] + shift , u.coord()[ 0 ][ -1 ] + shift , mstyl , color = c , markersize = ms , markerfacecolor = 'none' , alpha = a )
			plt.plot( u.coord()[ 1 ] + shift, u.coord()[ 0 ] + shift , '-' , color = c , linewidth = lw , alpha = a )

			if ( ID & ( u.coord()[ 1 ][ -1 ] == u.coord()[ 1 ][ -1 ] ) & ( u.coord()[ 0 ][ -1 ] == u.coord()[ 0 ][ -1 ] ) ) :

				ID_text = t.annotations()[ 'file' ]

				if ID_length == ID_length :
					
					ID_text = ID_text[ - ( 4 + ID_length ) : -4 ]

				plt.text( x = u.coord()[ 1 ][ -1 ] + shift + ID_shift[ 0 ] , y = u.coord()[ 0 ][ -1 ] + shift + ID_shift[ 1 ] , s = ID_text , color = c )

	# -------------------------

	l = len( tt )

	if ID :
		
		if ( len( ID_shift ) > 0 ) & ( isinstance( ID_shift , dict ) ) :
		
			if  l != len( ID_shift ) :
		
				raise TypeError( 'the ID_shift dictionary and the tt dictionary  must have the same length ' )
		else : 

			if 2 != len( ID_shift) :
				
				raise TypeError( 'the ID_shift list  must have only two values, one for the shift along x, the other for the shift along y ' )

	if l != len( col ) :

		raise TypeError( 'the tt dictionary and the list col must have the same length ' )

	if not os.path.exists( path_output ) :

		os.makedirs( path_output )

	for f in range( 0 , len( im ) ) :

		frameName = path_output + '/' + 'frame' + '%04d' % f

		plt.figure( 1 , figsize = figsize )
		plt.axes().set_aspect( 'equal' )

		plt.imshow( im[ f , : , : ] , cmap = 'gray' )
		
		for i in range( l ) :
		
			#load the trajectory list
			k = list( tt.keys() )[ i ]
			tl = tt[ k ]

			for t in tl :

				#define the correct ID shift if there are multiple trajectory lists and plot
				if ID :

					if isinstance( ID_shift , dict )  :
						ids = ID_shift[ k ]
					else :
						ids = ID_shift
				
					plot_traj( t , f , c = col[ i ] , mstyl = mstyl[ i ] , ms = ms , lw = lw , a = alpha , ID = ID , ID_shift = ids , ID_length = ID_length ) 
				
				else :

					plot_traj( t , f , c = col[ i ] , mstyl = mstyl[ i ] , ms = ms , lw = lw , a = alpha ) 

		plt.xlabel( 'Pixel' )
		plt.ylabel( 'Pixel' )
		plt.savefig( frameName )
		plt.close()
		

def show_selected_trajectories( tt , movie_path , output_path , dataset_path = '' , n = np.nan , r = 10 , n_col = 10 ) :
	
	"""
	selected_trajectories( tt , movie_path , n = 3 , r = 10 ) show snapshots of the spots 
	from which the trajectories in the list tt were derived. The snapshots are generated from the 
	trajectory movies in movie_path using n frames equally distributed across the trajectory lifetime. 
	'r' determines the radius of the snapshot defined which will cover a region [ c - r , c + r ], where c is the centroi position, all in pixels.
	The trajectories are mapped to the right movie finding the trajectory in the traj.txt file, unless 
	the movie name is in the trajectory annotations already, using assign_datasetID
	"""

	for t in tt : 

		print( t.annotations() )

		# load the movie name, it could be that the trajectory as already 
		# the annotation 'dataset', in which case the dataset_path is not 
		# needed (default) 
		if t.annotations()[ 'dataset' ] :
			
			movie_name = t.annotations()[ 'dataset' ][ 5 : -4 ] + '.tif'
		
		elif len( dataset_path ) :
			
			t.assign_datasetID( dataset_path )
			movie_name = t.annotations()[ 'dataset' ][ 5 : -4 ] + '.tif'

		else :

			raise AttributeError( 'trajectory has no annotation dataset, and there is no dataset_path' )

		im = tiff.imread( movie_path + '/' + movie_name )

		# exctract the trajectory name, if it has a file exension that's left out
		t_name = t.annotations()[ 'file' ].split( '.' )[ 0 ]

		# if n is not defiend, n is the length of the trajectory
		if n != n : 
			n = len( t )
		# and n cannot be one otherwise n-1 denominators will diverge. 
		# Also 1 example, or a 1 element trajectory are meaningless
		if n == 1 : 
			raise AttributeError( 'n must be greather than 1, or the trajectory must have more than one datapoint' )

		# define frames and coordinates without nan
		f = [ t.frames( i ) for i in range( len( t ) ) if t.coord( i )[ 0 ] == t.coord( i )[ 0 ] ]
		x = [ t.coord( i )[ 0 ] for i in range( len( t ) ) if t.coord( i )[ 0 ] == t.coord( i )[ 0 ] ] 
		y = [ t.coord( i )[ 1 ] for i in range( len( t ) ) if t.coord( i )[ 0 ] == t.coord( i )[ 0 ]  ] 
		
		# define what is the delta-frame interval needed to show the desired number 
		# of equally spaced frames that to show the spot
		df = int( np.ceil( len( f ) / ( n ) ) )

		# select the frame numbers to plot
		sel = [ i for i in range( 0 , len( f ) , df ) ]

		# select the frames and centroid coordinates
		sel_f = [ f[ i ] for i in sel ]
		sel_x = [ int( np.round( x[ i ] ) ) for i in sel ]
		sel_y = [ int( np.round( y[ i ] ) ) for i in sel ]

		# define the number of rows in the array of subplots
		n_row = int( np.ceil( n / n_col ) )

		# plot the figure
		plt.figure( figsize = ( n_col * 5 , n_row * 4 ) )

		for i in range( len( sel_f ) ) :
			
			plt.subplot( n_row , n_col , i + 1 )
			plt.title( 'frame ' + str( sel_f[ i ] ) )
			
			# centroid
			sim =  im[ sel_f[ i ] , - r + sel_x[ i ] : sel_x[ i ] + r , - r + sel_y[ i ] : sel_y[ i ] + r ]
			plt.imshow( sim )
			i = i + 1

		plt.savefig( output_path + '/' + t_name + '.pdf' )		


