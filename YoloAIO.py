from typing import Iterable, Union, List

def type_assert( v: object, v_name: str, expected_type: Union[type, Iterable[type]], prefix: str, accept_none: bool = False ) -> None:
	''' Makes sure a variable is of given type(s).

	Raises AssertionError if `v` has type not covered by `expected_type`.

	`prefix` : A string prefix for the message the raised error may display, useful for knowing which
			   part of the code generated the error. eg: 'MyClass.method2'

	`accept_none` : if True, accepts a `None` value for `v` no matter the expected type(s). 
					Alternatively, include `type(None)` to the expected type list.
	'''
	# Case 1 : accept None value
	if accept_none is True and v is None:
		return

	error_txt = f"{prefix}: expected received '{v_name}' to be a {expected_type} object, received '{type(v)}'"
	# Case 2 : expected_type is a list/set => recursion
	if isinstance( expected_type, set ) or isinstance( expected_type, list ):
		for e_t in expected_type:
			try:
				type_assert( v, v_name, e_t, prefix, accept_none )
				return
			except AssertionError:
				continue
		raise AssertionError( error_txt )
	
	# Default case : check type
	assert isinstance( v, expected_type ), error_txt


def ordinal_expr( idx ):
	# maps [0-26] index to [x-z,a-w], to fit core.std.Expr load operator convention
	assert idx in range(0,27)
	_ord = idx + 120 if idx < 3 else idx + 94
	return chr(_ord)


class Coordinate:
	def __init__( self, x, y ):
		self.x = x
		self.y = y


class Color:
	NON_RGB_COLORS = { 'white', 'black' }
	RGB = [ 'R', 'G', 'B' ]

	def __init__( self, color: Union[str,List[int]], SeuilI: int = 200, SeuilO: int = 90, marginRel: float = 0.25, marginAbs: int = 25 ):
		assert isinstance(color, list) or color in self.NON_RGB_COLORS, f"Color.init: ERROR: color {color} not in {self.ACCEPTED_COLORS} !"
		type_assert( 
			v=SeuilI, 
			v_name='SeuilI', 
			expected_type=int,
			prefix='Color.init'
		)
		type_assert( 
			v=SeuilO, 
			v_name='SeuilO', 
			expected_type=int,
			prefix='Color.init'
		)
		assert marginRel <  0.5 and marginRel >= 0
		assert marginAbs <= 100 and marginRel >= 0
		
		self.color = color
		self.SeuilI = SeuilI
		self.SeuilO = SeuilO
		self.marginRel = marginRel
		self.marginAbs = marginAbs


	def __str__( self ):
		return f"<Color: color={str(self.color)}, SeuilI={self.SeuilI},\n SeuilO={self.SeuilO}, marginRel={self.marginRel}, marginAbs={self.marginAbs} >"
		
	# def __eq__( self, other ):
	# 	if type(other)!=str or (not(other in self.ACCEPTED_COLORS)):
	# 		raise NotImplementedError(f"Color.__eq__: cannot handle other={other}")
	# 	return self.color == other

	@property
	def is_rgb( self ):
		return isinstance(self.color, list)

	def __color_range( self, plane ):
		assert plane in { 0, 1, 2 } and isinstance(self.color, list)
		intensity = self.color[plane]
		_min = int(max(intensity * (1 - self.marginRel) - self.marginAbs,   0))
		_max = int(min(intensity * (1 + self.marginRel) + self.marginAbs, 255))
		return [ _min, _max ]

	def color_range( self ):
		return '\n'.join( [ 
			self.RGB[plane] + ': ' +str(self.__color_range(plane))
			for plane in range(3)
		] )
		
	def color_isolation_expression( self ):
		def plane_expr( plane ):
			_min, _max = self.__color_range( plane )
			plane_id = ordinal_expr( plane )
			return f"{plane_id} {_min} >= {plane_id} {_max} <= and"
	
		expr = [ plane_expr( i ) for i in range(3) ]
		return f"{expr[0]} {expr[1]} and {expr[2]} and 255 0 ?"
		


def makeMOD2( x: int ) -> int:
	# ensures x is even (mod 2)
	if not isinstance( x, int ):
		x = int(x)
	return x+1 if x%2==1 else x



