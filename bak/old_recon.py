"""fullsky reconstruction based on cmblensplus"""

import sys, os
import healpy as hp, numpy as np
import os, os.path as op
import argparse
import pandas as pd
from datetime import datetime

from orphics import maps, stats, cosmology
from pixell import enmap, utils as u
from enlib import bench

import curvedsky
# add the parent dir in the python path
sys.path.append(os.path.dirname(os.getcwd()))
import param as p

defaults = {
    'mapdir': '../simMaps',
    'odir': '../output/recon_ps/',
    'lmax_write': p.lmax_write
}

def log(text):
    time = datetime.now().strftime("%H:%M:%S")
    with open(args.logfile, "a") as f:
        f.write(f"{time}\t{text}\n")


# define parser
parser = argparse.ArgumentParser()

parser.add_argument('--experiment', type=str, help='experiment name')
parser.add_argument('--sim_num', type=int, help='the number of simulation')
parser.add_argument("--mapdir",       type=str, default=defaults['mapdir'], help="Output directory")

parser.add_argument('--nlev_t', type=float, help='noise level of temperature field, in ukarcmin', default=7)
parser.add_argument('--beam_arcmin', type=float, help='beam_arcmin', default=1.4)
parser.add_argument('--ellmin', type=int, help='ellmin of CMB', default=30)
parser.add_argument('--ellmax', type=int, help='ellmax of CMB', default=3000)
parser.add_argument('--delta_L', type=int, help='delta_L of Kappa', default=150)
parser.add_argument('--pure', type=str, default='standard', help='purify method')
parser.add_argument('--logfile', default='log.txt')
parser.add_argument('--add_noise', action='store_true')
parser.add_argument('--obs_filter', action='store_true')
parser.add_argument('--nside', default=1024)

args = parser.parse_args()


if not(op.exists(defaults['odir'])): os.makedirs(defaults['odir'])

# parse parameters into compatible dict
params = {} # params for lensing reconstruction
params['experiment'] = args.experiment
params['nlev_t'] = args.nlev_t
params['nlev_p'] = args.nlev_t*2**0.5
params['beam_arcmin'] = args.beam_arcmin
params['ellmin'] = args.ellmin
params['ellmax'] = args.ellmax
params['Lmin'] = args.ellmin
params['Lmax'] = args.ellmax

cmb_dir = args.mapdir
isim = args.sim_num
log("reading alm...")
with bench.show("read alm"):
    teb_alm = hp.read_alm(cmb_dir + f"/CMBLensed_fullsky_alm_{isim:03d}.fits", hdu=(1,2,3))
    teb_rot_alm = hp.read_alm(cmb_dir + f"/CMBLensedRot_fullsky_alm_{isim:03d}.fits", hdu=(1,2,3))
    kap_alm = hp.read_alm(cmb_dir + f'/kappa_fullsky_alm_{isim:03d}.fits')

lmax = hp.Alm.getlmax(teb_alm.shape[-1])
lmax = defaults['lmax_write']
# generate noise realization
if args.add_noise:
    ls  = np.arange(lmax+1)
    nl  = (params['nlev_p']*np.pi/180/60)**2/maps.gauss_beam(ls, params['beam_arcmin'])**2
    nl  = np.stack([nl/2, nl, nl, nl*0], axis=0)
    nlm = hp.synalm(nl, new=True, lmax=lmax)
else:
    nlm = 0
    nl  = [0,0,0,0]

# inverse variance filtering
ls = np.arange(0, lmax+1)

theory = cosmology.default_theory()
clee, clbb = theory.lCl('EE', ls), theory.lCl('BB', ls)
nlee = (params['nlev_p']*np.pi/180/60)**2/maps.gauss_beam(ls, params['beam_arcmin'])**2
nlbb = nlee
oclee = clee + nlee
oclbb = clbb + nlbb

oclee[0], oclee[1], oclbb[0], oclbb[1] = 1, 1, 1, 1

if args.add_noise:
    Elm = hp.almxfl(teb_alm[1]+nlm[1], 1/oclee)
    Blm = hp.almxfl(teb_alm[2]+nlm[2], 1/oclbb)
    Elm_rot = hp.almxfl(teb_rot_alm[1]+nlm[1], 1/oclee)
    Blm_rot = hp.almxfl(teb_rot_alm[2]+nlm[2], 1/oclbb)
else:
    Elm = hp.almxfl(teb_alm[1], 1/oclee)
    Blm = hp.almxfl(teb_alm[2], 1/oclbb)
    Elm_rot = hp.almxfl(teb_rot_alm[1], 1/oclee)
    Blm_rot = hp.almxfl(teb_rot_alm[2], 1/oclbb)


# convert alm to healpix order to be compatible with clp
Elm = curvedsky.utils.lm_healpy2healpix(Elm, lmax)
Blm = curvedsky.utils.lm_healpy2healpix(Blm, lmax)
Elm_rot = curvedsky.utils.lm_healpy2healpix(Elm_rot, lmax)
Blm_rot = curvedsky.utils.lm_healpy2healpix(Blm_rot, lmax)


# reconstruction
imax = params['ellmax'] + 1  # inclusive
reckap_alm = curvedsky.rec_lens.qeb(params['ellmax'],
                                    params['ellmin'], params['ellmax'], clee[:imax], Elm[:imax,:imax],
                                    Blm[:imax,:imax], gtype='k')

reckap_rot_alm = curvedsky.rec_lens.qeb(params['ellmax'],
                                    params['ellmin'], params['ellmax'], clee[:imax], Elm_rot[:imax,:imax],
                                    Blm_rot[:imax,:imax], gtype='k')


# normalization
Al = curvedsky.norm_quad.qeb('lens', params['ellmax'],
                             params['ellmin'], params['ellmax'], clee[:imax], oclee[:imax],
                             oclbb[:imax], lfac='k')# , clbb[:imax])


reckap_alm *= Al[0][:,None]
reckap_rot_alm *= Al[0][:,None]

# get input kappa alm

kap_alm = curvedsky.utils.lm_healpy2healpix(kap_alm, lmax)

# compute power spectra
EB_inkap_x_inkap   = curvedsky.utils.alm2cl(params['ellmax'], kap_alm[:imax,:imax])

EB_inkap_x_reckap  = curvedsky.utils.alm2cl(params['ellmax'], kap_alm[:imax,:imax], reckap_alm[0])
EB_rot_inkap_x_reckap  = curvedsky.utils.alm2cl(params['ellmax'], kap_alm[:imax,:imax], reckap_rot_alm[0])

EB_reckap_x_reckap = curvedsky.utils.alm2cl(params['ellmax'], reckap_alm[0])
EB_rot_reckap_x_reckap = curvedsky.utils.alm2cl(params['ellmax'], reckap_rot_alm[0])


# # Store data in a dictionary
data_dict = {}
data_dict['EB_inkap_x_inkap'] = EB_inkap_x_inkap

data_dict['EB_inkap_x_reckap'] = EB_inkap_x_reckap
data_dict['EB_rot_inkap_x_reckap'] = EB_rot_inkap_x_reckap

data_dict['EB_reckap_x_reckap'] = EB_reckap_x_reckap
data_dict['EB_rot_reckap_x_reckap'] = EB_rot_reckap_x_reckap


data_df = pd.DataFrame(data_dict)
if args.add_noise:
    data_df.to_csv(defaults['odir'] + f'%s_%s_%s_%s_n.csv' %(params['experiment'], isim, params['ellmin'],params['ellmax']), index=False)
else:
    data_df.to_csv(defaults['odir'] + f'%s_%s_%s_%s.csv' %(params['experiment'], isim, params['ellmin'],params['ellmax']), index=False)








    


