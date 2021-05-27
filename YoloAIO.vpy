VideoSrc=r'!!!VIDEO_FILE_HERE!!!'

# Main adjustment variables : finding good values is essential
Step=3 # 1:Resize, 2:Seuil, 3:CR
# Step 1 : adjusting bounding box for subtitles
DimensionCropBox=[0.9,0.2] # in [0,1]; Width, Height of box for subtitles
HauteurCropBox=0.0 # in [0,1-DimensionCropBox[1]]; How "high" (far from the bottom) should the text box be
# Step 2 : adjusting threshold for text extraction (L monochrome or RGB color mode)
ModeS='L' # 'L' for Luma, 'R' pour Red, 'B' pour Blue ou 'G' pour Green. Seuil à analyser.
SeuilI=170 # typically in [170,230]; Seuil délimitant les sous-titres. Cette valeur correspond à la luminosité minimale de l'intérieur (Inline).
SeuilO=50 # typically in [20,120]; Seuil délimitant les sous-titres. Cette valeur correspond à la luminosité maximale de l'extérieur (Outline).
# Step 3 : See output to check previously set values are good (subtitles are readable and there are not too many artifacts)

# Other variables
SeuilSCD=0.1 # Un seuil trop bas augmente le nombre de faux positifs, un seuil trop haut ne permet pas de détecter tous les sous-titres.
ModeU='sinc' # 'sinc' (2 taps, plus rapide), 'znedi3' (plus lent) ou 'waifu2x' (beaucoup plus lent), contrôle la méthode d'Upscale.


import vapoursynth as vs
if ModeU=='znedi3':
	import edi_rpow2 as edi
core=vs.get_core()
Clip=core.ffms2.Source(source=VideoSrc)

def makeMOD2( x: int ) -> int:
    # ensures x is even (mod 2)
    if not isinstance( x, int ):
    	x = int(x)
    return x+1 if x%2==1 else x

###########################################################
# percentage -> int conversion
# added black borders for subs too close to the border
Clip = core.std.AddBorders( Clip, 8,8,8,8 )
DimensionCropBox[0] = makeMOD2( int(DimensionCropBox[0] * Clip.width) )
DimensionCropBox[1] = makeMOD2( int(DimensionCropBox[1] * Clip.height) )
HauteurCropBox = makeMOD2( HauteurCropBox * Clip.height )
# HauteurCropBox must be a mod2 strictly positive integer
if HauteurCropBox == 0:
    HauteurCropBox += 2
LeftCropBox = makeMOD2( int((Clip.width-DimensionCropBox[0])/2) )
###########################################################

if Step==1:
    Clip=core.text.Text(Clip, f"DimensionCropBox: {DimensionCropBox}\nHauteurCropBox: {HauteurCropBox}", 5)
    Supersampling=1 # Facteur de supersampling (multiplication de la résolution de la vidéo). Mettre à -1 pour calculer le facteur automatiquement.

    def Grayuv(x):
        return 128

    CropBox=core.std.CropAbs(clip=Clip,width=DimensionCropBox[0],height=DimensionCropBox[1],left=LeftCropBox,top=Clip.height-HauteurCropBox-DimensionCropBox[1])
    ClipGray=core.std.Lut(clip=Clip,planes=[1,2],function=Grayuv)

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

    if ModeU=='znedi3' and Ss!=1:
        if Ss-int(Ss)>0:
            Ss=int(Ss/2)*2+2
        else:
            Ss=int(Ss/2)*2
        if Supersampling<0:
            Ssbis=TargetRes/(CurrentRes*Ss)
        else:
            Ssbis=Supersampling/Ss

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
    ClipTop=core.std.Crop(clip=Clip,bottom=int(HauteurCropBox*Ss)+CropBox.height)
    ClipBottom=core.std.Crop(clip=Clip,top=ClipTop.height+CropBox.height)

    Bord=int(10*Ss)
    Crop=core.std.Crop(clip=CropBox,left=Bord,right=Bord,top=Bord,bottom=Bord)
    Rect=core.std.AddBorders(clip=Crop,left=Bord,right=Bord,top=Bord,bottom=Bord,color=[255,128,128])
    Clip=core.std.StackVertical([ClipTop,Rect,ClipBottom])
    Clip=core.std.StackHorizontal([ClipLeft,Clip,ClipRight])
    Clip.set_output()

elif Step==2:
    Supersampling=-1 # Facteur de supersampling (multiplication de la résolution de la vidéo). Mettre à -1 pour calculer le facteur automatiquement.
    Seuil=-1 # Seuil délimitant les sous-titres. Mettre à -1 pour chercher le seuil à l'aide de VapourSynth Editor.

    Clip=core.std.CropAbs(clip=Clip,width=DimensionCropBox[0],height=DimensionCropBox[1],left=LeftCropBox,top=Clip.height-HauteurCropBox-DimensionCropBox[1])

    if ModeS=='L':
        Clip=core.std.ShufflePlanes(clips=Clip,planes=0,colorfamily=vs.GRAY)

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

    if ModeU=='znedi3' and Ss!=1:
        if Ss-int(Ss)>0:
            Ss=int(Ss/2)*2+2
        else:
            Ss=int(Ss/2)*2
        if Supersampling<0:
            Ssbis=TargetRes/(CurrentRes*Ss)
        else:
            Ssbis=Supersampling/Ss

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
    Supersampling=-1 # Facteur de supersampling (multiplication de la résolution de la vidéo). Mettre à -1 pour calculer le facteur automatiquement.
    ExpandRatio=1 # EXPERIMENTAL ! Facteur Expand/Inpand. La valeur 1 est adaptée pour un Supersampling automatique (1080p). Calcul typique de la valeur : ExpandRatio="RésolutionFinale"/1080.
    HauteurCropBoxAlt=-1

    from pathlib import Path
    stat_scenechanges_log   = Path("stat_scenechanges.log")
    stat_nonblackframes_log = Path("stat_nonblackframes.log")

    if stat_scenechanges_log.is_file():
        stat_scenechanges_log.unlink()
    if stat_nonblackframes_log.is_file():
        stat_nonblackframes_log.unlink()

    import havsfunc as haf
    import functools
    import os

    def minimum(x,y):
	    return min(x,y)

    if type(SeuilI) is int and type(SeuilO) is int:
	    Clip=core.std.ShufflePlanes(clips=Clip,planes=0,colorfamily=vs.GRAY)
	
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

    if ModeU=='znedi3' and Ss!=1:
        if Ss-int(Ss)>0:
            Ss=int(Ss/2)*2+2
        else:
            Ss=int(Ss/2)*2
        if Supersampling<0:
            Ssbis=TargetRes/(CurrentRes*Ss)
        else:
            Ssbis=Supersampling/Ss

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
        
    def SceneLog(n,f,clip,log):
        if f.props._SceneChangePrev == 1:
            # scene change
            with stat_scenechanges_log.open("a") as f:
                f.write(f"{n}\n")
        return clip
        
    def BlackLog(n,f,clip,log):
        if f.props.PlaneStatsAverage > 0.05:
            # Black frame
            with stat_nonblackframes_log.open("a") as f:
                f.write(f"{n}\n")
        return clip

    HauteurCropBox=HauteurCropBox+DimensionCropBox[1]
    if HauteurCropBoxAlt>=0:
        HauteurCropBoxAlt=HauteurCropBoxAlt+DimensionCropBox[1]

    ClipResized=Resizing(Clip,DimensionCropBox[0],DimensionCropBox[1],HauteurCropBox)

    Blackclip=core.std.BlankClip(width=int(ClipResized.width-20),height=int(ClipResized.height-20),format=vs.GRAY8,color=0)
    Rect=core.std.AddBorders(clip=Blackclip,left=10,right=10,top=10,bottom=10,color=255)
    Blank=core.std.BlankClip(ClipResized,format=vs.GRAY8)

    ClipCleaned=Cleaning(ClipResized,ExpandRatio)

    ClipCleanedSC=core.std.CropAbs(clip=ClipCleaned,width=int(ClipCleaned.width/2.7),height=int(ClipCleaned.height/2.7),left=int(ClipCleaned.width*(1-1/2.7)/2),top=int(ClipCleaned.height/2))
    ClipCleanedSC=core.misc.SCDetect(clip=ClipCleanedSC,threshold=SeuilSCD)
    ClipCleanedStats=core.std.PlaneStats(clipa=ClipCleanedSC)
    ClipCleaned=core.std.FrameEval(ClipCleaned,functools.partial(SceneLog,clip=ClipCleaned,log="SceneChanges.log"),prop_src=ClipCleanedSC)
    ClipCleaned=core.std.FrameEval(ClipCleaned,functools.partial(BlackLog,clip=ClipCleaned,log="Blackframes.log"),prop_src=ClipCleanedStats)

    if HauteurCropBoxAlt>=0:
        ClipResizedAlt=Resizing(Clip,DimensionCropBox[0],DimensionCropBox[1],HauteurCropBoxAlt)
        
        ClipCleanedAlt=Cleaning(ClipResizedAlt,ExpandRatio)
        
        open("SceneChangesAlt.log", "w").write("0 1 0\n")
        ClipCleanedAltSC=core.std.CropAbs(clip=ClipCleanedAlt,width=int(ClipCleanedAlt.width/2.7),height=int(ClipCleanedAlt.height/2.7),left=int(ClipCleanedAlt.width*(1-1/2.7)/2),top=int(ClipCleanedAlt.height*(1/2-1/2.7)))
        ClipCleanedAltSC=core.misc.SCDetect(clip=ClipCleanedAltSC,threshold=SeuilSCD)
        ClipCleanedAlt=core.std.FrameEval(ClipCleanedAlt,functools.partial(SceneLog,clip=ClipCleanedAlt,log="SceneChangesAlt.log"),prop_src=ClipCleanedAltSC)
        
        Clip=core.std.StackVertical([ClipCleanedAlt,ClipCleaned])

    else:
        if os.path.exists("SceneChangesAlt.log"):
            os.remove("SceneChangesAlt.log")
        Clip=ClipCleaned

    Clip.set_output()

else:
    raise ValueError(f"Step '{Step}' is an invalid option !")
    