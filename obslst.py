#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 11 11:49:09 2022

@author: ywan3191
"""
import sys
import argparse
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from astropy.coordinates import SkyCoord, Angle, AltAz, EarthLocation
from astropy.time import Time
from astropy import units as u
from astropy.table import Table


def _main():
    parser = argparse.ArgumentParser(description='Plan the observation', 
                                     formatter_class=argparse.HelpFormatter)
    parser.add_argument('--site', type=str, default='atca', help='telescope name')
    parser.add_argument('--target', type=str, nargs='+', help='target coordinate')
    parser.add_argument('--cal', type=str, nargs='+', 
                        default=['1934-638', '0823-500'], 
                        help='calibrator name')
    parser.add_argument('--time', type=str, default='2022-03-11 00:00:00', 
                        help='planned observing date and time in UTC')
    parser.add_argument('--length', type=float, default=6, 
                        help='planned observing time length')
    parser.add_argument('--elimit', type=float, default=12, 
                        help='elevation limit of the horizon, Parkes is 30 deg')
    
    # default file location/name
    parser.add_argument('--telefile',type=str, default='telescope.csv')
    parser.add_argument('--sourcefile', type=str, default='source.csv')
    parser.add_argument('--calfile', type=str, default='calibrator.csv')
    values = parser.parse_args()
    
    # get telescope location, exit if it's unknown site
    print('plan observation using telescope', values.site)
    location = read_telescope(values)
    
    # get source coordinates
    coords, target_names = get_target(values)
    print('target source', target_names)
    print(coords)
    
    # get calibrator coordinates
    calibrator, cal_names = read_source(values.calfile)
    
    # get planned observing date and time (in UTC)
    # times = get_times(location, values)
    
    # make the elevation plot (radio mode, default)
    elevation_plot(location, coords, calibrator, target_names, cal_names, values)
    
    # make the LST range plot (optional)
    
    
    # make the parallactic angle plot (optional)
    
    
    # check the Azimuth plot (optional)
    
    
    # make the elevation plot (optical mode, with sunrise sunset, optional)
    


def read_telescope(values):
    '''
    Get the telescope location
    '''
    sitetable = Table.read(values.telefile)
    
    # if the telescope is in astropy site list
    if values.site in EarthLocation.get_site_names():
        location = EarthLocation.of_site(values.site)
        
    # or the infomation of the telescope is saved in the csv table
    elif values.site in sitetable['name']:
        idx = sitetable['name'] == values.site
        location = EarthLocation(
            lat=Angle(sitetable[idx]['lat'], unit=u.degree), 
            lon=Angle(sitetable[idx]['lon'], unit=u.degree),
            height=float(sitetable[idx]['height']) * u.m
            )[0]
    else:
        sys.exit('ERROR: unknown telescope name')
    
    return location
    


def read_source(filename):
    
    sourcetable = Table.read(filename)
    coords = []
    
    for i in range(len(sourcetable)):
        if sourcetable['unit'][i] == 'hms':
            coord = SkyCoord(sourcetable['coordinate'][i], 
                             unit=(u.hourangle, u.deg), 
                             frame='icrs')
        elif sourcetable['unit'][i] == 'deg':
            coord = SkyCoord(sourcetable['coordinate'][i], 
                             unit=(u.deg, u.deg), 
                             frame='icrs')
        else: 
            sys.exit('ERROR: wrong unit for source coordinates, should be hms or deg')
            
        coords.append(coord)
    
    return coords, sourcetable['name']
    


# def get_times(location, values):
    
#     t1 = Time(values.time, format='iso', location=location) # UTC
#     t2 = t1 + values.length * u.hour
#     times = t1 + np.arange(0.0, 24.0, 0.1) * u.hour - 5 * u.hour
#     times.format = 'datetime64'

#     return times


def get_target(values):
    
    if values.target == None:
        print('reading target file' + values.sourcefile)
        coords, target_names = read_source(values.sourcefile)
    else:
        coords = SkyCoord(values.target, 
                          unit=(u.hourangle, u.deg), 
                          frame='icrs')
        target_names = list(range(len(values.target)))
        target_names = ['source ' + str(num) for num in target_names]
        
    return coords, target_names



def elevation_plot(location, coords, calibrator, target_names, cal_names, values):
    
    # get observing times
    t1 = Time(values.time, format='iso', location=location) # UTC
    t2 = t1 + values.length * u.hour
    times = t1 + np.arange(0.0, 24.0, 0.1) * u.hour - 5 * u.hour
    times.format = 'datetime64'
    
    # plot!
    fig, ax = plt.subplots(figsize=(8, 6))
    
    for i, coord in enumerate(coords): 
        elevation = coord.transform_to(AltAz(obstime=times,
                                   location=location)).alt
        ax.plot(times.value, elevation, label=target_names[i])
        
    for i, coord in enumerate(calibrator):
        elevation = coord.transform_to(AltAz(obstime=times,
                                    location=location)).alt
        ax.plot(times.value, elevation, ls='--', 
                label=cal_names[i])
        
    ax.axvspan(t1.value, t2.value, alpha=0.3, color='pink')

    ax.set_ylim(bottom=values.elimit)
    ax.set_ylabel('Elevation (deg)')
    ax.set_xlabel('Time (UTC)')
    ax.legend()
    
    date_form = mdates.DateFormatter("%d-%b-%Y/%H:%M")
    ax.xaxis.set_major_formatter(date_form)
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=4))
    fig.autofmt_xdate()
    
    ax2 = ax.twiny()
    ax2.plot(times.value, elevation, alpha=0)
    ax2.xaxis.set_major_formatter(date_form)
    ax2.set_xticks([t1.value, t2.value])
    
    plt.show()


#def main_plan(coords, site, )

if __name__ == '__main__':
    _main()


