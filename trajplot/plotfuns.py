from trajalign.traj import Traj
from trajalign.average import unified_start, unified_end
from numpy import transpose, concatenate
from matplotlib.patches import Polygon
from matplotlib import pyplot as plt
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

def myplot( obj , t , what , label , col , x0 = 0 , t0 = 0 , x_scale = 1 , lw = 1.5 , ls = '-' , which_coord = 0 , unify_start_end = True ) :

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

		t.start( unified_start( t ) )
		t.end( unified_end( t ) )

	x , x_err = get_values_from_track( t , what , x0 , x_scale , which_coord )

	lower_error_boundary =  transpose( [ t.t() - t0 , x - 1.96 * x_err ] )
	upper_error_boundary =  transpose( [ t.t() - t0 , x + 1.96 * x_err ] )
	error_boundary = concatenate( ( lower_error_boundary , upper_error_boundary[ ::-1 ] ) )

	error_area = Polygon( error_boundary , True , color = col , alpha = 0.3 )
	obj.add_patch( error_area )

	#plot the trajectory
	obj.plot( t.t() - t0 , x , linewidth = lw , linestyle = ls , color = col , label = label )

def plot_average( obj , t , what , label , col , x0 = 0 , t0 = 0 , x_scale = 1 , fg_lw = 1.5 , which_coord = 0 , unify_start_end = True ) :

	tt = cp.deepcopy( t ) 
	bg_lw = fg_lw * 1.5

	if unify_start_end :

		tt.start( unified_start( t ) )
		tt.end( unified_end( t ) )

	x , x_err = get_values_from_track( tt , what , x0 , x_scale , which_coord )

	obj.plot( tt.t() - t0 , x , linewidth = bg_lw , color = "#000000" )
	obj.plot( tt.t() - t0 , x , linewidth = fg_lw , color = col , label = label )
	
	obj.plot( tt.t() - t0 , x + 1.96 * x_err , linewidth = bg_lw * 0.5 , color = "#000000" )
	obj.plot( tt.t() - t0 , x + 1.96 * x_err , linewidth = fg_lw * 0.5 , linestyle = ( 0 , ( 5 , 5 ) ) , color = col )

	obj.plot( tt.t() - t0 , x - 1.96 * x_err , linewidth = bg_lw * 0.5 , color = "#000000" )
	obj.plot( tt.t() - t0 , x - 1.96 * x_err , linewidth = fg_lw * 0.5 , linestyle = ( 0 , ( 5 , 5 ) ) , color = col )
	
def plot_raw( obj , path , what , label , which_coord = 0 , x0 = 0 , t0 = 0 ,  x_scale = 1 , average_trajectory = None , l_col = "#000000" , d_col = "#FF0000" , lw = 2 , ls = '-' , ls_err = ':' , l_alpha = 1 , d_alpha = 0.15 , plot_average_trajectory = True , flip_around = False , unify_start_end = True , trajectory_number_in_legend = False ) :

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

		plot_average( obj , average_trajectory , what=what , label=label_average + "average" , col=l_col , x0=x0 , t0=t0 , x_scale=x_scale , which_coord=which_coord , fg_lw = lw , unify_start_end = unify_start_end )

def trajectories_on_movie( movie_path , output_path , tls , cmaps , scale = np.nan , scale_unit = '' , shift = [ 0 , 0 ] , figsize = ( 10, 8 ) , movie_cmap = 'gray' , marker_size = 3 , line_width = 1 ) : # tls = trajectory_lists , cmaps = colormaps )
	
	def plot_traj( tt , f , cmap , scale , shift , ms , lw ) :

		l = len( tt ) 
		for i in range( l ) :

			c = cmap( i / l )

			t = tt [ i ]

			if ( f >= t.frames()[ 0 ] ) & ( f <= t.frames()[ -1 ] ) :

				#select the part of the trajectory to be drawn on the movie
				selected_frames = list( range( t.frames()[ 0 ] , f + 1 ) )
				sel = [ i for i in range( len( selected_frames ) ) if selected_frames[ i ] in t.frames() ]
				u = t.extract( sel )

				if scale == scale : 

					plt.plot( u.coord()[ 1 ] * scale + shift[ 0 ] , u.coord()[ 0 ] * scale - shift[ 1 ] , 'o' , color = c , markersize = ms )
					plt.plot( u.coord()[ 1 ] * scale + shift[ 0 ] , u.coord()[ 0 ] * scale - shift[ 1 ] , '-' , color = c , linewidth = lw )
				else : 

					plt.plot( u.coord()[ 1 ] + shift[ 0 ] , u.coord()[ 0 ] - shift[ 1 ] , 'o' , color = c , markersize = ms )
					plt.plot( u.coord()[ 1 ] + shift[ 0 ] , u.coord()[ 0 ] - shift[ 1 ] , '-' , color = c , linewidth = lw )

	#--------------------------------------------------

	if ( scale == scale ) & ( len( scale_unit ) == 0 ) :

		print( 'define the unit after the application of the scaling factor ')

	if len( tls ) == len( cmaps ) :
		
		im = tiff.imread( movie_path )
		
		for f in range( len( im ) ) :

			frameName = output_path + 'frame' + '%03dr' % f 
			output = plt.figure( 1 , figsize = figsize )

			plt.imshow( im[ f , : , : ] , cmap = movie_cmap )
			
			for i in range( len( tls ) ) :

				plot_traj( tls[ i ] , f , scale , shift , cmap = cmaps[ i ] , ms = marker_size , lw = line_width )

			if not scale == scale :

				plt.xlabel( 'Pixel' )
				plt.ylabel( 'Pixel' )

			else :
				
				plt.xlabel( scale_unit )
				plt.ylable( scale_unit )

			plt.savefig( output_path + frameName )
	else :

		print( 'Specify as many cmaps as there are trajectory lists' )
