pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir  = pkgdatadir / 'alusin_studio'
icondir    = meson.project_source_root() / 'data' / 'icons' / 'hicolor'
acticondir = icondir / 'scalable' / 'actions'

gnome = import('gnome')

gnome.compile_resources(
  'alusin-studio',
  'alusin-studio.gresource.xml',

  gresource_bundle: true,
        source_dir: [acticondir],
           install: true,
       install_dir: pkgdatadir,
)

python = import('python')

conf = configuration_data()
conf.set(    'PYTHON', python.find_installation('python3').full_path())
conf.set(   'VERSION', meson.project_version())
conf.set( 'localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
          input: 'alusin-studio.in',
         output: 'alusin-studio',
  configuration: conf,
        install: true,
    install_dir: get_option('bindir'),
   install_mode: 'rwxr-xr-x'
)

sources = [
  '__init__.py',
  'main.py',
  'window.py',
]

install_data(sources, install_dir: moduledir)
