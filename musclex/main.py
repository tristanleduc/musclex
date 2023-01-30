#!/usr/bin/python

"""
Copyright 1999 Illinois Institute of Technology

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL ILLINOIS INSTITUTE OF TECHNOLOGY BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Except as contained in this notice, the name of Illinois Institute
of Technology shall not be used in advertising or otherwise to promote
the sale, use or other dealings in this Software without prior written
authorization from Illinois Institute of Technology.
"""

import os
import sys
import unittest
from musclex import __version__
from musclex.ui.pyqt_utils import *
from musclex.utils.exception_handler import handlers
from musclex.tests.module_test import MuscleXTest
from musclex.tests.musclex_tester import MuscleXGlobalTester
from musclex.tests.environment_tester import EnvironmentTester

if sys.platform in handlers:
    sys.excepthook = handlers[sys.platform]

def main(arguments=None):
    if arguments is None:
        arguments = sys.argv

    run = True
    if len(arguments) == 2:
        prog = arguments[1]
        if prog == 'eq':
            app = QApplication(sys.argv)
            from musclex.ui.EQStartWindow import EQStartWindow
            myapp = EQStartWindow() # Even if 'myapp' isn't used after, it is necessary for the windows to show on the screen
            sys.exit(app.exec_())
        elif prog == 'qf':
            app = QApplication(sys.argv)
            from musclex.ui.QuadrantFoldingGUI import QuadrantFoldingGUI
            myapp = QuadrantFoldingGUI()
            sys.exit(app.exec_())
        elif prog == 'di':
            app = QApplication(sys.argv)
            from musclex.ui.ScanningDiffractionGUI import \
                ScanningDiffractionGUI
            myapp = ScanningDiffractionGUI()
            sys.exit(app.exec_())
        elif prog == 'dc':
            from musclex.ui.diffraction_centroids import \
                DiffractionCentroidStartWindow
            app = QApplication(sys.argv)
            myapp = DiffractionCentroidStartWindow()
            sys.exit(app.exec_())
        elif prog == 'ddf':
            from musclex.ui.ddf_processor import DDFWindow
            app = QApplication(sys.argv)
            myapp = DDFWindow()
            sys.exit(app.exec_())
        elif prog == 'pt':
            from musclex.ui.ProjectionTracesGUI import ProjectionTracesGUI
            app = QApplication(sys.argv)
            myapp = ProjectionTracesGUI()
            sys.exit(app.exec_())
        elif prog == 'aise':
            from musclex.ui.AddIntensitiesSingleExp import AddIntensitiesSingleExp
            app = QApplication(sys.argv)
            myapp = AddIntensitiesSingleExp()
            sys.exit(app.exec_())
        elif prog == 'aime':
            from musclex.ui.AddIntensitiesMultExp import AddIntensitiesMultExp
            app = QApplication(sys.argv)
            myapp = AddIntensitiesMultExp()
            sys.exit(app.exec_())
        elif prog == 'xv':
            from musclex.ui.XRayViewerGUI import XRayViewerGUI
            app = QApplication(sys.argv)
            myapp = XRayViewerGUI()
            sys.exit(app.exec_())
        elif prog == 'gui':
            from musclex.launcher import LauncherForm
            app = QApplication(sys.argv)
            myapp = LauncherForm.main()
            sys.exit(app.exec_())
        elif prog == 'test_global':
            suite = unittest.TestSuite()
            suite.addTest(MuscleXGlobalTester("testHeadlessMarEquator"))
            suite.addTest(MuscleXGlobalTester("testHeadlessEigerEquator"))
            suite.addTest(MuscleXGlobalTester("testHeadlessPilatusEquator"))
            suite.addTest(MuscleXGlobalTester("testHeadlessMarQuadrantFolder"))
            suite.addTest(MuscleXGlobalTester("testHeadlessEigerQuadrantFolder"))
            suite.addTest(MuscleXGlobalTester("testHeadlessPilatusQuadrantFolder"))
            suite.addTest(MuscleXGlobalTester("testHeadlessMarDiffraction"))
            suite.addTest(MuscleXGlobalTester("testHeadlessEigerDiffraction"))
            suite.addTest(MuscleXGlobalTester("testHeadlessPilatusDiffraction"))
            runner = unittest.TextTestRunner()
            runner.run(suite)
            sys.exit()
        elif prog == 'test_impl':
            from musclex.utils.zip_download import download_zip_pickles
            download_zip_pickles(os.path.dirname(__file__))
            suite = unittest.TestSuite()
            suite.addTest(MuscleXTest("testEquatorImage"))
            suite.addTest(MuscleXTest("testQuadrantFolder"))
            suite.addTest(MuscleXTest("testDiffractionCentroids"))
            suite.addTest(MuscleXTest("testProjectionTraces"))
            suite.addTest(MuscleXTest("testScanningDiffraction"))
            suite.addTest(MuscleXTest("testHDFRead"))
            suite.addTest(MuscleXTest("testOpenCLDevice"))
            suite.addTest(MuscleXTest("testGPUIntegratePyFAI"))
            runner = unittest.TextTestRunner()
            runner.run(suite)
            sys.exit()
        elif prog == 'test_env':
            suite = unittest.TestSuite()
            suite.addTest(EnvironmentTester("testEnvironment"))
            runner = unittest.TextTestRunner()
            runner.run(suite)
            sys.exit()
        elif prog == 'test_gpu':
            suite = unittest.TestSuite()
            suite.addTest(MuscleXTest("testOpenCLDevice"))
            suite.addTest(MuscleXTest("testGPUIntegratePyFAI"))
            runner = unittest.TextTestRunner()
            runner.run(suite)
            sys.exit()
        else:
            run = False

    elif len(arguments) >= 5 and arguments[1]=='eq' and arguments[2]=='-h':
        inputsetting=False
        delcache=False
        run=True
        i=3
        settingspath="empty"
        while i < len(arguments):
            if arguments[i]=='-s':
                inputsetting=True
                if i+1<len(arguments) and len(arguments[i+1])>5:
                    _, ext = os.path.splitext(str(arguments[i+1]))
                    if ext==".json" and os.path.isfile(arguments[i+1]):
                        i=i+1
                        settingspath=arguments[i]
                    else:
                        print("Please provide the right settings file")
                        run=False
            elif arguments[i]=='-d':
                delcache=True
            elif arguments[i]=='-i' or arguments[i]=='-f':
                i=i+1
                filename=arguments[i]
            else:
                run=False
                break
            i=i+1
        if run:
            from musclex.ui.EQStartWindowh import EQStartWindowh
            EQStartWindowh(filename, inputsetting, delcache, settingspath)
            sys.exit()

    elif len(arguments)>=5 and arguments[1]=='di' and arguments[2]=='-h':
        inputsetting=False
        delcache=False
        run=True
        i=3
        settingspath='empty'
        processFolder=False
        while i < len(arguments):
            if arguments[i]=='-s':
                inputsetting=True
                if i+1<len(arguments) and len(arguments[i+1])>5:
                    _, ext = os.path.splitext(str(arguments[i+1]))
                    if ext==".json" and os.path.isfile(arguments[i+1]):
                        i=i+1
                        settingspath=arguments[i]
                    else:
                        print("Please provide the right settings file")
                        run=False
            elif arguments[i]=='-d':
                delcache=True
            elif arguments[i]=='-i' or arguments[i]=='-f':
                if arguments[i]=='-f':
                    processFolder=True
                i=i+1
                fullfilename=arguments[i]
                if not processFolder:
                    filePath, fileName = os.path.split(fullfilename)
                else:
                    filePath=fullfilename
            else:
                run=False
                break
            i=i+1
        if run:
            if not processFolder:
                from musclex.ui.DIImageWindowh import DIImageWindowh
                DIImageWindowh(str(fileName), str(filePath), inputsetting, delcache, settingspath)
                sys.exit()
            else:
                from musclex.ui.DIBatchWindowh import DIBatchWindowh
                DIBatchWindowh(str(filePath), inputsetting, delcache, settingspath)
                sys.exit()

    elif len(arguments) >= 5 and arguments[1]=='qf' and arguments[2]=='-h':
        inputsetting=False
        delcache=False
        run=True
        i=3
        settingspath="empty"
        while i < len(arguments):
            if arguments[i]=='-s':
                inputsetting=True
                if i+1<len(arguments) and len(arguments[i+1])>5:
                    _, ext = os.path.splitext(str(arguments[i+1]))
                    if ext==".json" and os.path.isfile(arguments[i+1]):
                        i=i+1
                        settingspath=arguments[i]
                    else:
                        print("Please provide the right settings file")
                        run=False
            elif arguments[i]=='-d':
                delcache=True
            elif arguments[i]=='-i' or arguments[i]=='-f':
                is_file = arguments[i]=='-i'
                i=i+1
                filename=arguments[i]
            else:
                run=False
                break
            i=i+1
        if run:
            from musclex.ui.QuadrantFoldingh import QuadrantFoldingh
            if is_file:
                QuadrantFoldingh(filename, inputsetting, delcache, settingspath)
            else:
                from multiprocessing import Lock, Process, cpu_count
                lock = Lock()
                procs = []
                in_types = ['.adsc', '.cbf', '.edf', '.fit2d', '.mar345', '.marccd', '.pilatus', '.tif', '.h5', '.hdf5', '.smv']
                imgList = os.listdir(filename)
                imgList.sort()
                for image in imgList:
                    file_name=os.path.join(filename,image)
                    if os.path.isfile(file_name):
                        _, ext = os.path.splitext(str(file_name))
                        if ext in in_types:
                            print("filename is", file_name)
                            # QuadrantFoldingh(file_name, inputsetting, delcache, settingspath)
                            proc = Process(target=QuadrantFoldingh, args=(file_name, inputsetting, delcache, settingspath, lock,))
                            procs.append(proc)
                            proc.start()
                    if len(procs) % cpu_count() == 0:
                        for proc in procs:
                            proc.join()
                        procs = []
                for proc in procs:
                    proc.join()
                    sys.exit()

    else:
        run = False

    if not run:
        print("\nYou're using Muscle X version "+str(__version__))
        print("\nPlease specify the program shortcut that you want to run")
        print("")
        print("  $ musclex [program]")
        print("")
        print("          xv - X-Ray Viewer")
        print("          eq [<-h>] - Equator (-h for headless version)")
        print("          di [<-h>] - Scanning Diffraction (-h for headless version)")
        print("          qf [<-h>] - Quadrant Folding (-h for headless version)")
        print("          pt - Projection Traces")
        print("          ddf - DDF Processor")
        print("          aise - Add Intensities Single Experiment")
        print("          aime - Add Intensities Multiple Experiments")
        print("          dc - Diffraction Centroids (DEPRECATED)")
        print("")
        print("          gui - GUI Launcher")
        print("          test_global - Run Global Tests")
        print("          test_impl - Run Detailed Implementation Tests")
        print("          test_env - Run Environment Tests")
        print("          test_gpu - Run GPU Testing Module")
        print("")
        print("For example,")
        print("\t$ musclex eq")
        print("\t$ musclex eq -h -i test.tif -s config.json")
        print("")
        print("** Musclex headless arguments (works for eq, qf and di):")
        print("    $ musclex eq|di|qf -h -i|-f <file.tif|testfolder> [-s config.json] [-d] ")
        print("arguments:")
        print("-f <foldername> or -i <filename>")
        print("-d (optional) delete existing cache")
        print("-s (optional) <input setting file>")
        print("")
        print("Note: To generate the setting file, use the interactive muclex, set parameter in it, then select save the current settings. \nThis will create the necessary setting file. If a setting file is not provided, default settings will be used")
        print("Note: If a hdf file does not exist, the program will use the default file. You can generate a hdf step size file using the interactive version (set step size, click ok, the file will be automaticly saved)")
        print("")
        print("More details : https://musclex.readthedocs.io")
        print("Submit Feedback or issues : https://www.github.com/biocatiit/musclex/issues\n\n")

if __name__ == "__main__":
    main(sys.argv)
