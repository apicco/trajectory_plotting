from numpy import transpose, concatenate
from matplotlib.patches import Polygon

def myplot( obj , t , what , label , col , scale = 0.5 ) :
		
	x = getattr( t , '_' + what )
	x_err = getattr( t , '_' + what + '_err' )

	if x.ndim > 1 : 
		#then the attribute has more than one dimention and we are interested
		#only in the first one.
		x = x[ 0 ]
		x_err = x_err[ 0 ]
	lower_error_boundary =  transpose( [ t.t() , x - 1.96 * x_err ] )
	upper_error_boundary =  transpose( [ t.t() , x + 1.96 * x_err ] )
	error_boundary = concatenate( ( lower_error_boundary , upper_error_boundary[ ::-1 ] ) )

	error_area = Polygon( error_boundary , True , color = col , alpha = 0.3 )
	obj.add_patch( error_area )

	#plot the trajectory
	obj.plot( t.t() , x , linewidth = 1.5 , color = col , label = label )


