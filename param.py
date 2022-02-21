import math

# repository path
repodir = '/global/cscratch1/sd/hongbo/lens_rot_bias/'
# input power spectra path
psdir = repodir + 'ps/' 

# generated map fits files path
outmapdir = repodir + 'output/maps/'
# generated power spectra path 
outpsdir = repodir + 'output/ps/' 

# input power spectrum files path
lenspotental_cl = psdir + 'cosmo2017_10K_acc3_lenspotentialCls.dat' 

# generated map fits files
cmb_alm_fits = outmapdir + 'fullskyLensedCMB_alm.fits'
kap_alm_fits = outmapdir + 'kap_alm.fits'




# geometry parameters
px_arcmin = 1.
decmax = 45
width_deg = 30
npix = int(width_deg/(px_arcmin/60.))


# loop parameters
A = [0.2, 0.4, 0.6, 0.8, 1.0]
exps_config = {
    'Planck_SMICA': {
        'nlev_t': 45,
        'nlev_p':45*2**0.5,
        'beam_arcmin': 5
    },
    'CMB_S3': {
        'nlev_t': 7,
        'nlev_p': 7*2**0.5,
        'beam_arcmin': 1.4
    },
    'CMB_S4': {
        'nlev_t': 1,
        'nlev_p':2**0.5,
        'beam_arcmin': 3
    }
}

moments = {'moments1':{'ellmin':30, 'ellmax':3000, 'delta_L':150},'moments2':{'ellmin':30, 'ellmax':4000, 'delta_L':200}}

# 'pure', 'no', default='standard'
pure = 'no'
add_noise = True

# sbatch parameters for each job file
qos = 'regular' # 'regular' or 'debug'
nodes = 1 # N
time = '03:00:00' # t
n_tasks_per_node = 60 # how many threads(one task for one threads)
OMP_NUM_THREADS = 12 # how many threads for one process

# processes and jobs
# job_path = repo_path + 'jobs2/'
# npros = len(A)*len(exps_config)*len(moments) # number of total process
# npros_per_job = 5
# njobs = math.ceil(npros/npros_per_job)

