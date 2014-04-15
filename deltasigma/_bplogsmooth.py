# -*- coding: utf-8 -*-
# _bplogsmooth.py
# Module providing the bplogsmooth function
# Copyright 2013 Giuseppe Venturini
# This file is part of python-deltasigma.
#
# python-deltasigma is a 1:1 Python replacement of Richard Schreier's 
# MATLAB delta sigma toolbox (aka "delsigma"), upon which it is heavily based.
# The delta sigma toolbox is (c) 2009, Richard Schreier.
#
# python-deltasigma is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# LICENSE file for the licensing terms.

"""Module providing the bplogsmooth() function, which smooths an fft and 
converts it to dB.
"""

from __future__ import division
import numpy as np
from numpy.linalg import norm

from ._dbp import dbp
from ._utils import carray, mround

def bplogsmooth(X, tbin, f0):
	"""Smooth the FFT and convert it to dB.

	Use 8 bins from the bin corresponding to ``f0`` to ``tbin`` and again as far.
	Thereafter increase bin sizes by a factor of 1.1, staying less than 2^10.
	For tbin, group the bins together.

	Use this for nice double-sided log-log plots.

	.. note:: ``tbin`` is assumed to be in the upper sideband!

	.. seealso:: :func:`logsmooth`

	"""
	X = carray(X).squeeze()
	N = X.shape[0]
	N2 = int(np.floor(N/2))
	tbin = int(tbin)
	n = 8

	bin0 = int(mround(f0*N))
	assert tbin > bin0 # we said upper sideband!
	bin1 = ((tbin - bin0) % n) + bin0
	bind = bin1 - bin0
	usb1 = np.concatenate((np.arange(bin1, tbin+1, n), 
	                       np.arange(tbin+3, tbin+bind+1, 8)
	                     ))
	m = usb1[-1] + n
	while m + n/2. < N/2.:
		usb1 = np.concatenate((usb1, np.array((m,))))
		n = mround(min(n*1.1, 2**10))
		m = m + int(n)
	usb2 = np.concatenate((usb1[1:]-1, np.array((N2,))))

	n = 8
	lsb2 = np.arange(bin1, bin1 - 2*bind + 1, -n) - 1
	m = lsb2[-1] - n
	while m - n/2. > 1:
		lsb2 = np.concatenate((lsb2, np.array((m,))))
		n = mround(min(n*1.1, 2**10))
		m = m - int(n)
	lsb1 = np.concatenate((lsb2[1:] + 1, np.ones((1,))))

	startbin = np.concatenate((lsb1[::-1], usb1)) - 1
	stopbin = np.concatenate((lsb2[::-1], usb2)) - 1

	f = ((startbin + stopbin)/2.)/N - f0
	p = np.zeros(f.shape)
	for i in range(f.shape[0]):
		p[i] = dbp(
		           norm(X[startbin[i]:stopbin[i] + 1]**2. /
		                (stopbin[i] - startbin[i] + 1.),
		               ord=1)
		          )
	return f, p

def test_bplogsmooth():
	"""Test function for bplogsmooth()
	"""
	import scipy.io
	import pkg_resources
	from ._ds_hann import ds_hann
	from ._simulateDSM import simulateDSM
	from ._synthesizeNTF import synthesizeNTF
	f0 = 1./8
	OSR = 64
	order = 8
	N = 8192
	H = synthesizeNTF(order, OSR, 1, 1.5, f0)
	fB = int(np.ceil(N/(2. * OSR)))
	ftest = int(mround(f0*N + 1./3*fB))
	u = 0.5*np.sin(2*np.pi*ftest/N*np.arange(N))
	v, xn, xmax, y = simulateDSM(u, H)
	spec = np.fft.fft(v*ds_hann(N))/(N/4)
	X = spec[:N/2 + 1]
	f, p = bplogsmooth(X, ftest, f0)

	fname = pkg_resources.resource_filename(__name__, "test_data/test_bplogsmooth.mat")
	data = scipy.io.loadmat(fname)

	assert np.allclose(f, data['f'], atol=1e-9, rtol=1e-5)
	assert np.allclose(p, data['p'], atol=1e-9, rtol=1e-5)
