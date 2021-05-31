''' Copyright 2021 David Rodriguez

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

	http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Script to install required plugins for PyYoloCR. Tested on Windows 10. It assumes it was launched with privileges.
'''

from typing import Optional, List
from pathlib import Path

def get_VS_dir_from_PATH( PATH: List[str] ) -> Optional[Path]:
    # Get elements of PATH that contain 'VapourSynth'
    VS_PATH = [ Path(s).resolve() for s in PATH if s and 'VapourSynth' in s ]
    if VS_PATH and len(VS_PATH)<1:
        return None
    
    # try: check if a path like '[...]VapourSynth[...]plugins' exists in PATH
    plugin_candidate_dir = [ p for p in VS_PATH if p.parts[-1]=='plugins' and p.parts[-2]=='VapourSynth' ]
    if plugin_candidate_dir and 0 < len(plugin_candidate_dir):
        return plugin_candidate_dir[0]

    # try to deduce 'plugins' dir from other VapourSynth folders
    for p in VS_PATH:
        # try: p is root dir of VapourSynth
        if p.parts[-1]=='VapourSynth':
            plugin_dir = ( p / 'plugins' ).resolve()
            if plugin_dir.is_dir():
                return plugin_dir

        # try: p is 'core'/'vsrepo' subdir of VapourSynth
        if not ( (p / 'vsrepo.py').is_file() or (p / 'vspipe.exe').is_file() or p.parents[0]=='VapourSynth' ):
            continue
        plugin_dir = ( p.parents[0] / 'plugins' ).resolve()
        if plugin_dir.is_dir():
            return plugin_dir

def main():
    from pprint import pprint
    import sys

    system_path_f = Path('./PATH.log')
    assert system_path_f.is_file()
    system_path = system_path_f.read_text().split(';')
    python_path = [ Path(p) for p in sys.path ]

    # Finding 'all users' python 'site-packages' location
    python_site_packages = list( filter( lambda s: ('Program Files' in s.parts and 'site-packages'==s.parts[-1]), python_path ) )
    assert python_site_packages and len(python_site_packages)==1, f"ERROR: could not identify 'site-packages' location with python_path={python_path}"
    python_site_packages = python_site_packages[0]

    # Finding VapourSynth plugins folder
    vapoursynth_location = "C:\\Program Files\\VapourSynth\\"
    vapoursynth_plugins_location = f"{vapoursynth_location}\\plugins"
    if not Path( vapoursynth_plugins_location ).is_dir():
        print( f"ERROR: Vapoursynth should be in '{vapoursynth_plugins_location}' but wasn't !" )
        print( "Using alternative method to find VapourSynth plugins folder .." )
        vapoursynth_plugins_location = get_VS_dir_from_PATH( system_path )
        assert vapoursynth_plugins_location and vapoursynth_plugins_location.is_dir(), "ERROR: Alternative location method failed !"
    

    # Creating the command used to install plugins, then executing it
    plugins2install = [ 'ffms2', 'havsfunc', 'mvsfunc', 'adjust' ]
    cmd = f'vsrepo.py install {" ".join(plugins2install)} -b "{vapoursynth_plugins_location}" -s "{python_site_packages}"'
    import os
    os.system( cmd )

if __name__=="__main__":
    main()
