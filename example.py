#! /usr/bin/env python

import ROOT
from PyTreeReader import PyTreeReader

f = ROOT.TFile("./hsimple.root")
#for i, event in enumerate(PyTreeReader(f.ntuple,"p*")):
#	if i == 10: break
#	print event.px()
#        print event.random()

for i, event in enumerate(PyTreeReader(f.ntuple,"*")):
        if i == 10: break
        print event.px()
        print event.random()

for i, event in enumerate(PyTreeReader(f.ntuple,"*",cache=True)):
        if i == 10: break
        print event.px()
        print event.random()
