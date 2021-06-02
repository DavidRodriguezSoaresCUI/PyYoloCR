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

VideoSrc=r'!!!VIDEO_FILE_HERE!!!'

# Main adjustment variables : finding good values is essential
Step=3 # 0:VapourSynth crash workaround, 1:Resize, 2:Seuil, 3:CR
# Step 1 : adjusting bounding box for subtitles
CropBoxDimension=[0.8,0.2]  # in [0,1]; Width, Height of box for subtitles
CropBoxElevation=0.00         # in [0,1-CropBoxDimension[1]]; How "high" (far from the bottom) should the text box be
# Step 2 : adjusting threshold for text extraction (L monochrome or RGB color mode)
ModeS='L'   # 'L' for Luma, 'R' pour Red, 'B' for Blue or 'G' for Green.
SeuilI=200  # typically in [170,230]; Minimum luminance threshold for subtitle insides. Optimization : Maximize while keeping all characters readable. Characters deformed/too "skinny" suggest value is too high.
SeuilO=80   # typically in [20,120]; Maximum luminance threshold for subtitle outline. Optimization : Minimize while keeping all characters visible. Characters popping in and out of visibility or accent/punctuation invisible means value is too low
# Step 3 : See output to check previously set values are good (subtitles are readable and there are not too many artifacts)

# Other variables
Seuil    = -1     # In Step==2, sets the threshold for binarization to choose SeuilI/SeuilO values. Leave on -1 to search for threshold values using VapourSynth Editor's preview panel.
SeuilSCD = 0.1    # Scene change threshold. Too low a value result in false positive scene changes, too high causes some subtitles to not be identified/discriminated.
ModeU    = 'sinc' # Upscaling method : 'sinc' (2 taps, faster), 'znedi3' (slower) ou 'waifu2x' (way slower)
InverseL = False  # In Steps 2 and 3 with ModeS='L', inverts luminance. Useful for black text with white outline
SubtitleDetectionInterval=None # Set to [a,b] for subtitle detection to only be active between frame a and frame b; Useful to avoid picking up on Intro/outro.
Stat_debug = False # Used on Step==3; For developper, allows to check subtitle alignment stats and disables stat file writes


try:
	import havsfunc as haf
	import functools
	import os
	from pathlib import Path
	import vapoursynth as vs
	if ModeU=='znedi3':
		import edi_rpow2 as edi
except ImportException as e:
	raise ImportException(f"Error while trying to import required plugins and libraries : {e}\nYou may have not installed them properly.")


video_source = Path(VideoSrc)
assert video_source.is_file()
core=vs.get_core()
try:
	Clip=core.ffms2.Source(source=VideoSrc)
except AttributeError as e:
	raise AttributeError(f"The following error was raised : '{e}'\nYou may have forgotten/failed to install PyYoloCR required VapourSynth plugins !")
	

def makeMOD2( x: int ) -> int:
	# ensures x is even (mod 2)
	if not isinstance( x, int ):
		x = int(x)
	return x+1 if x%2==1 else x

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




if Step in [0,1]:

	Ss, Ssbis = SSdecision( Clip, Supersampling=1 )

	def Grayuv(x):
		return 128

	CropBox=core.std.CropAbs(clip=Clip,width=CropBoxDimension[0],height=CropBoxDimension[1],left=LeftCropBox,top=Clip.height-CropBoxElevation-CropBoxDimension[1])
	ClipGray=core.std.Lut(clip=Clip,planes=[1,2],function=Grayuv)

	def SuperSampling(clip):
		if Ss!=1:
			if ModeU=='znedi3' or ModeU=='waifu2x':
				if ModeU=='znedi3':
					clip=edi.znedi3_rpow2(clip=clip,rfactor=Ss)
				else :
					clip=core.fmtc.bitdepth(clip=clip,bits=32)
					clip=core.w2xc.Waifu2x(clip=clip,scale=Ss)
				if Ssbis!=1:
					clip=core.fmtc.resample(clip=clip,scale=Ssbis,kernel="sinc",taps=2)
			else:
				clip=core.fmtc.resample(clip=clip,scale=Ss,kernel="sinc",taps=2)
		clip=core.fmtc.resample(clip=clip,css="444")
		clip=core.fmtc.bitdepth(clip=clip,bits=8)
		return clip

	CropBox=SuperSampling(clip=CropBox)
	ClipGray=SuperSampling(clip=ClipGray)
	
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

	Ss, Ssbis = SSdecision( Clip )  

	Clip=core.std.CropAbs(clip=Clip,width=CropBoxDimension[0],height=CropBoxDimension[1],left=LeftCropBox,top=Clip.height-CropBoxElevation-CropBoxDimension[1])

	if ModeS=='L':
		Clip=core.std.ShufflePlanes(clips=Clip,planes=0,colorfamily=vs.GRAY)
		if InverseL:
			Clip = core.std.Invert(Clip, planes=0)

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
				Clip=core.fmtc.bitdepth(clip=Clip,bits=8)
		else:
			Clip=core.fmtc.resample(clip=Clip,scale=Ss,kernel="sinc",taps=2)
			Clip=core.fmtc.bitdepth(clip=Clip,bits=8)
	elif Clip.format.bits_per_sample!=8:
		Clip=core.fmtc.bitdepth(clip=Clip,bits=8)

	if ModeS=='R' or ModeS=='G' or ModeS=='B':
		Clip=core.fmtc.resample(clip=Clip,css="444")
		Clip=core.fmtc.matrix(clip=Clip,mat="709",col_fam=vs.RGB)
		Clip=core.fmtc.bitdepth(clip=Clip,bits=8)
		if ModeS=='R':
			Clip=core.std.ShufflePlanes(clips=Clip,planes=0,colorfamily=vs.GRAY)
		elif ModeS=='G':
			Clip=core.std.ShufflePlanes(clips=Clip,planes=1,colorfamily=vs.GRAY)
		else:
			Clip=core.std.ShufflePlanes(clips=Clip,planes=2,colorfamily=vs.GRAY)
		def remove_matrix(n,f):
			fout = f.copy()
			del fout.props._Matrix
			return fout
		Clip=core.std.ModifyFrame(clip=Clip,clips=Clip,selector=remove_matrix)

	if Seuil>=0:	
		Clip=core.std.Binarize(clip=Clip,threshold=Seuil)	
	Crop=core.std.CropAbs(clip=Clip,width=Clip.width-20,height=Clip.height-20,left=10,top=10)
	Rect=core.std.AddBorders(clip=Crop,left=10,right=10,top=10,bottom=10,color=255)
	Rect.set_output()

elif Step==3:

	Ss, Ssbis = SSdecision( Clip )

	ExpandRatio=1 # EXPERIMENTAL ! Facteur Expand/Inpand. La valeur 1 est adaptée pour un Supersampling automatique (1080p). Calcul typique de la valeur : ExpandRatio="RésolutionFinale"/1080.
	
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

	def minimum(x,y):
		return min(x,y)

	if type(SeuilI) is int and type(SeuilO) is int:
		Clip=core.std.ShufflePlanes(clips=Clip,planes=0,colorfamily=vs.GRAY)
		if InverseL:
			Clip = core.std.Invert(Clip, planes=0)

	def Resizing(clip,largeur,hauteur,hauteur2):
		clip=core.std.CropAbs(clip=clip,width=largeur,height=hauteur,left=LeftCropBox,top=clip.height-hauteur2)
		if Ss!=1:
			if ModeU=='znedi3' or ModeU=='waifu2x':
				if ModeU=='znedi3':
					clip=edi.znedi3_rpow2(clip=clip,rfactor=Ss)
				else :
					clip=core.fmtc.bitdepth(clip=clip,bits=32)
					clip=core.w2xc.Waifu2x(clip=clip,scale=Ss)
					if Ssbis!=1:
						clip=core.fmtc.bitdepth(clip=clip,bits=16)
					else :
						clip=core.fmtc.bitdepth(clip=clip,bits=8)
				if Ssbis!=1:
					clip=core.fmtc.resample(clip=clip,scale=Ssbis,kernel="sinc",taps=2)
					clip=core.fmtc.bitdepth(clip=clip,bits=8)
			else:
				clip=core.fmtc.resample(clip=clip,scale=Ss,kernel="sinc",taps=2)
				clip=core.fmtc.bitdepth(clip=clip,bits=8)
		elif clip.format.bits_per_sample!=8:
			clip=core.fmtc.bitdepth(clip=clip,bits=8)
		return clip
		
	def RGBBinarize(clip,seuil):
		R=core.std.ShufflePlanes(clips=clip,planes=0,colorfamily=vs.GRAY)
		G=core.std.ShufflePlanes(clips=clip,planes=1,colorfamily=vs.GRAY)
		B=core.std.ShufflePlanes(clips=clip,planes=2,colorfamily=vs.GRAY)
		for i in range(0,int(len(seuil)/3)):
			i=i*3
			RGB=core.std.Expr(clips=[R,G,B],expr=["x "+str(seuil[i])+" >= y "+str(seuil[i+1])+" >= or z "+str(seuil[i+2])+" >= or 255 0 ?"])
			if i==0:
				clipfin=RGB
			else:
				clipfin=core.std.Merge(clipfin,RGB)
		clipfin=core.std.Binarize(clip=clipfin,threshold=1)
		return clipfin
		

	def Cleaning(clip,e):
		if type(SeuilI) is list or type(SeuilO) is list:
			clipRGB=core.fmtc.resample(clip=clip,css="444")
			clipRGB=core.fmtc.matrix(clip=clipRGB,mat="709",col_fam=vs.RGB)
			clipRGB=core.fmtc.bitdepth(clip=clipRGB,bits=8)
			
		if type(SeuilI) is int and type(SeuilO) is int:
			White_Raw=core.std.Binarize(clip=clip,threshold=SeuilI)
			Bright_Raw=core.std.Binarize(clip=clip,threshold=SeuilO)
		elif type(SeuilI) is int and type(SeuilO) is list:
			White_Raw=core.std.ShufflePlanes(clips=clip,planes=0,colorfamily=vs.GRAY)
			White_Raw=core.std.Binarize(clip=White_Raw,threshold=SeuilI)
			Bright_Raw=RGBBinarize(clipRGB,SeuilO)
		elif type(SeuilI) is list and type(SeuilO) is int:
			White_Raw=RGBBinarize(clipRGB,SeuilI)
			Bright_Raw=core.std.ShufflePlanes(clips=clip,planes=0,colorfamily=vs.GRAY)
			Bright_Raw=core.std.Binarize(clip=Bright_Raw,threshold=SeuilO)
		else:
			White_Raw=RGBBinarize(clipRGB,SeuilI)
			Bright_Raw=RGBBinarize(clipRGB,SeuilO)

		Bright_Out=core.std.Lut2(clipa=Bright_Raw,clipb=Rect,function=minimum)

		Bright_Not=core.misc.Hysteresis(clipa=Bright_Out,clipb=Bright_Raw)
		Bright_Not=core.std.Invert(Bright_Not)

		White_Txt=core.std.MaskedMerge(Blank,White_Raw,Bright_Not)

		White_Lb=haf.mt_inpand_multi(src=White_Txt,sw=int(e),sh=int(e),mode="ellipse")
		White_Lb=haf.mt_expand_multi(src=White_Lb,sw=int(e),sh=int(e),mode="ellipse")

		White_Ub=haf.mt_inpand_multi(src=White_Txt,sw=int(5*e),sh=int(5*e),mode="ellipse")
		White_Ub=haf.mt_expand_multi(src=White_Ub,sw=int(3*e),sh=int(3*e),mode="ellipse")
		White_Ub=core.std.Invert(White_Ub)

		White=core.std.MaskedMerge(Blank,White_Lb,White_Ub)
		White=core.misc.Hysteresis(clipa=White,clipb=White_Txt)

		ClipCleaning=core.std.MaskedMerge(Blank,White_Raw,White)
		ClipCleaning=core.std.Median(clip=ClipCleaning)
		
		return ClipCleaning
		
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
		if f.props.PlaneStatsAverage > 0.05:
			# Black frame
			exclude_this_frame = rangedSubtitleDetection and ( n <= SubtitleDetectionInterval[0] or SubtitleDetectionInterval[1] <= n )
			if not exclude_this_frame:
				blackFrames.append(n)
			if Stat_debug:
				return core.text.Text(clip, f"BlackFrame@{n}", alignment=4)
				
		if n==clip.num_frames-1:
			# Last frame of the video -> write stats to file
			output_stats( log, blackFrames )
			
		return clip

	CropBoxElevation=CropBoxElevation+CropBoxDimension[1]

	ClipResized=Resizing(Clip,CropBoxDimension[0],CropBoxDimension[1],CropBoxElevation)

	Blackclip=core.std.BlankClip(width=int(ClipResized.width-20),height=int(ClipResized.height-20),format=vs.GRAY8,color=0)
	Rect=core.std.AddBorders(clip=Blackclip,left=10,right=10,top=10,bottom=10,color=255)
	Blank=core.std.BlankClip(ClipResized,format=vs.GRAY8)

	ClipCleaned=Cleaning(ClipResized,ExpandRatio)

	ClipCleanedSC=core.std.CropAbs(clip=ClipCleaned,width=int(ClipCleaned.width/2.7),height=int(ClipCleaned.height/2.7),left=int(ClipCleaned.width*(1-1/2.7)/2),top=int(ClipCleaned.height/2))
	ClipCleanedSC=core.misc.SCDetect(clip=ClipCleanedSC,threshold=SeuilSCD)
	ClipCleanedStats=core.std.PlaneStats(clipa=ClipCleanedSC)
	ClipCleaned=core.std.FrameEval(ClipCleaned,functools.partial(SceneLog,clip=ClipCleaned,log=stat_scenechanges_log),prop_src=ClipCleanedSC)
	ClipCleaned=core.std.FrameEval(ClipCleaned,functools.partial(BlackLog,clip=ClipCleaned,log=stat_nonblackframes_log),prop_src=ClipCleanedStats)
	
	# Tesseract prefers black text on white background, so in this step the current white text on black background is inverted
	ClipCleanedInv = core.std.Invert(ClipCleaned, planes=0)
	ClipCleanedInv.set_output()

else:
	raise ValueError(f"Step '{Step}' is an invalid option !")
	
