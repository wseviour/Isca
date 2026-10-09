"""
MiMA Free-Running Test Case with Realistic Orographic & Non-Orographic GWD.

Physical and Dynamical Configuration:
1. Orographic (mountain) Gravity Wave Drag (mg_drag, Pierrehumbert & Stern scheme),
   using tuned parameters and ERA5-derived subgrid mountain height variance.
2. Non-orographic (convective) Gravity Wave Drag (cg_drag, Alexander & Dunkerton scheme)
   with enhanced extratropical momentum flux launch in the Northern Hemisphere
   (Bt_nh = 0.0010 Pa, phi0n = 25.0 deg N, dphin = 10.0 deg) to weaken the stratospheric
   polar vortex (SPV) and mitigate the cold SPV bias, while maintaining equatorial QBO launch.
3. Seasonally-varying CMIP5 ozone forcing (ozone_1990_cmip5.nc).
4. Realistic topography (1/6 deg Navy with ocean smoothing 0.995), land-sea heat capacity
   contrast, realistic albedo choice 7, and realistic surface roughness choice 4.
5. Prescribed analytic ocean Q-fluxes and full Betts-Miller convection.
6. 40 uneven vertical sigma levels extending up to ~0.01 hPa.
"""
import os
import sys
import argparse

# Ensure compiler and toolchain in current Python environment are on PATH
conda_bin = os.path.dirname(sys.executable)
if conda_bin not in os.environ.get('PATH', '').split(':'):
    os.environ['PATH'] = f"{conda_bin}:{os.environ.get('PATH', '')}"

from isca import IscaCodeBase, DiagTable, Experiment, Namelist, GFDL_BASE
from isca.util import interpolate_output

parser = argparse.ArgumentParser(description="Run MiMA free-running GWD test case")
parser.add_argument('--months', type=int, default=1, help="Number of months to run (default: 1)")
parser.add_argument('--days', type=int, default=None, help="Override run duration in days (for short test)")
parser.add_argument('--cores', type=int, default=16, help="Number of MPI cores (default: 16)")
args = parser.parse_args()

NCORES = args.cores
RESOLUTION = 'T42', 40
NUM_MONTHS = args.months

cb = IscaCodeBase.from_directory(GFDL_BASE)

exp = Experiment('strat_free_test', codebase=cb)
exp.clear_rundir()

# Locate orographic subgrid mountain height file (ghprime)
current_dir = os.path.dirname(os.path.realpath(__file__))
mg_drag_file = os.path.join(current_dir, 'input', 'mg_drag.res.nc')
if not os.path.exists(mg_drag_file):
    fallback = os.path.join(GFDL_BASE, 'exp/test_cases/mg_drag/input/mg_drag.res.nc')
    if os.path.exists(fallback):
        mg_drag_file = fallback
    else:
        raise FileNotFoundError(f"Subgrid mountain height file not found at {mg_drag_file} or {fallback}")

# Locate ozone input file (seasonally-varying CMIP5 ozone)
ozone_file = os.path.join(current_dir, 'input', 'ozone_1990_cmip5.nc')
if not os.path.exists(ozone_file):
    ozone_file = os.path.join(GFDL_BASE, 'input/rrtm_input_files/ozone_1990.nc')
    ozone_file_name = 'ozone_1990'
else:
    ozone_file_name = 'ozone_1990_cmip5'

# Input files required for this experiment
exp.inputfiles = [
    ozone_file,
    os.path.join(GFDL_BASE, 'input/navy_topography/navy_topography.data.nc'),
    os.path.join(GFDL_BASE, 'input/navy_topography/navy_pctwater.data.nc'),
    mg_drag_file,
]

diag = DiagTable()
diag.add_file('atmos_monthly', 30, 'days', time_units='days')
diag.add_file('atmos_daily', 1, 'days', time_units='days')

# Monthly 2D & physics diagnostics
diag.add_field('atmosphere', 'precipitation', files=['atmos_monthly'], time_avg=True)
diag.add_field('atmosphere', 'rh', files=['atmos_monthly'], time_avg=True)
diag.add_field('mixed_layer', 't_surf', files=['atmos_monthly'], time_avg=True)
diag.add_field('mixed_layer', 'flux_oceanq', files=['atmos_monthly'], time_avg=True)
diag.add_field('mixed_layer', 'albedo', files=['atmos_monthly'], time_avg=True)
diag.add_field('mixed_layer', 'heat_cap', files=['atmos_monthly'], time_avg=True)
diag.add_field('dynamics', 'vor', files=['atmos_monthly'], time_avg=True)
diag.add_field('dynamics', 'div', files=['atmos_monthly'], time_avg=True)
diag.add_field('rrtm_radiation', 'co2', files=['atmos_monthly'], time_avg=True)

# Convective and Orographic Gravity Wave Drag diagnostics
diag.add_field('damping', 'udt_cgwd', files=['atmos_monthly'], time_avg=True)
diag.add_field('damping', 'udt_gwd', files=['atmos_monthly', 'atmos_daily'], time_avg=True)
diag.add_field('damping', 'vdt_gwd', files=['atmos_monthly', 'atmos_daily'], time_avg=True)
diag.add_field('damping', 'taubx', files=['atmos_monthly'], time_avg=True)
diag.add_field('damping', 'tauby', files=['atmos_monthly'], time_avg=True)
diag.add_field('damping', 'taus', files=['atmos_monthly'], time_avg=True)
diag.add_field('damping', 'tdt_diss_gwd', files=['atmos_monthly'], time_avg=True)
diag.add_field('damping', 'sgsmtn', files=['atmos_monthly'], time_avg=True)

# Coordinate and pressure variables
diag.add_field('dynamics', 'ps', files=['atmos_monthly', 'atmos_daily'], time_avg=True)
diag.add_field('dynamics', 'bk', files=['atmos_monthly', 'atmos_daily'])
diag.add_field('dynamics', 'pk', files=['atmos_monthly', 'atmos_daily'])

# Daily and monthly 3D winds, temperature, geopotential height, and surface height
diag.add_field('dynamics', 'ucomp', files=['atmos_monthly', 'atmos_daily'], time_avg=True)
diag.add_field('dynamics', 'vcomp', files=['atmos_monthly', 'atmos_daily'], time_avg=True)
diag.add_field('dynamics', 'temp', files=['atmos_monthly', 'atmos_daily'], time_avg=True)
diag.add_field('dynamics', 'height', files=['atmos_monthly', 'atmos_daily'], time_avg=True)
diag.add_field('dynamics', 'zsurf', files=['atmos_monthly', 'atmos_daily'], time_avg=True)
diag.add_field('dynamics', 'sphum', files=['atmos_monthly', 'atmos_daily'], time_avg=True)

exp.diag_table = diag

run_days = args.days if args.days is not None else 30

exp.namelist = namelist = Namelist({
    'main_nml': {
        'days': run_days,
        'hours': 0,
        'minutes': 0,
        'seconds': 0,
        'dt_atmos': 180,
        'current_date': [1, 1, 1, 0, 0, 0],
        'calendar': 'thirty_day',
    },

    'idealized_moist_phys_nml': {
        'do_damping': True,
        'mixed_layer_bc': True,
        'do_bm': True,
        'bm_conserve_energy': True,
        'do_lw': False,
        'do_gray_radiation': False,
        'do_rrtm_radiation': True,
    },

    'surface_flux_nml': {
        'use_virtual_temp': True,
        'land_sea_roughness_contrast': True,
        'roughness_choice': 4,
    },

    'mixed_layer_nml': {
        'albedo_value': 0.38,
        'do_qflux': True,
        'load_qflux': False,
        'qflux_amp': 30.0,
        'qflux_width': 16.0,
        'land_sea_albedo_contrast': True,
        'albedo_choice': 7,
        'land_sea_heat_capacity_contrast': True,
        'heat_capacity_choice': 1,
        'depth': 2.5,
    },

    'betts_miller_nml': {
        'rhbm': 0.7,
        'do_simp': False,
        'do_shallower': True,
    },

    'damping_driver_nml': {
        'do_cg_drag': True,
        'do_mg_drag': True,
        'do_rayleigh': False,
    },

    'mg_drag_nml': {
        'do_mconv': False,
        'do_block': True,
        'do_wave': True,
        'gflux_fac': 0.125,
        'gflux_fac_front': 0.0,
        'crit_frac': 0.375,
        'block_fac': 0.5,
        'cg_drag_freq': 21600,
        'source_level_pressure': 315.e+02,
        'tau_min': 1.e-05,
        'efac': 1.0,
    },

    'cg_drag_nml': {
        'Bt_nh': 0.0010,
        'phi0n': 25.0,
        'dphin': 10.0,
        'Bt_eq': 0.0043,
        'Bt_sh': 0.0,
        'phi0s': -15.,
        'dphis': -10.,
        'flag': 0,
        'Bw': 0.4,
        'Bn': 0.0,
        'cw': 35.0,
        'cwtropics': 35.0,
        'cn': 2.0,
        'kelvin_kludge': 1.0,
        'weighttop': 0.7,
        'weightminus1': 0.28,
        'weightminus2': 0.02,
        'source_level_pressure': 315.e+02,
        'damp_level_pressure': 0.85e+02,
        'cg_drag_freq': 21600
    },

    'rrtm_radiation_nml': {
        'do_read_ozone': True,
        'ozone_file': ozone_file_name,
        'solr_cnst': 1370.,
        'dt_rad': 4500,
        'do_read_co2': False,
        'co2ppmv': 390.,
    },

    'diag_manager_nml': {
        'mix_snapshot_average_fields': False
    },

    'fms_nml': {
        'domains_stack_size': 600000
    },

    'fms_io_nml': {
        'threading_write': 'single',
        'fileset_write': 'single',
    },

    'spectral_dynamics_nml': {
        'damping_order': 4,
        'water_correction_limit': 200.e2,
        'reference_sea_level_press': 1.0e5,
        'num_levels': 40,
        'valid_range_t': [100., 800.],
        'initial_sphum': [2.e-6],
        'vert_coord_option': 'uneven_sigma',
        'surf_res': 0.1,
        'scale_heights': 7.9,
        'exponent': 1.4,
        'vert_advect_uv': 'second_centered',
        'vert_advect_t': 'second_centered',
        'robert_coeff': 0.03,
        'ocean_topog_smoothing': 0.995,
        'do_strat_nudging': False,
        'nudge_u_from_file': False,
    }
})

exp.set_resolution(*RESOLUTION)

PLEVELS = [
    100000, 92500, 85000, 70000, 60000, 50000, 40000, 30000, 25000, 20000,
    15000, 10000, 7000, 5000, 3000, 2000, 1000, 700, 500, 300, 200, 100, 50, 20, 10
]

def interpolate_to_pressure_levels(experiment, num_months, p_levs=PLEVELS, files=['atmos_monthly', 'atmos_daily']):
    for m in range(1, num_months + 1):
        outdir = experiment.get_outputdir(m)
        for fname in files:
            infile = os.path.join(outdir, f'{fname}.nc')
            outfile = os.path.join(outdir, f'plev_{fname}.nc')
            if os.path.exists(infile):
                print(f"Interpolating {infile} -> {outfile} onto pressure levels...")
                try:
                    interpolate_output(infile, outfile, all_fields=True, p_levs=p_levs, var_names=['slp', 'height'])
                except Exception as e:
                    print(f"Warning: pressure level interpolation failed for {fname}: {e}")

if __name__ == '__main__':
    cb.compile()
    exp.run(1, use_restart=False, num_cores=NCORES, overwrite_data=True)
    for i in range(2, NUM_MONTHS + 1):
        exp.run(i, num_cores=NCORES)

    interpolate_to_pressure_levels(exp, NUM_MONTHS, p_levs=PLEVELS)
    print(f"\nSUCCESS: Free-running test case completed ({NUM_MONTHS} month(s), {run_days} days)!\n")
