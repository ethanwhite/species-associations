"""Functions to evaluate the neutral simulations"""
from __future__ import division
import matplotlib
matplotlib.use('Agg')
import numpy as np
import cPickle
import mete
from neutral_Bell import *
from dispersal import *
import matplotlib.pyplot as plt
from scipy.stats import linregress
from random import sample, randint

def BrayCurtis(com1, com2):
    """Return the Bray-Curtis index between two communities"""
    return sum(abs(np.array(com1) - np.array(com2))) / (sum(com1) + sum(com2))

def Euclidean(sample1, sample2):
    """Return the Euclidean distance between two samples"""
    return np.sqrt(sum((np.array(sample1) - np.array(sample2)) ** 2))

def remove_margin(community, m):
    """Remove the marginal cells
    
    Input: 
    community - a community object (from neutral_Bell)
    m - number of rows/columns of cells to remove on each side
    Output:
    List of lists similar to community.COMS but with margins removed
    
    """
    inside_grid = []
    for i in range(m, community.D - m):
        for j in range(m, community.D - m):
            inside_grid.append([i, j])
    inside_grid_1d = [two_to_one_d(grid, community.D) for grid in inside_grid]
    inside_coms = [community.COMS[i] for i in inside_grid_1d]
    return inside_coms
    
def get_total_S(coms):
    """Returns the total richness in a list of lists"""
    abd_tot = np.sum(coms, axis = 0)
    S = sum(abd_tot > 0)
    return S

def get_avg_S(coms):
    """Returns the average richness and variance across local communities"""
    S_list = []
    for com in coms:
        S_list.append(sum(np.array(com) > 0))
    S_mean = sum(S_list) / len(S_list)
    S_var = np.var(S_list)
    return S_mean, S_var

def get_avg_N(coms):
    """Returns the average richness and variance across local communities"""
    N_list = []
    for com in coms:
        N_list.append(sum(com))
    N_mean = sum(N_list) / len(N_list)
    N_var = np.var(N_list)
    return N_mean, N_var

def get_avg_diversity(coms):
    """Returns the average diversity (as Simpson's index) in local communities"""
    div_list = []
    for com in coms:
        abd = np.array(filter(lambda a: a > 0, com))
        simp_index = 1 - sum((abd / sum(abd)) ** 2)
        div_list.append(simp_index)
    return np.mean(div_list)

def get_significance(x, y, alpha):
    """Runs a linear regression y~x and determines if the slope is significant"""
    p = linregress(x, y)[4]
    if p >= alpha: # If slope NOT significantly different from zero
        return 1
    else: return 0

def plot_rad_all(coms, ax):
    """Overlay RADs from all local communities onto a single plot"""
    for com in coms:
        rad = filter(lambda x: x != 0, com)
        ax.semilogy(range(1, len(rad) + 1), sorted(rad, reverse = True), 'o-', color = '#9400D3')
    plt.xlabel('Rank')
    plt.ylabel('Abundance')
    return ax

def plot_rad_avg(coms, ax):
    """Plot the RAD averaged across local communities"""
    richness_list = []
    sum_abd = np.zeros(len(coms[0]))
    for com in coms:
        rad = np.array(sorted(com, reverse = True))
        sum_abd += rad
    avg_rad = sum_abd / len(coms)
    avg_rad_nozero = filter(lambda x: x != 0, avg_rad)
    ax.semilogy(range(1, len(avg_rad_nozero) + 1), avg_rad_nozero, 
                'o-', color = '#9400D3')
    plt.xlabel('Rank')
    plt.ylabel('Abundance')
    return ax
    
def get_S_box(coms, start_loc, d):
    """Obtain S for a box of dim d starting at start_loc in the grid"""
    D = int(np.sqrt(len(coms)))
    x0, y0 = start_loc
    loc_1d = []
    for x in range(x0, x0 + d):
        for y in range(y0, y0 + d):
            loc_1d.append(two_to_one_d([x, y], D))
    com_box = [coms[i] for i in loc_1d]
    abd_box = np.sum(com_box, axis = 0)
    S_box = sum(abd_box != 0)
    return S_box

def plot_SAR(coms, ax):
    """Plot the SAR of the grid"""
    D = int(np.sqrt(len(coms))) # grid dimension
    max_n = int(np.ceil(np.log(D) / np.log(2)))
    S_list = []
    for i in range(max_n):
        d = 2 ** i
        start_loc_list = [two_to_one_d([x, y], D) for x in range(D - d + 1) for y in range(D - d + 1)]
        if (len(start_loc_list) > 100):
            start_locs = sample(start_loc_list, 100)
        else: start_locs = start_loc_list
        S_i_list = [get_S_box(coms, one_to_two_d(loc, D), d) for loc in start_locs]
        S_list.append(np.mean(S_i_list))
    ax.loglog(4 ** np.array(range(max_n)), S_list, 'o-', color = '#9400D3')
    sar_slope = linregress(math.log(4) * np.array(range(max_n)), np.log(S_list))[0]
    plt.xlabel('Area')
    plt.ylabel('Richness')
    plt.annotate('slope = %0.2f' %sar_slope, xy = (0.5, 0.85), xycoords = 'axes fraction', color = 'black')
    return ax

def plot_dd(coms, ax, index = BrayCurtis):
    """Plot distance decay (default index: Bray-Curtis)"""
    D = int(np.sqrt(len(coms)))
    xy = int(np.floor(D / 2)) # (one of) the central cell(s)
    central_com = coms[two_to_one_d([xy, xy], D)]
    dist_list = []
    dd_list = []
    for i, com in enumerate(coms):
        dist_list.append(Euclidean(one_to_two_d(i, D), [xy, xy]))
        dd_list.append(index(com, central_com))
    ax.plot(dist_list, dd_list, 'o', color = '#9400D3')
    plt.xlabel('Distance')
    plt.ylabel('Dissimilarity')
    return ax

def plot_dd_sample(coms, ax, D, index = BrayCurtis, n_sample = 200):
    """Plot distance decay of randomly drawn pair of cells"""
    dist_list = []
    dd_list = []
    for i in range(n_sample):
        a, b = sample(range(len(coms)), 2)
        cell_a = coms[a]
        cell_b = coms[b]
        dd_list.append(index(coms[a], coms[b]))
        dist_list.append(Euclidean(one_to_two_d(a, D), one_to_two_d(b, D)))
    ax.plot(sorted(dist_list), [x for (y, x) in sorted(zip(dist_list, dd_list))], 
            'o-', color = '#9400D3')
    
def plot_heat_map(community, ax, obj = 'N', m = 2):
    """Plot a heatmap of S or N inside local communities"""
    obj_list = [[0 for x in range(0, community.D)] for y in range(0, community.D)]
    for i in range(m, community.D - m):
        for j in range(m, community.D - m):
            loc = two_to_one_d([i, j], community.D)
            if obj == 'N':
                obj_list[i][j] = sum(community.COMS[loc])
            elif obj == 'S':
                obj_list[i][j] = len(filter(lambda a: a != 0, community.COMS[loc]))
    y, x = np.mgrid[slice(0, community.D + 1, 1), slice(0, community.D + 1, 1)]
    plt.pcolor(x, y, obj_list, cmap = plt.get_cmap('Autumn'))
    plt.colorbar()
    plt.title(obj)
    return ax

def get_SAR_slope_Adler(coms):
    """Obtain the SAR slope following Adler (2004)
    
    by randomly sampling 100 square blocks of cells.
    
    """
    D = int(np.sqrt(len(coms)))
    S_list = []
    A_list = []
    for i in range(100):
        block_dim = randint(1, D)
        A_list.append(block_dim ** 2)
        start_loc = [randint(0, D - block_dim), randint(0, D - block_dim)]
        S_i = get_S_box(coms, start_loc, block_dim)
        S_list.append(S_i)
    slope = linregress(np.log(A_list), np.log(S_list))[0]
    return slope