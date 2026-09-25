"""
MiMA test case with convective gravity wave drag (cg_drag) and analytic Q-fluxes,
following the control simulation configuration described in Ning et al. (2026, WCD)
and Garfinkel et al. (2020, JAMES):
- Ning et al. (2026): https://wcd.copernicus.org/articles/7/277/2026/
- Release / namelist: https://github.com/whning96/MiMA/releases/tag/MiMA-ZonallyAsymmetricMomentumTorque

Physics settings:
- Alexander & Dunkerton (1999) convective gravity wave drag scheme (cg_drag)
  with equatorial launch parameters from Ning et al. (2026) / White et al. (2022).
  do_rayleigh is disabled so Rayleigh friction does not damp the upper levels.
- Analytic ocean Q-fluxes including meridional heat transport and 2D perturbations
  (warm pool, Gulf Stream, Kuroshio, Tropical Atlantic, etc.) via qflux_mod
  (Jucker & Gerber 2017, Garfinkel et al. 2020).
- RRTM radiation with climatological ozone (ozone_1990) and 390 ppmv CO2.
- Betts-Miller convection and Monin-Obukhov boundary layer scheme.
- T42 horizontal resolution with 40 uneven sigma levels extending to ~0.1 hPa.
"""
import os

from isca import IscaCodeBase, DiagTable, Experiment, Namelist, GFDL_BASE

NCORES = 16
RESOLUTION = 'T42', 40
NUM_MONTHS = 6

cb = IscaCodeBase.from_directory(GFDL_BASE)

exp = Experiment('mima_qflux_test', codebase=cb)
exp.clear_rundir()

exp.inputfiles = [os.path.join(GFDL_BASE, 'input/rrtm_input_files/ozone_1990.nc')]

diag = DiagTable()
diag.add_file('atmos_monthly', 30, 'days', time_units='days')
diag.add_field('dynamics', 'ps', time_avg=True)
diag.add_field('dynamics', 'bk')
diag.add_field('dynamics', 'pk')
diag.add_field('atmosphere', 'precipitation', time_avg=True)
diag.add_field('mixed_layer', 't_surf', time_avg=True)
diag.add_field('mixed_layer', 'flux_oceanq', time_avg=True)
diag.add_field('dynamics', 'sphum', time_avg=True)
diag.add_field('dynamics', 'ucomp', time_avg=True)
diag.add_field('dynamics', 'vcomp', time_avg=True)
diag.add_field('dynamics', 'temp', time_avg=True)
diag.add_field('dynamics', 'vor', time_avg=True)
diag.add_field('dynamics', 'div', time_avg=True)
diag.add_field('rrtm_radiation', 'co2', time_avg=True)
diag.add_field('damping', 'udt_cgwd', time_avg=True)  # cg_drag zonal wind tendency
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

    'idealized_moist_phys_nml': {
        'do_damping': True,
        'turb': True,
        'mixed_layer_bc': True,
        'do_virtual': False,
        'do_simple': True,
        'roughness_mom': 3.21e-05,
        'roughness_heat': 3.21e-05,
        'roughness_moist': 3.21e-05,
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
    }
})

exp.set_resolution(*RESOLUTION)

if __name__ == '__main__':
    cb.compile()
    exp.run(1, use_restart=False, num_cores=NCORES)
    for i in range(2, NUM_MONTHS + 1):
        exp.run(i, num_cores=NCORES)
