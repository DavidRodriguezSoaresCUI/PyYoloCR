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
'''

from typing import List, Union
from pathlib import Path
import multiprocessing as mp
import pytesseract
import re

def OCR_Tesseract( arg ) -> dict:
    img, lang, Tesseract_CFG = arg
    tmp = {
        k:v[4:]
        for k,v in pytesseract.image_to_data( 
            str(img),
            lang=lang,
            config=Tesseract_CFG,
            output_type=pytesseract.Output.DICT
        ).items()
        if k=='conf' or k=='text' or k=='line_num'
    }
    _len_txt = len(tmp['text'])
    assert len(tmp['conf']) == _len_txt
    tmp['len'] = _len_txt
    return tmp

def OCR_scene( scene_id: int, lang: str ) -> str:
    f = OCR_Tesseract
    args = [
        ( img, lang, Tesseract_CFG )
        for img in filteredScreensDir.glob(f"primary_scene{scene_id}-*.jpg") 
    ]
    _thr = int(_getThreads() * .8)
    pool = mp.Pool(processes=_thr)
    return pool.map( f, args )

    # return [ 
    #     OCR_Tesseract( img, lang ) 
    #     for img in filteredScreensDir.glob(f"primary_scene{scene_id}-*.jpg") 
    # ]

def execute( call: Union[str,List[str]] ) -> dict():
    from subprocess import Popen, STDOUT, PIPE
    try:
        stdX = Popen(
            call,
            stdout=PIPE, 
            stderr=STDOUT
        ).communicate()
    except Exception as e:
        logging.getLogger('YoloCR').error(f"execute: the following error was raised when executing {call} : {e}")
        stdX = [None]*2
    names = ['stdout','stderr']
    return {
        names[i]:(stdX[i].decode('utf8') if stdX[i] else None)
        for i in range(2)
    }


def debugvar( v, vname ):
    # Useful for developpers, gives various infos about a variable
    print(f"DEBUG: {vname}={v} ({type(v)})")


def ensure_min_python( min_ver: List[int] = [3,6] ):
    # Raise error on older Python versions
    import platform
    curr_ver_s = platform.python_version()
    curr_ver = [ int(s) for s in curr_ver_s.split('.')[0:2] ]
    
    _len = min(len(curr_ver),len(min_ver))
    for i in range(_len):
        assert curr_ver[i]>=min_ver[i], f"Current python interpreter is too old ({curr_ver_s}<{'.'.join([str(s) for s in min_ver])}) ! "


def __input( msg: str ) -> str:
    try:
        return input(msg)
    except KeyboardInterrupt:
        import sys
        print("\nKEYBOARDINTERRUPT")
        sys.exit(1)


def choose( choices: List[str], msg: str = 'Choice' ) -> str:
    while True:
        print(f"Choices : ")
        for i,c in enumerate(choices):
            print(f"[{i}] {c}")
        try:
            return choices[int(__input(f"{msg} : "))]
        except ValueError:
            print("Invalid choice")
        except IndexError:
            print("Invalid choice")


def check_ext_programs() -> None:
    ''' Ensures required and optional external programs can be called, and display their version.
    Exits on error with required programs.
    Returns GUI mode [bool]
    '''

    software_not_found_msg = lambda x: f"Could not retrieve {x[0]}'s version. Make sure it is installed on this system and '{' '.join(x)}' can be called on your shell." if isinstance(x,list) else f"Could not retrieve {x[0][0]}'s version. Make sure it is installed on this system and `{'` or `'.join(' '.join(y) for y in x)}` can be called on your shell."

    def no_mandatory_prg( __call ):
        LOG.error( software_not_found_msg(__call) )
        sys.exit(1)

    programs = [
        {
            'call': [ 'ffmpeg', '-version' ],
            're.version': r'ffmpeg version (\d[\d.\-]+\d)',
            'failure': no_mandatory_prg
        },
        {
            'call': [ 'ffprobe', '-version' ],
            're.version': r'ffprobe version (\d[\d.\-]+\d)',
            'failure': no_mandatory_prg
        },
        {
            'call': ([ 'tesseract', '-v' ], [ 'tesseract', '--version' ]),
            're.version': r'tesseract v?([\d.]+)',
            'failure': no_mandatory_prg
        }
    ]

    def check_program( prg, __call ):
        stdX = execute( __call )
        try:
            version = re.search( prg['re.version'], stdX['stdout'] ).group(1)
            assert version and (stdX['stderr'] is None)
        except Exception as e:
            LOG.error( e )
            return
        return version


    for prg in programs:
        __call = prg['call']
        if isinstance( __call, tuple ):
            prg_name = __call[0][0]
            for __alt_call in __call:
                version = check_program( prg, __alt_call )
                if version:
                    break
        else:
            prg_name = __call[0]
            version = check_program( prg, __call )
        if version:
            LOG.info( f"Found {prg_name} {version} !" )
            continue
        prg['failure']( __call )
        


def frame2timestamp_SRT( frame, fps ):
    s = frame/fps
    import time
    return time.strftime("%H:%M:%S,", time.gmtime(s)) + f"{int(1000*(s-int(s))):03d}"


def frame2timestamp( frame, fps ):
    s = frame/fps
    # return f"{int(s//3600):02d}h{int((s%3600)//60):02d}m{int(s%60):02d}s{int(1000*(s-int(s))):03d}"
    import time
    return time.strftime("%Hh%Mm%Ss", time.gmtime(s)) + f"{int(1000*(s-int(s))):03d}"


class Interval:
    def __init__(self, a: int, b: int ) -> None:
        assert a < b and isinstance(a,int) and isinstance(b,int)
        self.a = a
        self.b = b

    @classmethod
    def from_list( cls, l: List[int], min_interval: int = 1, split_list: List[int] = None ) -> List:
        a = b = None
        intervals = set()

        for i in l:
            if a is None:
                # Interval begins
                a = b = i
                continue

            if i==b+1: #i > b and i <= b+3:
                # Interval continues : accepts "gaps" up to 2-wide
                b = i
                continue
            
            # Interval ends
            if a + min_interval <= b:
                intervals.add( Interval( a, b ) )
            else:
                LOG.warning(f"Discarded interval : [{a},{b}]")
            a = b = i

        if a and a + min_interval <= b:
            # Last Interval ends
            intervals.add( Interval( a, b ) )

        # Applying `split_list`
        def interval2split( i ):
            for interval in intervals:
                if interval.contains( i ):
                    return interval

        split_list_useful = 0
        for split_i in split_list:
            interval_to_split = interval2split( split_i )
            if interval_to_split is None:
                continue
            # `split_i` in `interval`
            tentative_split = interval_to_split.split( split_i, min_interval )
            if tentative_split is None:
                continue
            # successful split : replace `interval_to_split` with intervals in `tentative_split` in `intervals`
            LOG.debug(f"Split interval : {repr(interval_to_split)} -> {repr(tentative_split[0])} + {repr(tentative_split[1])}")
            split_list_useful += 1
            intervals.discard( interval_to_split )
            intervals.add( tentative_split[0] )
            intervals.add( tentative_split[1] )

        LOG.debug( f"No interval was split from 'split_list' :(" if split_list_useful==0 else f"{split_list_useful} interval(s) were split from 'split_list' !" )

        return list( sorted( intervals, key=lambda x: x.a ) )


    @classmethod
    def join( cls, intervals:list ):
        return Interval( intervals[0].a, intervals[-1].b)

    @property
    def len( self ):
        return self.b-self.a

    def contains( self, val, inclusive: bool = True ):
        return (self.a <= val and val <= self.b) if inclusive else (self.a < val and val < self.b)

    def split( self, at: int, min_interval: int = 1 ) -> List:
        ''' [a,b] -> [a,at-1], [at,b] '''
        if not self.contains( at, inclusive=False ):
            return None
        
        try:
            res = [ Interval(self.a,at-1), Interval(at,self.b) ]
        except AssertionError:
            return None 
        if all( [ interval.len >= min_interval for interval in res ] ):
            return res

    def __repr__( self ):
        return f"{self.a}->{self.b}"

    def timestamp_SRT( self, fps: float ) -> str:
        return ' --> '.join(
            [
                frame2timestamp_SRT(x, fps)
                for x in [self.a,self.b]
            ]
        )

    def timestamp( self, fps: float ) -> str:
        return '-'.join(
            [
                frame2timestamp(x, fps)
                for x in [self.a,self.b+1]
            ]
        )

    def add_padding( self, padding: int ):
        self.a -= padding
        self.b += padding
        

def guess_text( ocr_data ):
    # new line detection
    def detect_value_increment( values ):
        return [
            i
            for i in range(len(values)-1)
            if values[i] < values[i+1]
        ]

    # 1st : not every OCR'd frame has same text length, so we only keep those with popular word count
    from statistics import mode
    text_length = mode( [ x['len'] for x in ocr_data ] )
    ocr_data = list( filter( lambda x: x['len']==text_length, ocr_data) )

    # 2nd : We assume that every frame tried to read the same words. 
    # Then, for each word we choose the variation that has highest confidence
    from collections import defaultdict
    any2int = lambda x: x if isinstance(x,int) else ( int(x) if isinstance(x,float) else int(float(x)))
    words = [ defaultdict( lambda: 0 ) for _ in range(text_length) ]
    for frame in ocr_data:
        text, conf, newline_idx = frame['text'], frame['conf'], detect_value_increment(frame['line_num'])
        
        for i in range(text_length):
            _word = text[i] + ( '\n' if i in newline_idx else '' )
            (words[i])[ _word ] += any2int( conf[i] )

    guess_words = [
        max(word, key=word.get) # get word variation with highest combined confidence
        for word in words
    ]

    # Assemble words in phrase, with spaces and newlines
    guess_line = re.sub( r'\n\s+', r'\n', ' '.join( guess_words ) )

    return guess_line


def _getThreads():
    # from https://oxavelar.wordpress.com/2011/03/09/how-to-get-the-number-of-available-threads-in-python/
    """ Returns the number of available threads on a posix/win based system """
    import os,sys
    if sys.platform == 'win32':
        return (int)(os.environ['NUMBER_OF_PROCESSORS'])
    else:
        return (int)(os.popen('grep -c cores /proc/cpuinfo').read())


def deduplicate_subtitles( subtitles ):
    
    get_scene = lambda x: subtitles[x]['scene']
    get_text  = lambda x: subtitles[x]['text']
    nb_sub = len(subtitles)

    subtitles_ok = list()
    curr_sc = get_scene(0)
    curr_tx = get_text(0)
    for i in range(1, nb_sub):
        tmp_txt = get_text(i)
        if tmp_txt!=curr_tx:
            # curr_subtitle ended
            subtitles_ok.append( {
                'scene': curr_sc,
                'text' : curr_tx
            })
            curr_sc = get_scene(i)
            curr_tx = tmp_txt
        else:
            # joining subtitles
            curr_sc = Interval.join( [ curr_sc, get_scene(i) ] )
    
    # Ending last subtitle
    subtitles_ok.append( {
        'scene': curr_sc,
        'text' : curr_tx
    })

    return subtitles_ok
    

def subtitle_normaization( txt: str, lang: str ) -> str:
    # Here is the section dedicated to correcting common OCR mistakes
    # Notice : substitutions that correct the original text (eg. that correct accents on capitals in french) are to be avoided, as not the focus of this section
    res = txt

    # Duplicated whitespace
    res = re.sub( r'\s{2,}', ' ', res )
    # Double/simple quote normalization
    res = res.replace( '”', '"' )
    res = res.replace( '‘', "'" )
    # More symbols
    res = res.replace('’', "'")
    res = res.replace('—','-')
    res = res.replace('.…','…')
    res = res.replace('….','…')
    res = res.replace('...','…')
    # Merged characters(character ligature)
    res = res.replace('ﬁ','fi')
    res = res.replace('ﬂ','fl')

    if lang=='eng':
        # Malformed 'I' capitalization (or l)
        res = res.replace('|', 'I')
        res = res.replace('|', 'I')
        res = re.sub(r'^l','I', res)
        res = re.sub(r'1([a-z])','I\1', res)
    if lang=='fra':
        res = res.replace('II','Il')
        res = res.replace('||','Il')
        res = re.sub(r'([a-zA-Z])\s\'([a-zA-Z])','\1\'\2', res)

        
    return res


if __name__=='__main__':
    # Necessary in Windows for multiprocessing
    mp.freeze_support()

    img_fmt = 'jpg'  # 'bmp' and 'png' are technically available from FFmpeg but not recommended because slower and/or heavier
    sub_padding = 0  # Padding for subtitles, in frames. May be useful for very slow fading subtitles. This feature has become deprecated thanks to better subtitle detection but is left here just in case.
    Dev_mode = False # Outputs debug files and messages, for developpers

    # Require Python >=3.6
    ensure_min_python( [3,6] )

    try:
        import pytesseract
        from PIL import Image
        from progress.bar import Bar
    except ImportError as e:
        raise ImportError(f"The following error occurred : '{e}'. This may be caused by missing required libraries. Please run 'python3 -m pip install -r requirements'.")
    import sys,re

    import logging
    logging.basicConfig( level=(logging.DEBUG if Dev_mode else logging.INFO ) )
    LOG = logging.getLogger( "YoloCR" )
    
    from pprint import pformat
    from math import floor


    # dealing with arguments
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--engine",
        action='store',
        nargs=1,
        default=None,
        choices=['legacy','LSTM','legacy+LSTM'],
        help="Select Tesseract engine."
    )
    parser.add_argument(
        "-l",
        action='store',
        nargs=1,
        default=None,
        metavar='lang',
        help="Select Tesseract language."
    )
    parser.add_argument(
        "--overwrite",
        action='store_true',
        default=False,
        help="Overwrite extracted frames."
    )
    args = parser.parse_args()

    # Retrieve tesseract langs
    local_tessdata = Path('./tessdata')
    Tesseract_mode_CFG = {
        'Use legacy engine only': {
            'cfg': f"--oem 0 --psm 6",
            'tag': 'legacy'
        },
        'Use Neural nets LSTM engine only': {
            'cfg': "--oem 1 --psm 6",
            'tag': 'LSTM'
        },
        'Use legacy+LSTM engines': {
            'cfg': "--oem 2 --psm 6",
            'tag': 'legacy+LSTM'
        },
        'Use default engine': {
            'cfg': "--oem 3 --psm 6",
            'tag': 'default'
        }
    }
    k = 'Use default engine'
    Incl_lang = pytesseract.get_languages(config='')
    Local_lang = list()
    if local_tessdata.is_dir():
        # Ask user for Tesseract mode
        Local_lang = [ lang_file.stem for lang_file in local_tessdata.glob('*.traineddata') ]
        if Local_lang:
            if args.engine:
                k = [ n for n in Tesseract_mode_CFG.keys() if Tesseract_mode_CFG[n]['tag']==args.engine[0] ][0]
            else:
                k = choose( list(Tesseract_mode_CFG.keys()), msg="Please choose a mode for Tesseract-OCR" )
    
    T_mode = Tesseract_mode_CFG[k]['tag']
    Tesseract_CFG = Tesseract_mode_CFG[k]['cfg']
    print()
    
    # Ask user for language : limited to local ./tessdata lang files for "legacy" engine
    T_lang = list(set(Local_lang + Incl_lang)) if ('LSTM' in T_mode) else Local_lang
    assert T_lang and len(T_lang)>0
    if args.l and args.l[0] in T_lang:
        lang = args.l[0]
    else:
        lang = choose( T_lang, msg="Choose a language for Tesseract OCR" )
    LOG.info(f"Selected language : {lang}")
    if lang in Local_lang:
        Tesseract_CFG += f' --tessdata-dir "{local_tessdata.as_posix()}"'
    print()

    # filtered video file
    video = Path('Filtered_video.mp4').resolve()
    LOG.info(f"Selected video file : {video}\n")


    # Check for external programs
    LOG.info("Checking for external dependencies ..")
    check_ext_programs()    
    LOG.info("Checking for external dependencies OK\n")
            

    # `FilteredScreens` : if exist, remove all `img_fmt` files, else mkdir.
    generate_screens = True
    LOG.info("Preparing folder for screens ..")
    filteredScreensDir = Path('FilteredScreens').resolve()
    if filteredScreensDir.is_dir():
        LOG.info(f"Found {filteredScreensDir}")
        files2remove = list(filteredScreensDir.glob(f'*.{img_fmt}'))
        if files2remove:
            if args.overwrite or input(f"Remove the {len(files2remove)} {img_fmt.upper()} files from {filteredScreensDir} ? (y/n) : ")=='y':
                LOG.info(f"Removing {len(files2remove)} {img_fmt.upper()} files from {filteredScreensDir} ..")
                for f in files2remove:
                    f.unlink()
            else:
                generate_screens = False 

    else:
        LOG.info(f"Created {filteredScreensDir}")
        filteredScreensDir.mkdir()
    LOG.info("Preparing folder for screens OK\n")



    # Use ffprobe to obtain FPS for video file
    # stdX = execute( ["ffprobe", str(video), '-v ', '-select_streams v', '-print_format flat', '-show_entries stream=r_frame_rate'] )
    ffprobe_FPS_stdX = execute( ["ffprobe", '-v', '0', '-select_streams', 'v', '-print_format', 'flat', '-of', 'default=noprint_wrappers=1:nokey=1', '-show_entries', 'stream=r_frame_rate', str(video)] )
    assert ffprobe_FPS_stdX['stdout'] and ffprobe_FPS_stdX['stderr'] is None
    video_FPS = eval(ffprobe_FPS_stdX['stdout'].rstrip())


    # Scene Detection : Combination of stats : NonBlackFrames and SceneChanges
    stat_nonblackframes_f = Path('stat_nonblackframes.log')
    assert stat_nonblackframes_f.is_file()
    stat_nonblackframes = [ int(s) for s in stat_nonblackframes_f.read_text().splitlines() if s ]
    stat_scenechanges_f = Path('stat_scenechanges.log')
    assert stat_scenechanges_f.is_file()
    stat_scenechanges = [ int(s) for s in stat_scenechanges_f.read_text().splitlines() if s ]
    scenes = Interval.from_list(stat_nonblackframes, min_interval=int(video_FPS*.5), split_list=stat_scenechanges )
    print(f"Found {len(scenes)} scenes")

    # Extracting frames for all scenes
    out_file_fmt = str( filteredScreensDir / (r'{}_scene{}-{}.'+img_fmt) )
    out_file = lambda label,sceneidx: out_file_fmt.format( label, sceneidx, '%d' )

    # Acceleration : limit the number of frames to extract from the video. Use modulo to extract frames consistently (not all from beginning/end of scene).
    # The 'frame objective' is a threshold to limit the number of frames to extract below the set number. Scenes with >frame_objective frames will be clamped to [ frame_objective/2, frame_objective ] frames
    frame_objective = 30

    def scene_mod( scene ):
        if not frame_objective:
            return 1
        return max(1,floor(scene.len/(frame_objective/2)))

    def scene_len( scene ):
        if not frame_objective:
            return scene.len
        return len([ i for i in range(scene.a,scene.b) if i%scene_mod(scene)==0 ])

    res = [
        [
            'ffmpeg', 
            '-i', str(video),
            '-vf', f"select=between(n\,{scene.a}\,{scene.b})*eq(mod(n\,{scene_mod(scene)})\,0)",
            '-frames', str(scene_len(scene)),
            '-vsync', '0',
            out_file( 'primary', idx )
        ]
        for idx,scene in enumerate(scenes)
    ]
    import time
    if generate_screens:
        start_time = time.time()
        nbFrames2extract = sum([ scene_len(sc) for sc in scenes ])
        LOG.info(f"Extracting {nbFrames2extract} frames from video ..")
        if not Dev_mode:
            bar = Bar('Processing scenes', max=len(res))
        for idx,__call in enumerate(res):
            LOG.debug( f"Processing scene {idx} ({scenes[idx].len} frames, timestamp={scenes[idx].timestamp(video_FPS)}) .." )
            if not Dev_mode:
                bar.next()
            execute( __call )
        if not Dev_mode:
            bar.finish()

        LOG.info(f"Extracting {nbFrames2extract} frames from video in {time.time() - start_time}s.")

    # Finereader section : TODO
    # Windows: Find `Finereader.exe`. If found, make the user choose OCR engine.
    # `HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App\ Paths\\FineReader.exe /ve`

    # OCR with Tesseract : use pytesseract
    # check every OCR result for '<em>' : display image with sxiv and ask user "Is it italic (y/n) ? "
    # Note : uses `xdotool` to maintain CLI active (QOL)

    # subtitles = [
    #     ( scene.timestamp(video_FPS) , OCR_scene(idx) )
    #     for idx,scene in enumerate(scenes)
    # ]

    print()
    subtitles = None
    # Caching for performance, typically for developper
    subtitles_cache_file = Path(f'Tesseract-OCR.subdata.{T_mode}.{lang}.pickle')
    import pickle
    if Dev_mode and subtitles_cache_file.is_file():
        with subtitles_cache_file.open("rb") as f:
            subtitles = pickle.load( f )

    if subtitles is None:
        subtitles = [ None for _ in range(len(scenes)) ]
        start_time = time.time()
        if not Dev_mode:
            bar = Bar( message="OCR with Tesseract", max=len(scenes))
        for idx,scene in enumerate(scenes):
            LOG.debug( f"OCR scene {idx} .." )
            subtitles[idx] = {
                'scene': scene ,
                'text' : OCR_scene(idx, lang)
            }
            if not Dev_mode:
                bar.next()
        if not Dev_mode:
            bar.finish()
        LOG.info(f"OCR done in {time.time() - start_time}s.")
        if Dev_mode:
            LOG.info(f"OCR caching results ({subtitles_cache_file}).")
            with subtitles_cache_file.open("wb") as f:
                pickle.dump( subtitles, f )
    else:
        LOG.info(f"OCR cache hit ({subtitles_cache_file}).")

    if Dev_mode:
        Path('debug.ocr_data.log').write_text(pformat(subtitles), encoding='utf8')
    
    # guess scene text from OCR'ed frame text
    for __s in subtitles:
        __s['text'] = guess_text( __s['text'] )
        
    
    # Applying corrections
    for subtitle in subtitles:
        subtitle['text'] = subtitle_normaization( subtitle['text'], lang )        
    
    if Dev_mode:
        Path('debug.subtitles.log').write_text(pformat(subtitles), encoding='utf8')

    # De-duplicate subtitles
    subtitles = deduplicate_subtitles( subtitles )
    if Dev_mode:
        Path('debug.sub_deduplicated.log').write_text(pformat(subtitles), encoding='utf8')


    # Add Padding to subtitles
    if sub_padding:
        for subtitle in subtitles:
            subtitle['scene'].add_padding(sub_padding)
    

    # Writing subtitles to file
    subtitle_file = Path( f"output.{Tesseract_mode_CFG[k]['tag']}.{lang}.srt" )
    LOG.info( f"\nWriting subtitle file {subtitle_file} .." )
    SRT_format = lambda idx,ts,s: f"{idx+1}\n{ts}\n{s}\n\n"
    # Note : SRT requires Windows-style line ending (http://www.textfiles.com/uploads/kds-srt.txt)
    with subtitle_file.open("w+",encoding='utf8', newline='\r\n') as f:
        for idx,s in enumerate(subtitles):
            f.write( 
                SRT_format( idx, s['scene'].timestamp_SRT(video_FPS), s['text'] )
            )
    LOG.info( f"Writing subtitle file {subtitle_file} OK" )

        
    
    sys.exit(0)

    # Post-processing : adding '\n' when necessary, dealing with empty subtitles, etc

    # Alternative : OCR with FineReader :
    # ???







