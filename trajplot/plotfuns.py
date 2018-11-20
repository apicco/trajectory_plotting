from numpy import transpose, concatenate
from matplotlib.patches import Polygon

def myplot( obj , t , what , label , col , x0 = 0 , t0 = 0 , x_scale = 1 , lw = 1.5 , ls = '-' , which_coord = 0 ) :

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

	lower_error_boundary =  transpose( [ t.t() - t0 , x - 1.96 * x_err ] )
	upper_error_boundary =  transpose( [ t.t() - t0 , x + 1.96 * x_err ] )
	error_boundary = concatenate( ( lower_error_boundary , upper_error_boundary[ ::-1 ] ) )

	error_area = Polygon( error_boundary , True , color = col , alpha = 0.3 )
	obj.add_patch( error_area )

	#plot the trajectory
	obj.plot( t.t() - t0 , x , linewidth = lw , linestyle = ls , color = col , label = label )


