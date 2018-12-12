# coding=utf-8
#
# hypothesis_callables: A callable generator extension for the hypothesis lib.
# Copyright (C) 2018 Ruby Allison Rose
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.
#
# END HEADER

"""MODULE DOCSTRING TODO"""


from __future__ import division, print_function, absolute_import


__author__ = "Ruby Allison Rose"
__version__ = "0.0.1"
__all__ = [
	"classes",
	"functions",
	"methods",
	"classmethods",
	"staticmethods",
	#"callables",
	#"parameters"
]


from collections import Iterable, OrderedDict
import sre_constants
import re

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

# NOTE:
#	Matches any alphanumeric string beginning in an alphabetic char.
# NOTE:
#	Don't allow the _supported_binding_regex to be left uncompiled,
#	if you can't find a way to ensure it's compiled before the strategies get
#	it, leave this code block in each of them.
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
#
# BUG: 12-08-2018 m3tior UPDATE:
#	I couldn't find anything in the PEPs, Still have yet to look into the
#	sources and docs. I'll probs check the docs first just in case I missed
#	something in there.
#
_supported_binding_regex = re.compile(
	'^(_?([a-zA-Z]_*)+[0-9_]*|(_([0-9]_*)+[a-zA-Z_]*))\Z'
)
"""str: Regex that matches all known supported variable bindings.

This is used internally for generation of all inexplicit hypothesis_callables
variable bindings. It's also the default for generated function and class names.
"""
#_get_supported_binding_regex = lambda : sbr = _supported_binding_regex; \
#	return sbr if hasattr(sbr, 'pattern') else re.compile(sbr)

def _phony_callable(*args, **kwargs):
	"""DOCUMENT ME!!!"""
	return (args, kwargs)

@check_function
def _check_callable(arg, name=''):
	if name:
		name += '='
	if not callable(arg):
		raise InvalidArgument('Expected a callable object but got %s%r \
								(type=%s)' % (name, arg, type(arg).__name__))

def _validate_bindings(draw, elements, name=""):
	"""DOCUMENT ME!!!"""

	# Use OrderedDict over regular to enforce strictness of binding position
	# because they tranlate directly to a linear memory map.
	check_type(OrderedDict, elements, name)

	# preallocated memory pool for optimized access times.
	def static(): return tuple(None for elm in elements)

	bindings = static()
	values = static()
	unknown = []

	# This is some really funky syntax python (*-*) enumerate my soul
	for pos, (key, value) in enumerate(elements.items()):
		# Don't forget to make sure our children's values are strategies
		# before we waste any resources on generating and ordering them.
		check_strategy(value, name="value at key '%s' in %s" % (key, name))

		if isinstance(key, int):
			unknown.append(pos)
		elif isinstance(key, text_type):
			if not _supported_binding_regex.match(key):
				try:
					key = draw(hs.from_regex(key))
				except(sre_constants.error):
					raise InvalidArgument(
						"Could not satisfy requirements of binding \
						'%s' at index '%i' in %s, invalid regex."
						% (key, index, name)
					)

			bindings[pos] = key
		else:
			raise InvalidArgument(
				"Expected binding at index '%d' of '%s' be int or %s, \
				but got '%r' (type=%s)"
				% (pos, name, text_type, key, type(key).__name__)
			)

		# Generate our children after sorting; micro optimization
		values[pos] = draw(value)

	unknown_bindings = len(lost_members)
	generated_bindings = draw(hs.lists(
		hs.from_regex(_supported_binding_regex),
		min_size=unknown_bindings,
		max_size=unknown_bindings,
		unique=True,
	))

	for long, lat in enumerate(unknown_bindings):
		bindings[lat] = generated_bindings[long]

	return (bindings, values)

@hs.composite
def _strategies(min_difficulty=None, max_difficulty=None):
	"""DOCUMENT ME!!!"""
	return draw(one_of(
		_global_strategy_lookup.items()[min_difficulty : max_difficulty]
	))

# TODO:
#	*Possibly add automatic generation of children on unassigned children*
#	*Possibly add automatic generation of ancestors on unnasigned inherits*
#	*Add ability to have multiple random children be bound to the same object*
@hs.composite
def classes(draw, name=None, inherits=None, children=None):
	"""DOCUMENT ME!!!"""
	# double check types because insurance :P (and hypothesis standards lol)
	check_type(text_type, name, "name")
	check_type(list, inherits, "inherits")

	if children is None:
		children = draw(hs.dictionaries(
			hs.from_regex(_supported_binding_regex),
			_strategies()
		))

		bindings = children.keys()
		values = children.values()
	else:
		bindings, values = _validate_bindings(draw, children, name="children")

	class_name = draw(hs.from_regex(
		name if name is not None else _supported_binding_regex
	))
 	code = "".join([
		"class ", class_name, "(*inherits):\n\t", "\n\t".join(
			["pass"] if len(members) < 1 else [
				"%s = tallent[%r]" % (name, pos) \
					for pos, name in enumerate(members)
			]
		)
	])

	exec(code, locals())

	return locals()[class_name]

# I really never thought I'd be testing variable function inputs at any point in my life...
@hs.composite
def functions(draw,
		name=None
		min_argc=None, # int
		max_argc=None, # int
		manual_argument_bindings=None, # {} dict
		manual_keyword_bindings=None, # {} dict
		body=_phony_callable,
		decorators=None, # [] list
		kwarginit=hs.nothing(),
	):
	"""DOCUMENT ME!!!"""

	# Replicates check_valid_sizes logic but with correct variable names
	check_valid_size(min_argc, "min_argc")
	check_valid_size(max_argc, "max_argc")
	check_valid_interval(min_argc, max_argc, "min_argc", "max_argc")

	min_argc = None if min_argc is None else ceil(min_argc)
	max_argc = None if max_argc is None else floor(max_argc)

	check_strategy(kwarginit, name="kwarginit")

	if decorators is not None:
		check_type(list, decorators, "decorators")
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
			unique_by=lambda x: x not in argb.keys()
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
			check_type(text_type, value, name="")

			if not binding_regex.match(binding):
				raise InvalidArgument(
					"binding dictionary value at '%s' does not match binding \
					regex. '%s' not found in (regex=%s)"
					% (key, value, binding_regex)
				)

			if key <= argb: argb[key] = value

	if manual_keyword_bindings is not None:
		for key, value in manual_keyword_bindings.items():
			check_type(int, key, name="")
			check_type(text_type, value, name="")

			if not binding_regex.match(binding):
				raise InvalidArgument(
					"binding dictionary value at %s does not match binding \
					regex. '%s' not found in (regex=%s)"
					%(key, value, binding_regex)
				)

			if key <= kwargb: kwargb[key] = value

	function_name = draw(hs.from_regex(binding_regex))
	arg_defs = ",".join(argb),
	kwarg_defs = ("".join([kwarg, "=kwargv[", str(index), "],"])) \
		for index, kwarg in enumerate(kwargb)
	kwarg_pass = ("".join(kwarg, "=", kwarg, ",") for kwarg in kwargb),

	code = "".join([
		'def ', function_name, '(', arg_defs, *list(kwarg_defs), '): ',
			'return body(', arg_defs, *list(kwarg_pass), ')'
	])

	exec(code, locals())

	function = locals()[function_name]

	if decorators is not None:
		for d in reverse(decorators): function = d(function)

	return function

@hs.composite
def methods(draw,
		min_argc=None, # int
		max_argc=None, # int
		manual_argument_bindings=None, # {}
		manual_keyword_bindings=None, # {}
		body=_phony_callable,
		decorators=None, # [] itterable
		kwarginit=hs.nothing(),
		parent=classes()
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
		binding_regex=binding_regex,
		min_argc=(min_argc + 1), max_argc=(max_argc+1),
		manual_argument_bindings = arguments,
		manual_keyword_bindings = manual_keyword_bindings, body=body,
		decorators = decorators, kwarginit = kwarginit
	))
	setattr(container, method_body.__name__, method_body)

	call = "".join(["container.", method_body.__name__, "(*args, **kwargs)"])
	def method_wrapper(*args, **kwargs):
		exec(call , locals())

	return method_wrapper

@hs.composite
def classmethods(draw,
		parent=classes(),
		min_argc=None, # int
		max_argc=None, # int
		manual_argument_bindings=None, # {}
		manual_keyword_bindings=None, # {}
		kwarginit=hs.nothing(),
		decorators=None, # [] itterable
		body=_phony_callable,
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
	decorators = [classmethod,] + decorators

	container = draw(parent)
	method_body = draw(functions(
		binding_regex=binding_regex,
		min_argc=(min_argc+1),
		max_argc=(max_argc+1),
		manual_argument_bindings=arguments, # enforce defaults
		manual_keyword_bindings=manual_keyword_bindings,
		kwarginit=kwarginit,
		decorators=decorators,
		body=body,
	))
	setattr(container, method_body.__name__, method_body)

	call = "".join(["container.", method_body.__name__, "(*args, **kwargs)"])
	def method_wrapper(*args, **kwargs):
		exec(call , locals())

	return method_wrapper

@hs.composite
def staticfunctions(draw,
		parent=classes(),
		min_argc=None, # int
		max_argc=None, # int
		manual_argument_bindings=None, # {}
		manual_keyword_bindings=None, # {}
		kwarginit=hs.nothing(),
		decorators=None, # [] itterable
		body=_phony_callable,
	):
	"""DOCUMENT ME!!!"""
	check_strategy(parent, name="parent")
	check_type(list, decorators, name="decorators")

	# primary decorator must be first in the series function properly
	decorators = [staticmethod,] + decorators

	container = draw(parent)
	method_body = draw(functions(
		binding_regex=binding_regex,
		min_argc=min_argc,
		max_argc=max_argc,
		manual_argument_bindings=arguments,
		manual_keyword_bindings=manual_keyword_bindings,
		kwarginit=kwarginit,
		decorators=decorators,
		body=body,
	))
	setattr(container, method_body.__name__, method_body)

	call = "".join(["container.", method_body.__name__, "(*args, **kwargs)"])
	def function_wrapper(*args, **kwargs):
		exec(call , locals())

	return function_wrapper

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
