:: Carry out automatic alignment for Bora files
::
:: Jan Strunk
:: August 2013
::
:: USAGE: align_bora.bat WAVNAME NAME

@ECHO OFF

SET BASEPATH=.
SET REFTIER=ref
SET TEXTTIER=t

:: Output command-line arguments
ECHO Base path: %BASEPATH%
ECHO Name of wave file: %1
ECHO Base file name: %2
ECHO Reference tier: %REFTIER%
ECHO Text tier: %TEXTTIER%

:: Create BASPartitur files for automatic alignment
ECHO Creating BASPartitur file
python %BASEPATH%\Toolbox2BASPartitur.py -t %TEXTTIER% -r %REFTIER% -wave %BASEPATH%\input\Media\Bora\%1.wav -starttimemarker ELANBegin -endtimemarker ELANEnd %BASEPATH%\input\Toolbox\Bora\%2.txt %BASEPATH%\output\PAR\Bora\%2.par %BASEPATH%\transliterationtables\Bora\bora.sampa.tab
ECHO done

:: Wait for user to perform automatic alignment
ECHO Please perform automatic alignment using WebMAUS
ECHO Wave file: %1.wav
ECHO Base file name: %2
ECHO Copy resulting mau file to %BASEPATH%\output\MAU\Bora\
ECHO Please press any key to continue...
PAUSE

:: Convert the result of the automatic alignment into Toolbox files
ECHO Converting mau file into Toolbox file
python %BASEPATH%\MAU2Toolbox.py -wave %BASEPATH%\input\Media\Bora\%1.wav -toolboxfile %BASEPATH%\input\Toolbox\Bora\%2.txt -keeputterancetimes -outputwordtimes -reftier %REFTIER% %BASEPATH%\output\MAU\Bora\%2.mau %BASEPATH%\output\PAR\Bora\%2.par %BASEPATH%\output\Toolbox\Bora\%2.txt
ECHO done

:: Wait for user to import Toolbox file into ELAN
ECHO Please import the Toolbox file into ELAN
ECHO and save the resulting file in %BASEPATH%\output\ELAN\Bora\
ECHO File name: %2.nowordtimes.eaf
ECHO Please press any key to continue...
PAUSE

:: Flexibilize ELAN file
ECHO Flexibilizing ELAN file
python %BASEPATH%\flexibilize_imported_toolbox_in_elan.py %BASEPATH%\output\ELAN\Bora\%2.nowordtimes.eaf %BASEPATH%\output\ELAN\Bora\%2.flexibilized.eaf
ECHO done

:: Set word start and begin times in the flexibilized ELAN files by extracting the WordBegin and WordEnd tiers from the corresponding Toolbox files
ECHO Setting word times in ELAN file
python %BASEPATH%\import_wordtimes_from_toolbox_to_elan.py -reftier %REFTIER% -texttier %TEXTTIER% %BASEPATH%\output\ELAN\Bora\%2.flexibilized.eaf %BASEPATH%\output\Toolbox\Bora\%2.txt %BASEPATH%\output\ELAN\Bora\%2.wordtimes.eaf
ECHO done
ECHO Please check the resulting ELAN file: %2.wordtimes.eaf
