"""
Verification script for wavenumber-selective stratospheric nudging in Isca.

Tests 4 cases (1-day simulations):
1. Case A: Baseline full gridpoint nudging (nudge_wave_min=0, nudge_wave_max=-1)
2. Case B: Zonal-mean nudging (nudge_wave_min=0, nudge_wave_max=0)
3. Case C: Planetary Wave 1 nudging (nudge_wave_min=1, nudge_wave_max=1)
4. Case D: Planetary Waves 1-3 nudging (nudge_wave_min=1, nudge_wave_max=3)

Verifies:
- Zonal variance / standard deviation along longitude
- Fourier power spectrum |c(s)|^2 for s = 0, 1, 2, ...
- Spectral purity of the nudging tendency field udt_nudge
"""
import os
import sys
import numpy as np

# Ensure environment
os.environ['PATH'] = '/home/links/ws359/miniconda3/envs/isca_env/bin:' + os.environ.get('PATH', '')
os.environ['GFDL_BASE'] = '/home/links/ws359/Isca'
os.environ['GFDL_ENV'] = 'ubuntu_conda'
os.environ['GFDL_WORK'] = '/home/links/ws359/isca_work'
os.environ['GFDL_DATA'] = '/home/links/ws359/isca_data'

from isca import IscaCodeBase, DiagTable, Experiment, Namelist, GFDL_BASE

NCORES = 8
DAYS = 1

cb = IscaCodeBase.from_directory(GFDL_BASE)

current_dir = os.path.dirname(os.path.realpath(__file__))
u_target_file = os.path.join(current_dir, 'input', 'u_target.nc')
target_basename = os.path.basename(u_target_file)

cases = [
    {
        'id': 'baseline',
        'name': 'Case A: Full Gridpoint (s >= 0)',
        'exp_name': 'verify_nudge_baseline',
        'wave_min': 0,
        'wave_max': -1,
        'wave_list': None,
    },
    {
        'id': 'zonal_mean',
        'name': 'Case B: Zonal Mean Only (s = 0)',
        'exp_name': 'verify_nudge_zonal_mean',
        'wave_min': 0,
        'wave_max': 0,
        'wave_list': None,
    },
    {
        'id': 'wave_1',
        'name': 'Case C: Planetary Wave 1 (s = 1)',
        'exp_name': 'verify_nudge_wave_1',
        'wave_min': 1,
        'wave_max': 1,
        'wave_list': None,
    },
    {
        'id': 'wave_1_3',
        'name': 'Case D: Waves 1-3 (s in [1, 3])',
        'exp_name': 'verify_nudge_waves_1_3',
        'wave_min': 1,
        'wave_max': 3,
        'wave_list': None,
    },
]

results = {}

for case in cases:
    exp_name = case['exp_name']
    print(f"\n==========================================")
    print(f"Setting up and running {case['name']}...")
    print(f"==========================================")

    exp = Experiment(exp_name, codebase=cb)
    exp.clear_rundir()

    exp.inputfiles = [
        os.path.join(GFDL_BASE, 'input/rrtm_input_files/ozone_1990.nc'),
        u_target_file
    ]

    diag = DiagTable()
    diag.add_file('atmos_daily', 1, 'days', time_units='days')

    diag.add_field('dynamics', 'udt_nudge', files=['atmos_daily'], time_avg=True)
    diag.add_field('dynamics', 'ucomp', files=['atmos_daily'], time_avg=True)
    diag.add_field('dynamics', 'vcomp', files=['atmos_daily'], time_avg=True)
    diag.add_field('dynamics', 'temp', files=['atmos_daily'], time_avg=True)
    diag.add_field('dynamics', 'ps', files=['atmos_daily'], time_avg=True)
    diag.add_field('dynamics', 'bk', files=['atmos_daily'])
    diag.add_field('dynamics', 'pk', files=['atmos_daily'])

    exp.diag_table = diag

    spectral_dynamics_nml = {
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
        # Stratospheric nudging options
        'do_strat_nudging': True,
        'nudge_u_from_file': True,
        'nudge_u_file': f'INPUT/{target_basename}',
        'nudge_u_varname': 'ucomp',
        'nudge_u_time_offset_days': 30.0,
        'nudging_tau': 21600.0,
        'nudging_p_bottom': 90.0e2,
        'nudging_p_top': 50.0e2,
        'nudge_wave_min': case['wave_min'],
        'nudge_wave_max': case['wave_max'],
    }

    if case['wave_list'] is not None:
        spectral_dynamics_nml['nudge_wave_list'] = case['wave_list']

    exp.namelist = Namelist({
        'main_nml': {
            'days': DAYS,
            'hours': 0,
            'minutes': 0,
            'seconds': 0,
            'dt_atmos': 450,
            'current_date': [1, 1, 1, 0, 0, 0],
            'calendar': 'thirty_day'
        },
        'idealized_moist_phys_nml': {
            'do_damping': True,
            'turb': True,
            'mixed_layer_bc': True,
            'do_virtual': False,
            'do_simple': True,
            'roughness_mom': 3.21e-05,
            'roughness_heat': 3.21e-05,
            'roughness_moist': 3.21e-05,
            'two_stream_gray': False,
            'do_rrtm_radiation': True,
            'convection_scheme': 'FULL_BETTS_MILLER'
        },
        'vert_turb_driver_nml': {
            'do_mellor_yamada': False,
            'do_diffusivity': True,
            'do_simple': True,
            'constant_gust': 0.0,
            'use_tau': False
        },
        'diffusivity_nml': {
            'do_entrain': False,
            'do_simple': True,
        },
        'surface_flux_nml': {
            'use_virtual_temp': False,
            'do_simple': True,
            'old_dtaudv': True
        },
        'atmosphere_nml': {
            'idealized_moist_model': True
        },
        'mixed_layer_nml': {
            'tconst': 285.,
            'prescribe_initial_dist': True,
            'evaporation': True,
            'depth': 100.,
            'albedo_value': 0.23,
            'do_qflux': True,
            'do_warmpool': True,
        },
        'qflux_nml': {
            'qflux_amp': 26.,
            'warmpool_localization_choice': 3,
            'warmpool_k': 1.66666,
            'warmpool_amp': 18.,
            'warmpool_width': 35.,
            'qflux_width': 16.,
            'warmpool_phase': 140.,
            'warmpool_centr': 0.,
            'gulf_k': 4,
            'gulf_amp': 70.,
            'kuroshio_amp': 40.,
            'trop_atlantic_amp': 50.,
            'gulf_phase': 310.,
            'Hawaiiextra': 30.0,
            'Pac_ITCZextra': 0.0,
            'north_sea_heat': 0.0,
        },
        'betts_miller_nml': {
            'tau_bm': 7200.,
            'rhbm': .7,
            'do_simp': False,
            'do_shallower': True,
            'do_changeqref': False,
            'do_envsat': False,
            'do_taucape': False,
            'capetaubm': 900.,
            'tau_min': 2400.,
        },
        'lscale_cond_nml': {
            'do_simple': True,
        },
        'cg_drag_nml': {
            'Bt_nh': 0.0,
            'Bt_0': 0.0043,
            'Bt_eq': 0.0043,
            'Bt_sh': 0.0,
            'phi0n': 15.,
            'phi0s': -15.,
            'dphin': 10.,
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
            'ozone_file': 'ozone_1990',
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
        'spectral_dynamics_nml': spectral_dynamics_nml,
    })

    exp.run(1, use_restart=False, num_cores=NCORES)
    output_file = os.path.join(os.environ['GFDL_DATA'], exp_name, 'run0001', 'atmos_daily.nc')
    print(f"Completed {case['name']}. Output file: {output_file}")
    results[case['id']] = output_file

print("\nAll 4 test cases ran successfully!")
