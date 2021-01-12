#!/usr/bin/env python
#

# This code is adapted from a python script kindly shared by T.J.Ragen - University of Leciester, 2019

import os
import sys
import xml.etree.ElementTree as ET

# Crude input variables for xml file
arg=str(sys.argv[1])
#file=os.path.splitext(arg)[0]

# Read xml file
tree = ET.parse(arg)
root = tree.getroot()

# FEI EPU xml stuff
ns = {'p': 'http://schemas.datacontract.org/2004/07/Applications.Epu.Persistence'}  # TODO: versioning
ns['system'] = 'http://schemas.datacontract.org/2004/07/System'
ns['so'] = 'http://schemas.datacontract.org/2004/07/Fei.SharedObjects'
ns['g'] = 'http://schemas.datacontract.org/2004/07/System.Collections.Generic'
ns['s'] = 'http://schemas.datacontract.org/2004/07/Fei.Applications.Common.Services'
ns['a'] = 'http://schemas.datacontract.org/2004/07/System.Drawing'

# Find beam diameter in xml file
beamDiameter = root.find('so:microscopeData/so:optics/so:BeamDiameter', ns).text
stagePositionA = root.find('so:microscopeData/so:stage/so:Position/so:A', ns).text
stagePositionB = root.find('so:microscopeData/so:stage/so:Position/so:B', ns).text
stagePositionX = root.find('so:microscopeData/so:stage/so:Position/so:X', ns).text
stagePositionY = root.find('so:microscopeData/so:stage/so:Position/so:Y', ns).text
stagePositionZ = root.find('so:microscopeData/so:stage/so:Position/so:Z', ns).text
pixelSize = root.find('so:SpatialScale/so:pixelSize/so:x/so:numericValue', ns).text

micronPix = float(pixelSize)*1e6
micronX = float(stagePositionX)*1e6
micronY = float(stagePositionY)*1e6

print('stagePosX: '+str(micronX))
print('stagePosY: '+str(micronY))

print('micronPix: '+str(micronPix))
