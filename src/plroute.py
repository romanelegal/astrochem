#!@PYTHON@
#
#  plroute - Plot the destruction/formation routes computed by
#  astrochem for a given specie
#
#  Copyright (c) 2006-2011 Sebastien Maret
# 
#  This file is part of Astrochem.
#
#  Astrochem is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published
#  by the Free Software Foundation, either version 3 of the License,
#  or (at your option) any later version.
#
#  Astrochem is distributed in the hope that it will be useful, but
#  WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  General Public License for more details.
# 
#  You should have received a copy of the GNU General Public License
#  along with Astrochem.  If not, see <http://www.gnu.org/licenses/>.

import sys
import os
import getopt
import string
import biggles
from numpy import *

VERSION = "0.1"

def usage():
    """
    Display usage.

    """

    print """Usage: plroute [options] command file

Commands:
   time   Plot formation/destruction rates vs. time in a given shell
   av     Plot formation/destruction rates vs. visual extinction
          at a given time

Options:
   -h, --help               Display this help
   -V, --version            Display plroute version information
   -o, --output             Create a postscript file

   -s, --shell=index        Plot form./dest. rates in a given shell
   -t, --time=index         Plot form./dest. rates at a given time
   -n, --nroutes=number     Plot the rates of the first n routes
   -x, --xrange=xmin,xmax   Set the x axis range
   -y, --yrange=ymin,ymax   Set the y axis range
   -c, --chmfile=file       Specify chemical network file
   
See the plroute(1) man page for more information
Report bugs to <sebastien.maret@obs.ujf-grenoble.fr>."""

def version():
    """
    Display version number.

    """

    print "This is plroute, version %s" % VERSION
    print """Copyright (c) 2006-2011 Sebastien Maret

This is free software. You may redistribute copies of it under the terms
of the GNU General Public License. There is NO WARRANTY, to the extent
permitted by law."""

def readrout(filename):
    """
    Read a rout file and return arrays of time, shell number,
    formation/destruction rates

    """

    a = []
    try:
        f = open(filename)
    except:
        sys.stderr.write("plroute: error: can't open %s.\n" % filename)
        sys.exit(1)

    # Skip comments
    f.readline()
    f.readline()
    f.readline()

    # Read all lines
    lines = map(string.strip, f.readlines())

    # Construct a list of the elements of the array
    for line in lines:
        newline = []        
        for elem in string.split(line):
	    elem = string.atof(elem)
            newline.append(elem)
        a.append(newline)

    # Create an array from the list
    a = array(a)

    # Extract shell number, time, formation/destruction reactions and
    # rates.
    shell = array(a[::2,0], dtype = int)
    time = a[::2,1]
    formation_reac = array(a[0::2,2::2], dtype = int)
    formation_rate = a[0::2,3::2]
    destruction_reac = array(a[1::2,2::2], dtype = int)
    destruction_rate = a[1::2,3::2]

    shell = unique(shell)
    nshell = len(unique(shell))
    time = unique(time)
    ntime = len(unique(time))

    # Reshape formation/destruction reactions and rates arrays 
    formation_reac = reshape(formation_reac, (nshell, ntime, -1))
    formation_rate = reshape(formation_rate, (nshell, ntime, -1))
    destruction_reac = reshape(destruction_reac, (nshell, ntime, -1))
    destruction_rate = reshape(destruction_rate, (nshell, ntime, -1))

    return time, shell, formation_reac, formation_rate, destruction_reac, destruction_rate

def speciename(filename):
    """
    Guess the specie name from the .abun or .rout file name

    """
    
    filename = os.path.basename(filename)[:-5]

    return "$" + formatspecies(filename) + "$"

def curveblank(xvalues, yvalues, blanking = 0, linecolor = "black"):
    """
    Return a list of curves of yvalues vs. xvalues with blank values

    This function returns a list of curves of yvalues vs. xvalues
    ignoring blanked values. For example, if xvalues = [1,2,3,4,5] and
    yvalues = [1,2,0,3,4], it will return a list of two curves
    corresponding to the xvalues [1,2] and [3,4], respectively. These
    curves can be added to a plot object, so the two closest non
    blanked value from a blank values (2 and 3 in this example) are
    not connected.

    Arguments:
       xvalues:     sequence of x values
       yvalues:     sequence of y values
       blanking:    blanking value for y (default 0)
       linecolor:   curve color (default "black")
       
    """

    x = []
    y = []
    c = []
    for xi, yi in zip(xvalues, yvalues):
        if yi != blanking:
            x.append(xi)
            y.append(yi)
        else:
            if len(x) >= 2:
                c.append(biggles.Curve(x, y, linecolor = linecolor, linewidth = 2))
            x = []
            y = []
    if len(x) >= 2:
        c.append(biggles.Curve(x, y, linecolor = linecolor, linewidth = 2))

    return c

def getreact(react_number, chmfile):
    """
    Get the reactions corresponding to reaction numbers

    Arguments:
    react_number:   a list of reaction number
    chmfile:        chemical network file

    """

    # Read the chemical network file
    react_dict = {}
    try:
        f = open(chmfile, 'r')
        for line in f:
            if line[0] == "#":
                continue
            react = line.rsplit(None, 5)[0]
            react_n = int(line.rsplit(None, 5)[5])
            react_dict[react_n] = react
    except:
	sys.stderr.write("plroute: error: can't read %s.\n" % chmfile)
	sys.exit(1)

    react = []
    for react_n in react_number:
        try:
            react.append(formatreact(react_dict[react_n]))
        except KeyError:
            sys.stderr.write("plroute: warning: can't find reaction %i in %s.\n" \
                                 % (react_n, chmfile))
            react.append(react_n)
        
    return react

def formatreact(react):
    """
    Format a reaction in Biggles' TeX-like format

    Arguments:
    react:   reaction string

    """

    reaction = "$"

    reactants = react.split("->")[0].split(" + ")
    products = react.split("->")[1].split(" + ")

    for i in range(len(reactants) - 1):
        reaction = reaction + formatspecies(reactants[i].strip()) + " + "
    reaction = reaction + formatspecies(reactants[-1].strip()) + " \\rightarrow  "
    for i in range(len(products) - 1):
        reaction = reaction + formatspecies(products[i].strip()) + " + "
    reaction = reaction + formatspecies(products[-1].strip()) + "$"

    return reaction

def formatspecies(spec):
    """
    Format a species in Biggles' TeX-like format

    Arguments:
    species:   species string

    """

    if spec in ["cosmic-ray", "uv-photon"]:
        return spec

    species = ""
    for char in spec:
	if char == '(' or char == ')':
	    continue
	elif (char == '+' or char == '-'):
	    species = species + "^{" + char + "}"
	elif char.isdigit():
	    species = species + "_{" + char + "}"
	else:
	    species = species + char

    return species

def main():
    """
    Main program for plroute

    """

    # Parse options and check commands and arguments
    try:
	opts, args = getopt.getopt(sys.argv[1:], "ho:s:t:x:y:c:",
				   ["help", "output=", "shell=", 
                                    "time=", "xrange=", "yrange=",
                                    "chmfile="])
    except getopt.GetoptError:
	usage()
	sys.exit(1)

    output = None
    s =  0
    t = -1
    n = 8
    xrange = None
    yrange = None
    chmfile = None

    for opt, arg in opts:
	if opt in ("-h", "--help") :
	    usage()
	    sys.exit()
	if opt in ("-o", "--output"):
	    output = arg
	if opt in ("-s", "--shell"):
            try:
                s = int(arg)
            except:
                sys.stderr.write("plroute: error: invalid shell index.\n")
                sys.exit(1)
	if opt in ("-t", "--time"):
            try:
                t = int(arg)
            except:
                sys.stderr.write("plroute: error: invalid time index.\n")
                sys.exit(1)
	if opt in ("-n", "--nroutes"):
            try:
                r = int(arg)
            except:
                sys.stderr.write("plroute: error: number of routes.\n")
                sys.exit(1)
        if opt in ("-x", "--xrange"):
            try:
                xrange = [float(arg.split(",")[0]), float(arg.split(",")[1])]
            except:
                sys.stderr.write("plroute: error: invalid x axis range.\n")
                sys.exit(1)
        if opt in ("-y", "--yrange"):
            try:
                yrange = [float(arg.split(",")[0]), float(arg.split(",")[1])]
            except:
                sys.stderr.write("plroute: error: invalid y axis range.\n")
                sys.exit(1)
        if opt in ("-c", "--chmfile"):
            chmfile = arg

    if len(args) != 2:
	usage()
	sys.exit(1)
    command = args[0]
    filename = args[1]

    if not command in ["time", "av"]:
	sys.stderr.write("plroute: error: invalid command.\n")
	sys.exit(1)

    biggles.configure( 'screen', 'width', 1200 )
    biggles.configure( 'screen', 'height', 600 )
    biggles.configure('postscript', 'width', '15.0in')
    biggles.configure('postscript', 'height', '7.5in')

    t = biggles.Table(1,2)
    p1 = biggles.FramedPlot()
    p2 = biggles.FramedPlot()
    p1.title = "Main " + speciename(filename) + " formation routes"
    p2.title = "Main " + speciename(filename) + " destruction routes"
    p1.ytitle = "$Formation rate (cm^{-3} s^{-1})$"
    p2.ytitle = "$Destruction rate (cm^{-3} s^{-1})$"
    p1.ylog = p2.ylog = 1
    if xrange:
	p1.xrange = p2.xrange = xrange
    if yrange:
	p1.yrange = p2.yrange = yrange
    curves_f = []
    curves_d = []

    # Stack for line colors
    linecolor_stack = ["red", "blue", "green", "yellow", "orange", "cyan"]
    
    # Plot formation/destruction rates as a function of time or shell
    # number for the main formation/destruction routes

    time, shell, formation_reac, formation_rate, destruction_reac, \
        destruction_rate = readrout(filename)
    if command == "time":

        p1.xtitle = p2.xtitle = "Time (yr)"
        p1.xlog = p2.xlog = 1

        # Check that the shell index is valid
        try:
            temp = formation_reac[s, 0, 0]
        except IndexError:
            sys.stderr.write("plroute: error: shell index is out of bounds.\n")
            sys.exit(1)

        # Create arrays containing the destruction/formation routes at
        # each time step and in each shell

        f_reac = unique(formation_reac[s, :, :])
        d_reac = unique(destruction_reac[s, :, :])
        f_reac = f_reac[f_reac.nonzero()]
        d_reac = d_reac[d_reac.nonzero()]
        f_rate = zeros(len(f_reac) * len(time), dtype=float)
        d_rate = zeros(len(d_reac) * len(time), dtype=float)
        f_rate = f_rate.reshape(len(f_reac), len(time))
        d_rate = d_rate.reshape(len(d_reac), len(time))

        for i in range(len(time)):
            for j in range(len(f_reac)):
                index = where(formation_reac[s, i, :] == f_reac[j])[0]
                if len(index) > 0:
                    f_rate[j, i] = formation_rate[s, i, index[0]]
                else:
                    f_rate[j, i] = 0.
            for j in range(len(d_reac)):
                index = where(destruction_reac[s, i, :] == d_reac[j])[0]
                if len(index) > 0:
                    d_rate[j, i] = destruction_rate[s, i, index[0]]
                else:
                    d_rate[j, i] = 0.

        # Find the most important formation/destruction routes

        max_f_rate = zeros(len(f_reac), dtype=float)
        max_d_rate = zeros(len(d_reac), dtype=float)
        
        for j in range(len(f_reac)):
            max_f_rate[j] = max(f_rate[j, :])
        for j in range(len(d_reac)):
            max_d_rate[j] = max(-d_rate[j, :])

        index_f = max_f_rate.argsort()[::-1]
        index_d = max_d_rate.argsort()[::-1]

        # Find the reaction corresponding to the reaction numbers
        if chmfile:
            f_reaction = getreact(f_reac, chmfile)
            d_reaction = getreact(d_reac, chmfile)

        # Plot them, ignoring blanked values
            
        for j in index_f[0:6]:
            linecolor = linecolor_stack.pop(0)
            linecolor_stack.append(linecolor)
            c = curveblank(time, f_rate[j, :], linecolor = linecolor)
            if chmfile:
                c[0].label = f_reaction[j]
            else:
                c[0].label = "%i" % f_reac[j]
            curves_f.append(c[0])
            for ci in c:
                p1.add(ci)

        for j in index_d[0:6]:
            linecolor = linecolor_stack.pop(0)
            linecolor_stack.append(linecolor)
            c = curveblank(time, -d_rate[j, :], linecolor = linecolor)
            if chmfile:
                c[0].label = d_reaction[j]
            else:
                c[0].label = "%i" % d_reac[j]
            curves_d.append(c[0])
            for ci in c:
                p2.add(ci)

    else:   
        print "Not implemented yet."
        sys.exit()
    
    # Draw the plot key
    if chmfile:
        xkey, ykey = .25, .4
    else:
        xkey, ykey = .75, .4
    p1.add(biggles.PlotKey(xkey, ykey, curves_f))
    p2.add(biggles.PlotKey(xkey, ykey, curves_d))
    if command == "av":
        p.add(biggles.PlotLabel(.8,.9, "t=%3.1fx10$^{%i} yr" % 
                                 (time[t]/10**log10(time[t]),
                                  floor(log10(time[t])))))
    
    t[0,0] = p1
    t[0,1] = p2

    if output:
	t.write_eps(arg)
    else:
        t.show()

main()  
	
    
