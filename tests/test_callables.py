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

# make sure we can do these tests in < python2.7 & > python3
from __future__ import division, print_function, absolute_import
if __debug__: import pdb

# make sure when we run pytest outside of setup, we can still run this.
import sys
import os.path as path
srcdir = path.abspath(path.join(path.dirname(repr(__file__)[1:-1]), "../"))
sys.path.append(srcdir)

from hypothesis import given
import hypothesis.errors as he
from hypothesis.internal.compat import PY3, text_type, getfullargspec

from hypothesis.strategies import *
from hypothesis_callables import *

from hypothesis_callables import _supported_binding_regex

import pytest # test library
import pdb # debugger

@composite
def primitives(draw):
	"""DOCUMENT ME!!!"""
	# NOTE:
	#	Could make this more complex and support recursion for itterables,
	#	but I'm too lazy atm.
	return draw(one_of( # lol, this couldn't be more direct.
		#none(),
		integers(),
		floats(),
		characters(),
		tuples(),
		lists()
	))

def primitives_w_bindings(automatic, manual, fail):
	"""DOCUMENT ME!!!"""
	bindings = []

	if manual: bindings.append( from_regex(_supported_binding_regex) )
	if automatic: bindings.append( integers() )
	if fail: bindings.append( characters() )

	return dictionaries(
		one_of(*bindings), # bindings
		primitives(), # child values
		max_size=10
	)

class TestClassStrategy(object):
	"""DOCUMENT ME!!!"""

	@given(data())
	def test_automatic_child_binding_assignment(self, data):
		children = data.draw(primitives_w_bindings(True, False, False))
		product = data.draw(classes(
			children={key: just(value) for key, value in children.items()}
		))

		children_produced = len(children)
		children_assigned = 0
		for value in children.values():
			for attribute in dir(product):
				if getattr(product, attribute) is value:
					children_assigned += 1;
					break; # break inner

		assert children_assigned == children_produced

	@given(data())
	def test_manual_child_binding_assignment(self, data):
		children = data.draw(primitives_w_bindings(False, True, False))
		product = data.draw(classes(
			children={key: just(value) for key, value in children.items()}
		))

		for binding, value in children.items():
			assert getattr(product, binding) is value

	@given(data())
	def test_combined_child_binding_assignment(self, data):
		children = data.draw(primitives_w_bindings(True, True, False))
		product = data.draw(classes(
			children={key: just(value) for key, value in children.items()}
		))

		children_produced = len(children)
		children_assigned = 0
		for key, value in children.items():
			if isinstance(int, binding):
				for attribute in dir(product):
					if getattr(product, attribute) is value:
						children_assigned += 1; break;
			else:
				assert getattr(product, key) is value
				children_assigned += 1

		assert children_assigned == children_produced

	@given(data())
	def test_ancestory_inheritance(self, data):
		unique_children = data.draw(primitives_w_bindings(False, True, False))
		unique_ancestors = (data.draw(classes(
			children = {key:just(value) for key, value in mapping.items()}
		)) for mapping in unique_children)

		product = data.draw(classes(inherits=unique_ancestors))

		product_elements = {}
		for mapping in unique_children: product_elements.update(mapping)

		assert all(
			getattr(product, key) is value \
				for key, value in product_elements.items()
		)



	@given(data())
	def test_bad_child_keys(self, data):
		"""DOCUMENT ME!!!"""
		pass
		with pytest.raises(he.InvalidArgument):
			children = data.draw(primitives_w_bindings(True, True, True))
			product = data.draw(classes(children = children))

	@given(data())
	def test_bad_ancestor(self, data):
		pass
		with pytest.raises(he.InvalidArgument):
			children = data.draw()

			generated_object = data.draw(classes(
				children = children
			))

	@given(data())
	def test_bad_binding_regex(self):
		pass

	@given(data())
	def test_good_instance(self):
		pass

class TestCallableStrategies(object):
	pass

class TestParameterStrategy(object):
	pass
