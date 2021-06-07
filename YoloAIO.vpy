''' VapourSynth script for the PyYoloCR project, used for subtitle extraction in conjunction with OCR software.
Based on scripts written by Bitbucket user YuriZero for the YoloCR project

Notes :
 - If you use VapourSynth Editor and experience crashes on launching Preview while on Step==1, then use workaround by first launching Preview while on Step==0; Step 1 should work after that. This is a VSEditor bug, I can't do much about this.
 - Untested : ModeS other than 'L'; ModeU other than 'sinc'; Subtitles that are not white with black outline or black with white outline

Copyright 2021 David Rodriguez

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

# Importing YoloAIO helper script
from pathlib import Path; import sys, importlib; from importlib import reload
sys.path.append(str(Path('.').resolve()))
import YoloAIO
YoloAIO = reload(YoloAIO)
Color, makeMOD2, ordinal_expr = YoloAIO.Color, YoloAIO.makeMOD2, YoloAIO.ordinal_expr


#################################### Adjustment Variables ####################################

VideoSrc=r'!!!VIDEO_FILE_HERE!!!'

# Main adjustment variables : finding good values is essential
Step=3 # 0:VapourSynth crash workaround, 1:Resize, 2:Seuil, 3:CR
# Step 1 : adjusting bounding box for subtitles
CropBoxDimension=[0.9,0.2]  # in [0,1]; Width, Height of box for subtitles
CropBoxElevation=0.04       # in [0,1-CropBoxDimension[1]]; How "high" (far from the bottom) should the text box be
# Step 2 : adjusting threshold for text extraction
# Color : describes color of text font. Accepts 'white', 'black', [R,G,B] (ex:[255,30,44])
# SeuilI : (for 'white'/'black') typically in [170,230]; Minimum luminance threshold for subtitle insides. Optimization : Maximize while keeping all characters readable. Characters deformed/too "skinny" suggest value is too high.
# SeuilO : (for 'white'/'black') typically in [20,120]; Maximum luminance threshold for subtitle outline. Optimization : Minimize while keeping all characters visible. Characters popping in and out of visibility or accent/punctuation invisible means value is too low
# marginRel/marginAbs : (for RGB colors) in [0,0.5] and [0,100] respectively; relative and absolute margins around 'color', to filter the colored text.
# FontColors : color, SeuilI: int = 200, SeuilO: int = 90, marginRel: float = 0.25, marginAbs: int = 25
FontColors = [
	Color( [ 210, 34, 180 ] ),
	Color( [ 198, 34, 40 ], marginRel = 0.1, marginAbs = 40 ),
	Color( 'black', SeuilI=190, SeuilO=80 )
]
SelectColor = None # In Step 2, set to None to see RGB output, or color index (0,1,..) to see binarized result
# Step 3 : See output to check previously set values are good (subtitles are readable and there are not too many artifacts)


# Other variables
SeuilSCD = 0.03    # (default: 0.03 = 3%) Scene change threshold. Too low a value result in false positive scene changes (typically not an issue), too high causes some subtitles to not be identified/separated.
MinTextThr = 0.01 # (default: 0.01 = 1%) Minimum amount of a frame to be Binarized positive to count as a frame containing text. Lower it if some small phrases go undetected.
ModeU    = 'sinc' # Upscaling method : 'sinc' (2 taps, faster), 'znedi3' (slower) ou 'waifu2x' (way slower)
SubtitleDetectionInterval=None # Set to [a,b] for subtitle detection to only be active between frame a and frame b; Useful to avoid picking up on Intro/outro.
Stat_debug = False # Used on Step==3; Set to False when producing video; Mainly for developper, allows to check subtitle alignment stats and disables stat file writes

#################################### Adjustment Variables ####################################



assert SelectColor is None or SelectColor in range(len(FontColors)), f"Error : SelectColor={SelectColor} not in [0,{len(FontColors)-1}] !"

# Verifying necessary imports
try:
	import havsfunc as haf
	from pprint import pprint
	import functools
	import os
	from pathlib import Path
	import vapoursynth as vs
	if ModeU=='znedi3':
		import edi_rpow2 as edi
except ImportException as e:
	raise ImportException(f"Error while trying to import required plugins and libraries : {e}\nYou may have not installed them properly.")

# Verifying video source
video_source = Path(VideoSrc)
assert video_source.is_file()
core=vs.get_core()
try:
	Clip=core.ffms2.Source(source=VideoSrc)
except AttributeError as e:
	raise AttributeError(f"The following error was raised : '{e}'\nYou may have forgotten/failed to install PyYoloCR required VapourSynth plugins !")
	


###########################################################
# percentage -> int conversion
# added black borders for subs too close to the border
Clip = core.std.AddBorders( Clip, 8,8,8,8 )
CropBoxDimension[0] = makeMOD2( int(CropBoxDimension[0] * Clip.width) )
CropBoxDimension[1] = makeMOD2( int(CropBoxDimension[1] * Clip.height) )
CropBoxElevation = makeMOD2( CropBoxElevation * Clip.height )
# CropBoxElevation must be a mod2 strictly positive integer
if CropBoxElevation == 0:
	CropBoxElevation += 2
LeftCropBox = makeMOD2( int((Clip.width-CropBoxDimension[0])/2) )
###########################################################


def SSdecision( Clip, Supersampling=-1 ):
	if Supersampling<0:
		if Clip.width/Clip.height>16/9:	
			TargetRes=1920
			CurrentRes=Clip.width	
		else:
			TargetRes=1080
			CurrentRes=Clip.height
		if ModeU=='znedi3':
			Ss=TargetRes/CurrentRes/1.125	
		else:
			Ss=TargetRes/CurrentRes
	elif Supersampling==0:
		Ss=1
	else:
		Ss=Supersampling
	
	Ssbis = None
	if ModeU=='znedi3' and Ss!=1:
		if Ss-int(Ss)>0:
			Ss=int(Ss/2)*2+2
		else:
			Ss=int(Ss/2)*2
		if Supersampling<0:
			Ssbis=TargetRes/(CurrentRes*Ss)
		else:
			Ssbis=Supersampling/Ss

	return Ss, Ssbis
	

def YUV2RGB( YUVclip ):
	# Simplistic YUV2RGB for color plane extraction
	c = core.fmtc.resample(clip=YUVclip, css="444")
	c = core.fmtc.matrix(clip=c, mat="709", col_fam=vs.RGB)
	return core.fmtc.bitdepth(clip=c, bits=8)


def SuperSampleClip( Clip, Ss, ModeU, Ssbis ):
	if Ss!=1:
		if ModeU=='znedi3' or ModeU=='waifu2x':
			if ModeU=='znedi3':
				Clip=edi.znedi3_rpow2(clip=Clip,rfactor=Ss)
			else :
				Clip=core.fmtc.bitdepth(clip=Clip,bits=32)
				Clip=core.w2xc.Waifu2x(clip=Clip,scale=Ss)
				if Ssbis!=1:
					Clip=core.fmtc.bitdepth(clip=Clip,bits=16)
				else :
					Clip=core.fmtc.bitdepth(clip=Clip,bits=8)
			if Ssbis!=1:
				Clip=core.fmtc.resample(clip=Clip,scale=Ssbis,kernel="sinc",taps=2)
				return core.fmtc.bitdepth(clip=Clip,bits=8)
		else:
			Clip=core.fmtc.resample(clip=Clip,scale=Ss,kernel="sinc",taps=2)
			return core.fmtc.bitdepth(clip=Clip,bits=8)
	elif Clip.format.bits_per_sample!=8:
		return core.fmtc.bitdepth(clip=Clip,bits=8)
	return Clip
	

		
def MergeClips( clips, normalize=False ):
	# Takes 2-26 clips of same format (all with vs.GRAY color family) and returns a merged clip
	assert all( [ c.format.color_family==vs.GRAY for c in clips ] )
	nb_clips = len(clips)
	assert nb_clips in range(2,27)
	
	# expression crafted to merge N clips toghether by adding pixel values (with 255 as maximum value)
	expr = 'x' + ''.join( 
		[
			f' {ordinal_expr(idx)} +'
			for idx,_ in enumerate(clips)
		])+ (
			f' {nb_clips} /' if normalize else ''		
		) + ' 255 min'
		
	return core.std.Expr(clips=clips,expr=[expr], format=vs.GRAY8)


def YuriZeroBinarize( clip, SeuilI, SeuilO ):
	assert isinstance( SeuilI, int ) and isinstance( SeuilO, int )

	# dependencies
	Blackclip=core.std.BlankClip(width=int(clip.width-20),height=int(clip.height-20),format=vs.GRAY8,color=0)
	Rect=core.std.AddBorders(clip=Blackclip,left=10,right=10,top=10,bottom=10,color=255)
	Blank=core.std.BlankClip(clip,format=vs.GRAY8)
	
	White_Raw=core.std.Binarize(clip=clip,threshold=SeuilI)
	Bright_Raw=core.std.Binarize(clip=clip,threshold=SeuilO)

	def minimum(x,y):
		return min(x,y)

	Bright_Out=core.std.Lut2(clipa=Bright_Raw,clipb=Rect,function=minimum)

	Bright_Not=core.misc.Hysteresis(clipa=Bright_Out,clipb=Bright_Raw)
	Bright_Not=core.std.Invert(Bright_Not)

	White_Txt=core.std.MaskedMerge(Blank,White_Raw,Bright_Not)

	White_Lb=haf.mt_inpand_multi(src=White_Txt,mode="ellipse")
	White_Lb=haf.mt_expand_multi(src=White_Lb,mode="ellipse")

	White_Ub=haf.mt_inpand_multi(src=White_Txt,sw=5,sh=5,mode="ellipse")
	White_Ub=haf.mt_expand_multi(src=White_Ub,sw=3,sh=3,mode="ellipse")
	White_Ub=core.std.Invert(White_Ub)

	White=core.std.MaskedMerge(Blank,White_Lb,White_Ub)
	White=core.misc.Hysteresis(clipa=White,clipb=White_Txt)

	ClipCleaning=core.std.MaskedMerge(Blank,White_Raw,White)
	ClipCleaning=core.std.Median(clip=ClipCleaning)
	
	return ClipCleaning


def binarize_RGB_from_color( RGBplanes, RGBcolor, text_info: int = 0 ):
	res = core.std.Expr( clips=RGBplanes, expr=RGBcolor.color_isolation_expression() )
	if 0 < text_info:
		# alignment : cast [1,..] to [1,9]
		res = core.text.Text( res, text=str(RGBcolor) + '\n' + RGBcolor.color_range(), alignment=((text_info-1)%9)+1 )
	return res
	
	
def ExtractColorPlanes( YUVclip, colors, debug=False ):
	are_colors_rgb = [ color.is_rgb for color in colors ]
	RGBclip = YUV2RGB( YUVclip ) if any( are_colors_rgb ) else None
	
	def ExtractRGBplanes( RGBclip ):
		# Step 1 : Extract color plane to monochrome plane
		planes = [ core.std.ShufflePlanes(clips=RGBclip, planes=i, colorfamily=vs.GRAY) for i in range(3) ]
		# Step 2 : properties cleanup (otherwise there will be errors)
		return [ core.std.SetFrameProp(plane, prop='_Matrix', delete=True) for plane in planes ]
		
	RGBplanes = ExtractRGBplanes( RGBclip ) if RGBclip else None
	Yclip     = None if all( are_colors_rgb ) else core.std.ShufflePlanes(clips=YUVclip, planes=0, colorfamily=vs.GRAY)
	
	def ExtractPlane( Yclip, RGBplanes, color ):
		if color.is_rgb:
			# DEPRECATED
			# plane_idx = {
			# 	'red'  :0,
			# 	'green':1,
			# 	'blue' :2
			# }[color.color]
			# other_planes_idx = { i for i in range(3) if i!=plane_idx }
			# clips = [ RGBplanes[plane_idx] ]
			# for i in other_planes_idx:
			# 	clips.append( RGBplanes[i] )
			# return core.std.Expr(clips, expr = ["x y - z - 0 max"], format=vs.GRAY8)
			
			return binarize_RGB_from_color( RGBplanes=RGBplanes, RGBcolor=color, text_info=3 if debug else 0 )
		elif color.color == 'white':
			return YuriZeroBinarize(Yclip, color.SeuilI, color.SeuilO)
		elif color.color == 'black':
			return YuriZeroBinarize( core.std.Invert(Yclip, planes=0), color.SeuilI, color.SeuilO )
		raise ValueaError(f"ExtractColorPlanes: Unexpected state: color={color} doesn't trigger a behavior.")
			
	return [ ExtractPlane( Yclip, RGBplanes, color ) for color in colors ]


	


Ss, Ssbis = SSdecision( Clip )

# Cropped clip, defined by CropBoxDimension, CropBoxElevation and video_source's dimensions
ClipTextBox = core.std.CropAbs(clip=Clip,width=CropBoxDimension[0],height=CropBoxDimension[1],left=LeftCropBox,top=Clip.height-CropBoxElevation-CropBoxDimension[1])



if Step==-1:
	# DEBUG
	#Wplane, Rplane, Bplane = ExtractColorPlanes( Clip, FontColors )
	#MergedClip = MergeClips( Planes )
	
	#RGBcolors = [
	#	,
	#]
	#RGBclip = YUV2RGB( Clip )
	#planes = [ core.std.ShufflePlanes(clips=RGBclip, planes=i, colorfamily=vs.GRAY) for i in range(3) ]
	#planes = [ core.std.SetFrameProp(plane, prop='_Matrix', delete=True) for plane in planes ]
	
	
	#Path('debug.log').write_text( RGBcolor.color_range() )
	#sys.exit(0)
	#expr = RGBcolor.color_isolation_expression()
	#text_info = str(RGBcolor) + '\n' + RGBcolor.color_range()
	#ClipFiltered = core.text.Text( core.std.Expr(clips=planes, expr=expr), text=text_info, alignment=5 )
	#clips_binarized_from_colors = [
	#	binarize_RGB_from_color( planes, RGBcolor, text_info = idx+1 )
	#	for idx,RGBcolor in enumerate(RGBcolors)
	#]
	
	
	#Clip=core.text.ClipInfo(clip=MergeClips( clips_binarized_from_colors ))
	#Clip=core.text.ClipInfo(clip=RGBclip)
	#Clip.set_output()
	pass
	

elif Step in [0,1]:

	def Grayuv(x):
		return 128

	CropBox=core.std.CropAbs(clip=Clip,width=CropBoxDimension[0],height=CropBoxDimension[1],left=LeftCropBox,top=Clip.height-CropBoxElevation-CropBoxDimension[1])
	ClipGray=core.std.Lut(clip=Clip,planes=[1,2],function=Grayuv)
	
	ClipLeft=core.std.Crop(clip=ClipGray,right=int((CropBox.width+ClipGray.width)/2))
	ClipRight=core.std.Crop(clip=ClipGray,left=ClipLeft.width+CropBox.width)
	Clip=core.std.CropAbs(clip=ClipGray,width=CropBox.width,height=ClipGray.height,left=int((ClipGray.width-CropBox.width)/2))
	ClipTop=core.std.Crop(clip=Clip,bottom=int(CropBoxElevation*Ss)+CropBox.height)
	ClipBottom=core.std.Crop(clip=Clip,top=ClipTop.height+CropBox.height)
	
	Bord=int(10*Ss)
	Crop=core.std.Crop(clip=CropBox,left=Bord,right=Bord,top=Bord,bottom=Bord)
	Rect=core.std.AddBorders(clip=Crop,left=Bord,right=Bord,top=Bord,bottom=Bord,color=[255,128,128])
	Clip=core.std.StackVertical([ClipTop,Rect,ClipBottom])
	Clip=core.std.StackHorizontal([ClipLeft,Clip,ClipRight])
	
	if Step==0:
		ClipGray=core.text.Text(ClipGray, f"Indexation OK", 5)
		ClipGray.set_output()
	else:
		Clip=core.text.Text(Clip, f"CropBoxDimension: {CropBoxDimension}\nCropBoxElevation: {CropBoxElevation}", 5)
		Clip.set_output()

elif Step==2:

	Clip = ClipTextBox

	Clip = SuperSampleClip( Clip, Ss, ModeU, Ssbis )

	if isinstance(SelectColor, int):
		planes = ExtractColorPlanes( Clip, FontColors, debug=True )
		planes[SelectColor].set_output()
	else:
		YUV2RGB( Clip ).set_output()

elif Step==3:
	
	rangedSubtitleDetection = isinstance(SubtitleDetectionInterval, list) and isinstance(SubtitleDetectionInterval[0],int) and isinstance(SubtitleDetectionInterval[1],int)
		
	# Creating stat files
	stat_scenechanges_log   = Path("stat_scenechanges.log")
	stat_nonblackframes_log = Path("stat_nonblackframes.log")

	if stat_scenechanges_log.is_file() and not Stat_debug:
		stat_scenechanges_log.unlink()
	if stat_nonblackframes_log.is_file() and not Stat_debug:
		stat_nonblackframes_log.unlink()

	blackFrames = list()
	sceneChanges = list()
	# if InverseL:
	# 	Clip = core.std.Invert(Clip, planes=0)

		
	def output_stats( out_file, stats ):
		# Write stats to file
		# Bugfix : had to sort `stats` because race conditions may have put values in wrong order
		if Stat_debug:
			return
		with out_file.open('a+', encoding='utf8') as f:
			f.write('\n'.join( [ str(s) for s in sorted(stats) ] ) )
		
	def SceneLog(n,f,clip,log):
		# Logs 'Scene change' events
		if f.props._SceneChangePrev == 1:
			# scene change
			exclude_this_frame = rangedSubtitleDetection and ( n <= SubtitleDetectionInterval[0] or SubtitleDetectionInterval[1] <= n )
			if not exclude_this_frame:
				sceneChanges.append(n)
			if Stat_debug:
				return core.text.Text(clip, f"SceneChange@{n}", alignment=7)
				
		if n==clip.num_frames-1:
			# Last frame of the video -> write stats to file
			output_stats( log, sceneChanges )
					
		return clip
		
	def BlackLog(n,f,clip,log):
		# Logs 'Black frame' events
		if f.props.PlaneStatsAverage > MinTextThr:
			# Black frame
			exclude_this_frame = rangedSubtitleDetection and ( n <= SubtitleDetectionInterval[0] or SubtitleDetectionInterval[1] <= n )
			if not exclude_this_frame:
				blackFrames.append(n)
			if Stat_debug:
				return core.text.Text(clip, f"BlackFrame@{n}", alignment=4)
				
		if n==clip.num_frames-1:
			# Last frame of the video -> write stats to file
			output_stats( log, blackFrames )
			
		if Stat_debug:
			return core.text.Text(clip, f"PlaneStatsAverage={f.props.PlaneStatsAverage}", alignment=4)
			
		return clip
		

	Clip = ClipTextBox

	Clip = SuperSampleClip( Clip, Ss, ModeU, Ssbis )

	planes = ExtractColorPlanes( Clip, FontColors )
	
	ClipCleaned = MergeClips( planes )
	

	# Scenedetect/BlackFrameDetect
	ClipCleanedSC=core.misc.SCDetect(clip=ClipCleaned,threshold=SeuilSCD)
	ClipCleanedStats=core.std.PlaneStats(clipa=ClipCleaned)
	ClipCleaned=core.std.FrameEval(ClipCleaned,functools.partial(SceneLog,clip=ClipCleaned,log=stat_scenechanges_log),prop_src=ClipCleanedSC)
	ClipCleaned=core.std.FrameEval(ClipCleaned,functools.partial(BlackLog,clip=ClipCleaned,log=stat_nonblackframes_log),prop_src=ClipCleanedStats)
	
	# Tesseract prefers black text on white background, so in this step the current white text on black background is inverted
	ClipCleanedInv = core.std.Invert(ClipCleaned, planes=0)
	ClipCleanedInv.set_output()

else:
	raise ValueError(f"Step '{Step}' is an invalid option !")
	
