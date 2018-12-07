# coding=utf-8
#
# hypothesis_callables: A callable generator extension for the hypothesis lib.
# Copyright (C) 2018 Ruby Allison Rose
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
# USA
#

from __future__ import division, print_function, absolute_import

import hypothesis.strategies as hs
from hypothesis.errors import InvalidArgument
from hypothesis.searchstrategy import check_strategy
from hypothesis.internal.coverage import check_function
from hypothesis.searchstrategy.types import _global_strategy_lookup
from hypothesis.internal.validation import (
	check_type, check_valid_size, check_valid_interval, check_valid_integer
)
from hypothesis.internal.compat import (
	PY3, text_type, ceil, floor, getfullargspec
)

from collections import Iterable
import re as re

__all__ = [
	"classes",
	"functions",
	"methods",
	"classmethods",
	"staticmethods",
	#"callables",
	#"parameters"
]

@check_function
def _check_callable(arg, name=''):
	if name:
		name += '='
	if not callable(arg):
		raise InvalidArgument('Expected a callable object but got %s%r \
								(type=%s)' % (name, arg, type(arg).__name__))

# NOTE:
#	Matches any alphanumeric string beginning in an alphabetic char.
# NOTE:
#	Don't allow the _supported_binding_regex to be left uncompiled,
#	if you can't find a way to ensure it's compiled before the strategies get
#	it, leave this code block in each them.
#
#	if not hasattr(binding_regex, 'pattern'):
#		# this has to be done later anyway inside the binding generator,
#		# might as well do it now to make things a little faster.
#		binding_regex = re.compile(binding_regex)
#
# BUG: 11-14-2018 m3tior
#	While looking for a problem in the test_manual_child_binding_assignment
#	I discovered a pottential issue in the exec() function call. When assigning
#	class children preceeded by two underscore characters: for some reason
#	the class name preceeded with one underscore gets appended to the front
#	of the child name.
#
#	I'm going to look into the latest Python sources for this issue (2.7 & 3.7)
#	as well as the Python PEPs to see if I can find some specification on it.
#	Maybe it's not actually a bug? I don't know yet. For now I'm leaving this
#	as a warning to all users of this library and as an educational example
#	of what a real bug looks like. This isn't my fault (I think, need PEPs);
#	hence it's a bug and not user error. :P
#
#	In case you're wondering my current Python version is 3.5.2
#
#	I've applied a bug fix for the issue; Unfortunately function names
#	can no longer start with two successive underscore characters...
#	Ugh :( I know, that sucks for now :P.
#	Hopefully this is a bug and I can work it out.
_supported_binding_regex = re.compile(r'^(_?[a-zA-Z]+[0-9_]+|(_[0-9]+[a-zA-Z_]+)){1,5}\Z')
"""DOCUMENT ME!!!"""
#_get_supported_binding_regex = lambda : sbr = _supported_binding_regex; \
#	return sbr if hasattr(sbr, 'pattern') else re.compile(sbr)

def _phony_callable(*args, **kwargs):
	"""DOCUMENT ME!!!"""
	return (args, kwargs)

def strategies():
	"""DOCUMENT ME!!!"""
	return one_of(_global_strategy_lookup.items())

# TODO:
#	*Possibly add automatic generation of children on unassigned children*
#	*Possibly add automatic generation of ancestors on unnasigned inherits*
#	*Add ability to have multiple random children be bound to the same object*
@hs.composite
def classes(draw, inherits=None, children=None):
	"""DOCUMENT ME!!!"""
	# double check types because insurance :P (and hypothesis standards lol)
	check_type(list, inherits, 'inherits')
	check_type(dict, children, 'children')

	if children is None:

	else:
		# preallocated memory pool for optimized access times.
		static = lambda: [None for child in children] if children is not None

		members = static() # for holding our generated bindings / "cast"
		lost_members = [] # for those who don't already know their place.
		tallent = static() # the skills of our cast members! Their values...

		# This is some really funky syntax python (*-*) enumerate my soul
		for location, (key, value) in enumerate(children.items()):
			# Don't forget to make sure our children's values are strategies
			# before we waste any resources on generating and ordering them.
			check_strategy(value, name="value at key '%s' in children" % (key))

			if isinstance(key, int): # anon
				lost_members.append(location)
			elif _supported_binding_regex.match(key):
				members[location] = key
			else:
				raise InvalidArgument("child's binding at index: %i, \
					does not match binding requirements" % (index))

			# Wait to generate our children after sorting micro optimization
			tallent[location] = draw(value)

		map_count = len(lost_members)
		maps = draw(hs.lists( # for those who need directions
			hs.from_regex(_supported_binding_regex),
			min_size=map_count,
			max_size=map_count,
			unique = True,
		))

		for long, lat in enumerate(lost_members):
			members[lat] = maps[long]

	#NOTE:
	#	While I found it easy to tell myself that I could optimize things a
	#	little by drawing the act_name with the generated variable names;
	#	because the generated variable names are unique, this would mean
	#	the act_name has no chance in having a child with the same name,
	#	which would unfortunately be bad for falsification. (;-;)
	act_name = draw(hs.from_regex(_supported_binding_regex))
	stage = ["pass"] if len(members) < 1 else \
		["%s=tallent[%r]" % (name, chord) for chord, name in enumerate(members)]
	act = "".join(["class ",act_name,"(*inherits):\n\t","\n\t".join( stage )])

	exec(act, locals())

	return locals()[act_name]

# I really never thought I'd be testing variable function inputs at any point in my life...
@hs.composite
def functions(draw,
		min_argc = None, # int
		max_argc = None, # int
		manual_argument_bindings = None, # {} dict
		manual_keyword_bindings = None, # {} dict
		body = _phony_callable,
		decorators = None, # [] list
		kwarginit = hs.nothing(),
	):
	"""DOCUMENT ME!!!"""

	# Replicates check_valid_sizes logic but with correct variable names
	check_valid_size(min_argc, 'min_argc')
	check_valid_size(max_argc, 'max_argc')
	check_valid_interval(min_argc, max_argc, 'min_argc', 'max_argc')

	min_argc = None if min_argc is None else ceil(min_argc)
	max_argc = None if max_argc is None else floor(max_argc)

	check_strategy(kwarginit, name="kwarginit")

	if decorators is not None:
		check_type(list, decorators, 'decorators')
		for index, d in enumerate(decorators):
			_check_callable(d, name="iteration %r in 'decorators'" % (index))

	_check_callable(body, name="body")

	#if not hasattr(binding_regex, 'pattern'):
	#	# this has to be done later anyway inside the binding generator,
	#	# might as well do it now to make things a little faster.
	#	binding_regex = re.compile(binding_regex)

	argb = draw(hs.lists(
		hs.from_regex(binding_regex),
		min_size=min_argc,
		max_size=max_argc,
		unique=True,
	))
	argc = len(argb)

	if kwarginit is not hs.nothing():
		# generate keyword inital values and bindings
		kwargv = draw(kwarginit)
		kwargc = len(kwargv)
		kwargb = draw(hs.lists(
			hs.from_regex(binding_regex),
			min_size=kwargc,
			max_size=kwargc,
			unique=True,
			unique_by= lambda x: x not in argb.keys()
		))
	else:
		kwargc = 0
		kwargb = []
		kwargv = []

	spec = getfullargspec(body)
	if (spec.varargs is None and spec.varkw is None):
		#(min_argc is not None and min_argc < len(spc.args)) or \
		#(max_argc is not None and max_argc > len(spc.args)) or \
		# NOTE:
		#	can't validate signature for kwargs so we're gonna require the
		#	wrapper function contain both varargs and varkw just to be safe.
		raise InvalidArgument(
			"function body %s cannot support generated argument range" % (body)
		)

	if manual_argument_bindings is not None:
		for key, value in manual_argument_bindings.items():
			check_type(int, key, name="")
			#if not isinstance(int, key):
			#	raise InvalidArgument(
			#		"binding dictionarys expect keys to be integers but got: \
			#		%s (type=%s)" %(key, type(key).__name__)
			#	)

			check_type(text_type, value, name="")
			#if not isinstance(text_type, value):
			#	raise InvalidArgument(
			#		"binding dictionarys expect values to be strings but got: \
			#		%s (type=%s)" %(value, type(value).__name__)
			#	)

			if not binding_regex.match(binding):
				raise InvalidArgument(
					"binding dictionary value at '%s' does not match binding \
					regex. '%s' not found in (regex=%s)"
					%(key, value, binding_regex)
				)

			if key <= argb: argb[key] = value

	if manual_keyword_bindings is not None:
		for key, value in manual_keyword_bindings.items():
			check_type(int, key, name="")
			#if not isinstance(int, key):
			#	raise InvalidArgument(
			#		"binding dictionarys expect keys to be integers but got: \
			#		%s (type=%s)" %(key, type(key).__name__)
			#	)

			check_type(text_type, value, name="")
			#if not isinstance(text_type, value):
			#	raise InvalidArgument(
			#		"binding dictionarys expect values to be strings but got: \
			#		%s (type=%s)" %(value, type(value).__name__)
			#	)

			if not binding_regex.match(binding):
				raise InvalidArgument(
					"binding dictionary value at %s does not match binding \
					regex. '%s' not found in (regex=%s)"
					%(key, value, binding_regex)
				)

			if key <= kwargb: kwargb[key] = value

	name = draw(hs.from_regex(binding_regex))

	exec ("".join([
		# Define function using generated name
		'def ',name,'(',
			",".join(argb),
			",".join([ kwarg + "=kwargv["+str(index)+"]," \
				# zip up the keyword arguments and assign them their init values.
				for index, kwarg in enumerate(kwargb)]),
		'): ',

		# Execute function body and return elements
		'return body(',
			",".join(argb),
			",".join([ kwarg+"="+kwarg for kwarg in kwargb]),
		')'
	]), locals())

	function = locals()[name]

	if decorators is not None:
		for d in reverse(decorators): function = d(function)

	return function

@hs.composite
def methods(draw,
		min_argc = None, # int
		max_argc = None, # int
		manual_argument_bindings = None, # {}
		manual_keyword_bindings = None, # {}
		body = _phony_callable,
		decorators = None, # [] itterable
		kwarginit = hs.nothing(),
		parent = classes()
	):
	"""DOCUMENT ME!!!"""
	check_strategy(parent, name="parent")
	check_type(dict, manual_argument_bindings, name="manual_argument_bindings")

	min_argc = 0 if min_argc is None \
		else check_valid_integer(min_argc, name="min_argc")
	max_argc = 0 if max_argc is None \
		else check_valid_integer(max_argc, name="max_argc")

	arguments = {0: "self"}
	arguments.update(manual_argument_bindings)

	container = draw(parent)
	method_body = draw(functions(
		binding_regex = binding_regex,
		min_argc = min_argc + 1, max_argc = max_argc + 1,
		manual_argument_bindings = arguments,
		manual_keyword_bindings = manual_keyword_bindings, body = body,
		decorators = decorators, kwarginit = kwarginit
	))
	setattr(container, method_body.__name__, method_body)

	def method_wrapper(*args, **kwargs):
		exec("container."+ method_body.__name__ +"(*args, **kwargs)", locals())

	return method_wrapper

@hs.composite
def classmethods(draw,
		min_argc = None, # int
		max_argc = None, # int
		manual_argument_bindings = None, # {}
		manual_keyword_bindings = None, # {}
		body = _phony_callable,
		decorators = None, # [] itterable
		kwarginit = hs.nothing(),
		parent = classes()
	):
	"""DOCUMENT ME!!!"""
	check_strategy(parent, name="parent")
	check_type(dict, manual_argument_bindings, name="manual_argument_bindings")
	check_type(list, decorators, name="decorators")

	min_argc = 0 if min_argc is None \
		else check_valid_integer(min_argc, name="min_argc")
	max_argc = 0 if max_argc is None \
		else check_valid_integer(max_argc, name="max_argc")

	arguments = {0: "cls"} # designation of defaults must be preemptive
	arguments.update(manual_argument_bindings) # because this is override

	# classmethod designation must be first in the series function properly
	decorators = [classmethod, ] + decorators

	container = draw(parent)
	method_body = draw(functions(
		binding_regex = binding_regex,
		min_argc = min_argc + 1, max_argc = max_argc + 1,
		manual_argument_bindings = arguments, # enforce defaults
		manual_keyword_bindings = manual_keyword_bindings, body = body,
		decorators = decorators, kwarginit = kwarginit
	))
	setattr(container, method_body.__name__, method_body)

	def method_wrapper(*args, **kwargs):
		exec("container."+ method_body.__name__ +"(*args, **kwargs)", locals())

	return method_wrapper

@hs.composite
def staticmethods(draw,
		min_argc = None, # int
		max_argc = None, # int
		manual_argument_bindings = None, # {}
		manual_keyword_bindings = None, # {}
		body = _phony_callable,
		decorators = None, # [] itterable
		kwarginit = hs.nothing(),
		parent = classes()
	):
	"""DOCUMENT ME!!!"""
	check_strategy(parent, name="parent")
	check_type(list, decorators, name="decorators")

	# primary decorator must be first in the series function properly
	decorators = [staticmethod, ] + decorators

	container = draw(parent)
	method_body = draw(functions(
		binding_regex = binding_regex,
		min_argc = min_argc, max_argc = max_argc,
		manual_argument_bindings = arguments,
		manual_keyword_bindings = manual_keyword_bindings, body = body,
		decorators = decorators, kwarginit = kwarginit
	))
	setattr(container, method_body.__name__, method_body)

	def method_wrapper(*args, **kwargs):
		exec("container."+ method_body.__name__ +"(*args, **kwargs)", locals())

	return method_wrapper

#@hs.composite
#def callables(draw,
#		min_argc = None, # int
#		max_argc = None, # int
#		manual_argument_bindings = None, # {}
#		manual_keyword_bindings = None, # {}
#		body = _phony_callable,
#		decorators = None, # [] itterable
#		kwarginit = hs.nothing(),
#		functions = True,
#		methods = True,
#		classmethods = True,
#		staticmethods = True
#	):
#	"""DOCUMENT ME!!!"""
#
#	check_
#
#	type = draw(one_of())
