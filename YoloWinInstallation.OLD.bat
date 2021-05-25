
@REM Script to install requirements for Windows 10
@echo off


call :check_Permissions
call :get_vapoursynth_scripts

echo End of Program
exit /b


:check_Permissions
    echo Administrative permissions required. Detecting permissions...
	Set scriptname="%~n0%~x0"
    net session >nul 2>&1
    if %errorLevel% == 0 (
        echo Running %scriptname% with Administrative permissions
    ) else (
        echo Failure: Current permissions inadequate. Please run %scriptname% with Administrative permissions.
    )
	echo:
    timeout /t 2 1>nul
EXIT /B

:get_vapoursynth_scripts
	MKDIR VapoursynthPythonScripts
	curl https://raw.githubusercontent.com/HomeOfVapourSynthEvolution/havsfunc/master/havsfunc.py -o ./VapoursynthPythonScripts/havsfunc.py
	curl https://raw.githubusercontent.com/HomeOfVapourSynthEvolution/mvsfunc/master/mvsfunc.py -o ./VapoursynthPythonScripts/mvsfunc.py
	curl https://raw.githubusercontent.com/dubhater/vapoursynth-adjust/master/adjust.py -o ./VapoursynthPythonScripts/adjust.py
EXIT /B



@REM # Vapoursynth Editor install
@REM if [ ! -z $DISPLAY ]; then
@REM 	git clone https://bitbucket.org/mystery_keeper/vapoursynth-editor.git; cd vapoursynth-editor/pro
@REM 	qmake -qt5 && make -j$(nproc); cd ..
@REM 	sudo cp build/release-64bit-gcc/vsedit /usr/local/bin/vsedit 
@REM 	sudo install -D build/release-64bit-gcc/vsedit.svg /usr/local/share/pixmaps/vsedit.svg
@REM 	if [ ! -d /usr/local/share/applications ]; then sudo mkdir /usr/local/share/applications; fi
@REM 	sudo wget https://gist.githubusercontent.com/YamashitaRen/4489ab810ee92f2fbbf7/raw/2ac6f4da0599d0b5e1166dd7458a689f8a5a2206/vsedit.desktop -P /usr/local/share/applications
@REM 	cp /usr/local/share/applications/vsedit.desktop /home/$USER/$Desktop/vsedit.desktop
@REM 	cd ..
@REM fi

@REM # Création du lien symbolique FFMS2 dans le dossier plugins de Vapoursynth
@REM sudo ln -s $(dpkg-query -L libffms2-4 | grep libffms2.so | tail -1) /usr/local/lib/vapoursynth/libffms2.so

@REM # Installation de HAvsFunc, mvsfunc et adjust
@REM git clone https://github.com/HomeOfVapourSynthEvolution/havsfunc.git
@REM git clone https://github.com/HomeOfVapourSynthEvolution/mvsfunc.git
@REM git clone https://github.com/dubhater/vapoursynth-adjust.git
@REM sudo cp havsfunc/havsfunc.py mvsfunc/mvsfunc.py vapoursynth-adjust/adjust.py /usr/local/lib/python3.8/site-packages/

@REM # Installation de fmtconv
@REM git clone https://github.com/EleonoreMizo/fmtconv.git; cd fmtconv; cd build/unix
@REM ./autogen.sh && ./configure --libdir=/usr/local/lib/vapoursynth && make -j$(nproc)
@REM sudo make install; cd ../../..

@REM # Installation de znedi3
@REM git clone --recursive https://github.com/sekrit-twc/znedi3.git; cd znedi3
@REM make -j$(nproc) X86=1
@REM sudo cp vsznedi3.so /usr/local/lib/vapoursynth/; cd ..

@REM # Installation de edi_rpow2
@REM git clone https://gist.github.com/020c497524e794779d9c.git vapoursynth-edi_rpow2
@REM sudo cp vapoursynth-edi_rpow2/edi_rpow2.py /usr/local/lib/python3.8/site-packages/edi_rpow2.py

@REM # Vapoursynth doit fonctionner
@REM if [[ $1 != eng-only ]]
@REM 	then echo -e '\n# Nécessaire pour Vapoursynth\nexport PYTHONPATH=/usr/local/lib/python3.8/site-packages' >> ~/.bashrc
@REM 	else echo -e '\n# Required for Vapoursynth\nexport PYTHONPATH=/usr/local/lib/python3.8/site-packages' >> ~/.bashrc
@REM fi

@REM # Éviter un reboot
@REM sudo ldconfig
@REM if [[ $1 != eng-only ]]
@REM 	then echo "Script d'installation terminé."
@REM 	else echo "Installation script finished."
@REM fi
@REM if [ ! -z $DISPLAY ]; then if [[ $1 != eng-only ]]
@REM 	then echo -e "Un raccourci pour Vapoursynth Editor a été créé sur le Bureau.\nNotez que les commandes "vsedit" et "vspipe" ne fonctionneront pas depuis le terminal actuel."
@REM 	else echo -e "A shortcut for Vapoursynth Editor had been created on the Desktop.\nNote that "vsedit" and "vspipe" commands will not work from current terminal."
@REM fi; fi
