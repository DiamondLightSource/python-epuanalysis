# epubrowser

## Description

Python and shell scripts for analysing EPU directories based on a Relion format particle star file. The analysis will allow you to visualise which micrographs were ultimately utilised in Relion processing and further to inspect what the foilhole and grid square looked like from which useful particles were identified. If particle coordinates are present in the star file then they can be shown on the micrograph for further understanding on trends in the data.

## Motivation

I would expect the develops of EPU are writing this functionality but it was necessary to write this code to troubleshoot a data set where 99% of the particles were being thrown away, without an obvious reason. This software helped identify that there were no trends in 'bad' parrticles coming from specific areas of the grid, nor 'good' particles coming from another part of the grid. Some mysteries in cryo-EM and biochemnistry remain unresolved! I hope the code is useful to you.

## FAQ

Please watch the short movie 'EPU_browser.mp4' to familiarise yourself with the functionality of this software.