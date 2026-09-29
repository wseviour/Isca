"""
MiMA realistic topography and land surface test case with stratospheric nudging from file,
emulating the full experimental setup of Ning et al. (2026, WCD) / White et al. (2022, JAS)
and the SNAPSI stratospheric nudging protocol (Hitchcock et al. 2022, GMD).

References:
- Ning et al. (2026): https://wcd.copernicus.org/articles/7/277/2026/
- MiMA code & namelists: https://github.com/whning96/MiMA/releases/tag/MiMA-ZonallyAsymmetricMomentumTorque
- White et al. (2022): https://journals.ametsoc.org/view/journals/atsc/79/8/JAS-D-21-0237.1.xml
- SNAPSI protocol: Hitchcock et al. (2022, https://gmd.copernicus.org/articles/15/5073/2022/)

Key features matching Ning et al. (2026) / MiMA v2.0:
1. Realistic Topography:
   - Interpolated from 1/6 deg Navy mean topography (navy_topography.data.nc)
     and percent water (navy_pctwater.data.nc).
   - Regularized / smoothed over ocean with ocean_topog_smoothing = 0.995.
2. Realistic Land Surface & Heat Capacity:
   - Land-sea mask interpolated from percent water dataset (land_option = 'interpolated').
   - Ocean heat capacity: 1.e08 J/(m^2 K) in the tropics (|lat| < 20 deg),
     smoothly transitioning to 3.e08 J/(m^2 K) in extratropics (|lat| > 60 deg).
   - Land heat capacity: 1.e07 J/(m^2 K) everywhere over land.
3. Realistic Surface Albedo:
   - Base ocean albedo: const_albedo = 0.23.
   - Smooth hyperbolic tangent polar ice caps: albedo_cntrNH = 68N, albedo_cntrSH = 64S,
     transition width = 5 deg, higher_albedo = 0.80.
   - Higher desert albedo (+0.20) over Sahara, Arabian, Gobi, and Australian deserts (albedo_choice = 7).
4. Realistic Surface Roughness:
   - Momentum roughness: 3.21e-05 m over ocean, 5.e3x higher (0.1605 m) over land.
   - Latitudinally-dependent moisture roughness over land with enhanced tropical evaporation (roughness_choice = 4).
5. Gravity Wave Drag & Convection:
   - Convective gravity wave drag (cg_drag) with equatorial launch parameters from Ning et al. (2026).
   - Full Betts-Miller convection and Monin-Obukhov boundary layer scheme.
6. Ocean Q-Fluxes:
   - Prescribed analytic heat transport with localized warm pool, Gulf Stream, Kuroshio, etc.
7. Stratospheric Nudging from File:
   - Nudges zonal wind (ucomp) towards an external 3D time-evolving NetCDF profile.
   - Linear time interpolation at every model time step.
   - 6-hour relaxation timescale above 50 hPa, zero below 90 hPa, cubic Hermite ramp between.
"""
import os

from isca import IscaCodeBase, DiagTable, Experiment, Namelist, GFDL_BASE

NCORES = 16
RESOLUTION = 'T42', 40
NUM_MONTHS = 1

cb = IscaCodeBase.from_directory(GFDL_BASE)

exp = Experiment('mima_ning_strat_nudging_test', codebase=cb)
exp.clear_rundir()

# Locate target zonal wind NetCDF file
current_dir = os.path.dirname(os.path.realpath(__file__))
u_target_file = os.path.join(current_dir, 'input', 'u_target.nc')
if not os.path.exists(u_target_file):
    # Fallback to free run output
    source_file = '/home/links/ws359/isca_data/strat_nudging_test_FREE/run0002/atmos_daily.nc'
    if os.path.exists(source_file):
        u_target_file = source_file
    else:
        raise FileNotFoundError(f"Nudging target file not found at {u_target_file} or {source_file}")

target_basename = os.path.basename(u_target_file)

# Input files required for this experiment
exp.inputfiles = [
    os.path.join(GFDL_BASE, 'input/rrtm_input_files/ozone_1990.nc'),
    os.path.join(GFDL_BASE, 'input/navy_topography/navy_topography.data.nc'),
    os.path.join(GFDL_BASE, 'input/navy_topography/navy_pctwater.data.nc'),
    u_target_file
]

diag = DiagTable()
diag.add_file('atmos_monthly', 30, 'days', time_units='days')
diag.add_file('atmos_daily', 1, 'days', time_units='days')

# Monthly 2D & physics diagnostics
diag.add_field('atmosphere', 'precipitation', files=['atmos_monthly'], time_avg=True)
diag.add_field('mixed_layer', 't_surf', files=['atmos_monthly'], time_avg=True)
diag.add_field('mixed_layer', 'flux_oceanq', files=['atmos_monthly'], time_avg=True)
diag.add_field('mixed_layer', 'albedo', files=['atmos_monthly'], time_avg=True)
diag.add_field('mixed_layer', 'heat_cap', files=['atmos_monthly'], time_avg=True)
diag.add_field('dynamics', 'zsurf', files=['atmos_monthly'])
diag.add_field('dynamics', 'sphum', files=['atmos_monthly'], time_avg=True)
diag.add_field('dynamics', 'vor', files=['atmos_monthly'], time_avg=True)
diag.add_field('dynamics', 'div', files=['atmos_monthly'], time_avg=True)
diag.add_field('rrtm_radiation', 'co2', files=['atmos_monthly'], time_avg=True)
diag.add_field('damping', 'udt_cgwd', files=['atmos_monthly'], time_avg=True)     # cg_drag zonal wind tendency
diag.add_field('dynamics', 'udt_nudge', files=['atmos_monthly'], time_avg=True)   # Stratospheric nudging zonal wind tendency

# Coordinate and pressure variables for both monthly and daily files
diag.add_field('dynamics', 'ps', files=['atmos_monthly', 'atmos_daily'], time_avg=True)
diag.add_field('dynamics', 'bk', files=['atmos_monthly', 'atmos_daily'])
diag.add_field('dynamics', 'pk', files=['atmos_monthly', 'atmos_daily'])

# Daily and monthly 3D winds, temperature, and geopotential height (ucomp, vcomp, temp, height)
diag.add_field('dynamics', 'ucomp', files=['atmos_monthly', 'atmos_daily'], time_avg=True)
diag.add_field('dynamics', 'vcomp', files=['atmos_monthly', 'atmos_daily'], time_avg=True)
diag.add_field('dynamics', 'temp', files=['atmos_monthly', 'atmos_daily'], time_avg=True)
diag.add_field('dynamics', 'height', files=['atmos_monthly', 'atmos_daily'], time_avg=True)
exp.diag_table = diag

exp.namelist = namelist = Namelist({
    'main_nml': {
        'days': 30,
        'hours': 0,
        'minutes': 0,
        'seconds': 0,
        'dt_atmos': 500,
        'current_date': [1, 1, 1, 0, 0, 0],
        'calendar': 'thirty_day'
    },

    'topography_nml': {
        'topog_file': 'INPUT/navy_topography.data.nc',
        'water_file': 'INPUT/navy_pctwater.data.nc'
    },

    'spectral_init_cond_nml': {
        'topography_option': 'interpolated',
        'initial_temperature': 264.
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
        'roughness_choice': 4,
        'mom_roughness_land': 5.e3,
        'q_roughness_land': 1.e-12,
        'land_option': 'interpolated',
        'two_stream_gray': False,       # Use RRTM, not grey radiation
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
        'old_dtaudv': True,
        'gust_const': 1.0
    },

    'monin_obukhov_nml': {
        'rich_crit': 2.0,
        'drag_min': 4.e-05
    },

    'atmosphere_nml': {
        'idealized_moist_model': True
    },

    'mixed_layer_nml': {
        'do_qflux': True,
        'surface_choice': 1,
        'tconst': 285.,
        'prescribe_initial_dist': True,
        'evaporation': True,
        'heat_capacity': 3.e08,
        'land_capacity': 1.e07,
        'trop_capacity': 1.e08,
        'trop_cap_limit': 20.,
        'const_albedo': 0.23,
        'albedo_choice': 7,
        'albedo_wdth': 5.0,
        'higher_albedo': 0.80,
        'albedo_cntrNH': 68.,
        'albedo_cntrSH': 64.,
        'lat_glacier': -70.,
        'land_option': 'interpolated',
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
        'do_evap': True
    },

    'sat_vapor_pres_nml': {
        'do_simple': True
    },

    'damping_driver_nml': {
        'do_rayleigh': False,       # off, so cg_drag is the only source of GWD forcing
        'trayfric': -0.5,
        'sponge_pbottom': 50.,
        'do_conserve_energy': True,
        'do_mg_drag': False,
        'do_cg_drag': True,
    },

    'cg_drag_nml': {
        'Bt_0': 0.0043,
        'Bt_nh': 0.0,
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
        # Stratospheric nudging options (SNAPSI protocol with 3D wind from file):
        'do_strat_nudging': True,
        'nudge_u_from_file': True,
        'nudge_u_file': f'INPUT/{target_basename}',
        'nudge_u_varname': 'ucomp',
        'nudge_u_time_offset_days': 30.0, # Nudge month 1 to month 2 (days 30.5-59.5) of free run
        'nudging_tau': 21600.0,           # 6 hour relaxation timescale in seconds
        'nudging_p_bottom': 90.0e2,       # Bottom pressure where nudging ramps up from 0 (90 hPa)
        'nudging_p_top': 50.0e2,          # Top pressure where nudging reaches full strength (50 hPa)
    }
})

exp.set_resolution(*RESOLUTION)

if __name__ == '__main__':
    cb.compile()
    exp.run(1, use_restart=False, num_cores=NCORES)
    for i in range(2, NUM_MONTHS + 1):
        exp.run(i, num_cores=NCORES)
