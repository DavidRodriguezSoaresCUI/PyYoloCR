
def main( argv ):
    from pprint import pprint
    from pathlib import Path

    system_path = argv[1].split(';')
    python_path = sys.path

    # Finding 'all users' python 'site-packages' location
    python_site_packages = list( filter( lambda s: ('Program Files' in s and 'site-packages' in s), python_path ) )
    assert python_site_packages and len(python_site_packages)==1, f"ERROR: could not identify 'site-packages' location with python_path={python_path}"
    python_site_packages = python_site_packages[0]

    # Finding 'all users' python 'site-packages' location
    vapoursynth_location = "C:\\Program Files\\VapourSynth\\"
    vapoursynth_plugins_location = f"{vapoursynth_location}\\plugins"
    assert Path( vapoursynth_plugins_location ).is_dir(), f"ERROR: Vapoursynth should be in '{vapoursynth_plugins_location}' but wasn't !"

    plugins2install = [ 'ffms2', 'havsfunc', 'mvsfunc', 'adjust' ]

    cmd = f'vsrepo.py install {" ".join(plugins2install)} -b "{vapoursynth_plugins_location}" -s "{python_site_packages}"'
    import os
    os.system( cmd )

if __name__=="__main__":
    import sys
    main(sys.argv)