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

import musclex
import fabio
from os.path import exists, isfile
from lmfit import Model, Parameters
from lmfit.models import GaussianModel, SkewedGaussianModel, VoigtModel
import pickle
from ..utils.file_manager import fullPath, createFolder
from ..utils.histogram_processor import smooth, movePeaks, getPeakInformations, convexHull
import copy
import numpy as np
from sklearn.metrics import r2_score

class ProjectionProcessor():
    def __init__(self, dir_path, file_name):
        self.dir_path = dir_path
        self.filename = file_name
        img = fabio.open(fullPath(dir_path, file_name)).data
        # img -= img.min()
        self.orig_img = img
        self.version = musclex.__version__
        cache = self.loadCache()
        if cache is None:
            # info dictionary will save all results
            self.info = {
                'box_names' : set(),
                'boxes' : {},
                'types' : {},
                'hists' : {},
                'peaks' : {},
                'bgsubs' : {},
                'hull_ranges':{},
                'hists2': {},
                'fit_results':{},
                'subtracted_hists' : {},
                'moved_peaks':{},
                'baselines':{},
                'centroids':{},
                'widths': {}
            }
        else:
            self.info = cache

    def addBox(self, name, box, type, bgsub):
        """
        Add a box to info. If it exists and it changed, clear all old result
        :param name: box name
        :param box: box coordinates
        :param type: box type 'v' ad vertical, 'h' as horizontal
        :param bgsub: background subtraction method 0 = fitting gaussians, 1 = convex hull
        :return:
        """
        box_names = self.info['box_names']
        if name in box_names and self.info['boxes'][name] != box:
            self.removeInfo(name)
            self.addBox(name, box, type, bgsub)
        else:
            box_names.add(name)
            self.info['boxes'][name] = box
            self.info['types'][name] = type
            self.info['bgsubs'][name] = bgsub

    def addPeaks(self, name, peaks):
        """
        Add peaks to a box.
        :param name: box name
        :param peaks: peaks
        :return:
        """
        box_names = self.info['box_names']
        if name in box_names:
            all_peaks = self.info['peaks']
            if all_peaks.has_key(name) and all_peaks[name] == peaks:
                return
            all_peaks[name] = peaks
            skip_list = ['box_names', 'boxes', 'types', 'peaks', 'hists', 'bgsubs']
            for k in self.info.keys():
                if k not in skip_list:
                    self.removeInfo(name, k)
        else:
            print "Warning : box name is invalid."

    def removePeaks(self, name):
        """
        Remove all peaks from a box
        :param name: box name
        :return:
        """
        skip_list = ['box_names', 'boxes', 'types', 'bgsubs']
        for k in self.info.keys():
            if k not in skip_list:
                self.removeInfo(name, k)

    def process(self, settings = {}):
        """
        All processing steps - all settings are provided by Projection Traces app as a dictionary
        """
        self.updateSettings(settings)
        self.getHistograms()
        self.applyConvexhull()
        self.fitModel()
        # self.getOtherResults()
        self.getBackgroundSubtractedHistograms()
        self.getPeakInfos()
        self.cacheInfo()

    def updateSettings(self, settings):
        if settings.has_key('boxes'):
            new_boxes = settings['boxes']
            types = settings['types']
            bgsubs = settings['bgsubs']
            old_boxes = self.info['boxes']
            all_name = new_boxes.keys()
            all_name.extend(old_boxes.keys())
            all_name = set(all_name)
            for name in all_name:
                if name in new_boxes.keys():
                    self.addBox(name, new_boxes[name], types[name], bgsubs[name])
                else:
                    self.removeInfo(name)
            del settings['boxes']
            del settings['types']
            del settings['bgsubs']

        if settings.has_key('peaks'):
            new_peaks = settings['peaks']
            old_peaks = self.info['peaks']
            all_name = new_peaks.keys()
            all_name.extend(old_peaks.keys())
            all_name = set(all_name)
            for name in all_name:
                if name in new_peaks.keys():
                    self.addPeaks(name, new_peaks[name])
                else:
                    self.removePeaks(name)
            del settings['peaks']

        if settings.has_key('hull_ranges'):
            new = settings['hull_ranges']
            current = self.info['hull_ranges']
            current.update(new)
            del settings['hull_ranges']

        self.info.update(settings)

    def getHistograms(self):
        """
        Obtain projected intensity for each box
        """
        box_names = self.info['box_names']
        if len(box_names) > 0:
            boxes = self.info['boxes']
            types = self.info['types']
            hists = self.info['hists']
            img = copy.copy(self.orig_img)
            for name in box_names:
                if not hists.has_key(name):
                    t = types[name]
                    b = boxes[name]
                    x1 = b[0][0]
                    x2 = b[0][1]
                    y1 = b[1][0]
                    y2 = b[1][1]
                    area = img[y1:y2+1, x1:x2+1]
                    if t == 'h':
                        hist = np.sum(area, axis=0)
                    else:
                        hist = np.sum(area, axis=1)
                    hists[name] = hist

    def applyConvexhull(self):
        """
        Apply Convex hull to the projected intensity if background subtraction method is 1 (Convex hull)
        :return:
        """
        box_names = self.info['box_names']
        if len(box_names) > 0:
            boxes = self.info['boxes']
            all_peaks = self.info['peaks']
            hists = self.info['hists']
            bgsubs = self.info['bgsubs']
            hists2 = self.info['hists2']
            types = self.info['types']
            hull_ranges = self.info['hull_ranges']
            for name in box_names:
                if hists2.has_key(name):
                    continue

                if bgsubs[name] == 1 and all_peaks.has_key(name) and len(all_peaks[name]) > 0:
                    # apply convex hull to the left and right if peaks are specified
                    box = boxes[name]
                    hist = hists[name]
                    peaks = all_peaks[name]
                    start_x = box[0][0]
                    start_y = box[1][0]

                    if types[name] == 'h':
                        centerX = self.orig_img.shape[1] / 2 - start_x
                    else:
                        centerX = self.orig_img.shape[0] / 2 - start_y

                    right_hist = hist[centerX:]
                    left_hist = hist[:centerX][::-1]
                    min_len = min(len(right_hist), len(left_hist))

                    if not hull_ranges.has_key(name):
                        start = max(min(peaks) - 15, 10)
                        end = min(max(peaks) + 15, min_len)
                        hull_ranges[name] = (start, end)

                    # find start and end points
                    (start, end) = hull_ranges[name]

                    left_hull = convexHull(left_hist, start, end)[::-1]
                    right_hull = convexHull(right_hist, start, end)

                    # import matplotlib.pyplot as plt
                    # bg = right_hist-right_hull
                    # fig = plt.figure()
                    # ax = fig.add_subplot(111)
                    # ax.plot(bg)
                    # fig.show()

                    hists2[name] = np.append(left_hull, right_hull)
                else:
                    # use original histogram
                    hists2[name] = copy.copy(hists[name])

                self.removeInfo(name, 'fit_results')

    def fitModel(self):
        """
        Fit model to histogram
        Fit results will be kept in self.info["fit_results"].
        """
        box_names = self.info['box_names']
        all_hists = self.info['hists2']
        bgsubs = self.info['bgsubs']
        all_peaks = self.info['peaks']
        all_boxes = self.info['boxes']
        fit_results = self.info['fit_results']

        for name in box_names:
            hist = np.array(all_hists[name])

            if not all_peaks.has_key(name) or len(all_peaks[name]) == 0 or fit_results.has_key(name):
                continue

            peaks = all_peaks[name]
            box = all_boxes[name]
            start_x = box[0][0]
            start_y = box[1][0]

            x = np.arange(0, len(hist))

            int_vars = {
                'x' : x
            }

            # Initial Parameters
            params = Parameters()

            # Init Center X
            if self.info['types'][name] == 'h':
                init_center = self.orig_img.shape[1] / 2 - 0.5 - start_x
            else:
                init_center = self.orig_img.shape[0] / 2 - 0.5 - start_y

            params.add('centerX', init_center, min=init_center - 1., max=init_center + 1.)

            if bgsubs[name] == 1:
                # Convex hull has been applied, so we don't need to fit 3 gaussian anymore
                int_vars['bg_line'] = 0
                int_vars['bg_sigma'] = 1
                int_vars['bg_amplitude'] = 0
                int_vars['center_sigma1'] = 1
                int_vars['center_amplitude1'] = 0
                int_vars['center_sigma2'] = 1
                int_vars['center_amplitude2'] = 0
            else:
                # Init linear background
                # params.add('bg_line', 0, min=0)
                int_vars['bg_line'] = 0

                # Init background params
                params.add('bg_sigma', len(hist)/3., min=1, max=len(hist)*2+1.)
                params.add('bg_amplitude', 0, min=-1, max=sum(hist)+1.)

                # Init Meridian params1
                params.add('center_sigma1', 15, min=1, max=len(hist)+1.)
                params.add('center_amplitude1', sum(hist) / 20., min=-1, max=sum(hist) + 1.)

                # Init Meridian params2
                params.add('center_sigma2',5 , min=1, max=len(hist)+1.)
                params.add('center_amplitude2', sum(hist) / 20., min=-1, max=sum(hist)+1.)

            # Init peaks params
            for j,p in enumerate(peaks):
                params.add('p_' + str(j), p, min=p - 10., max=p + 10.)
                params.add('sigma' + str(j), 10, min=1, max=50.)
                params.add('amplitude' + str(j), sum(hist)/10., min=-1)
                # params.add('gamma' + str(j), 0. , min=0., max=30)

            # Fit model
            model = Model(layerlineModel, independent_vars=int_vars.keys())
            result = model.fit(hist, verbose=False, params=params, fit_kws={'nan_policy':'propagate'}, **int_vars)
            if result is not None:
                #
                # import matplotlib.pyplot as plt
                # fig = plt.figure()
                # ax = fig.add_subplot(111)
                # ax.cla()
                # ax.plot(hist, color='g')
                # ax.plot(layerlineModel(x, **result.values), color='b')
                # fig.show()
                result_dict = result.values
                int_vars.pop('x')
                result_dict.update(int_vars)

                result_dict['error'] = 1. - r2_score(hist, layerlineModel(x, **result_dict))
                self.info['fit_results'][name] = result_dict
                self.removeInfo(name, 'subtracted_hists')
                print "Box :", name
                print "Fitting Result :", result_dict
                print "Fitting Error :", result_dict['error']
                print "---"


    def getBackgroundSubtractedHistograms(self):
        """
        Get Background Subtracted Histograms by subtract the original histogram by background from fitting model
        :return:
        """
        box_names = self.info['box_names']
        all_hists = self.info['hists2']
        fit_results = self.info['fit_results']
        subt_hists = self.info['subtracted_hists']
        for name in box_names:
            if subt_hists.has_key(name) or not fit_results.has_key(name):
                continue

            # Get subtracted histogram if fit result exists
            fit_result = fit_results[name]
            hist = all_hists[name]
            xs = np.arange(0, len(hist))
            background = layerlineModelBackground(xs, **fit_result)
            subt_hists[name] = hist-background
            self.removeInfo(name, 'moved_peaks')

    def getPeakInfos(self):
        """
        Get peaks' infomation including baseline and centroids
        :return:
        """

        box_names = self.info['box_names']
        all_hists = self.info['subtracted_hists']
        fit_results = self.info['fit_results']
        moved_peaks = self.info['moved_peaks']
        all_baselines = self.info['baselines']
        all_centroids = self.info['centroids']
        all_widths = self.info['widths']

        for name in box_names:

            if not all_hists.has_key(name):
                continue

            ### Find real peak locations in the box (not distance from center)
            model = fit_results[name]
            hist = all_hists[name]

            if not moved_peaks.has_key(name):
                peaks = []
                i = 0
                while 'p_'+str(i) in model.keys():
                    peaks.append(int(round(model['centerX']+model['p_'+str(i)])))
                    i+=1
                peaks = movePeaks(hist, peaks, 20)
                moved_peaks[name] = peaks
                self.removeInfo(name, 'baselines')

            peaks = moved_peaks[name]

            ### Calculate Baselines
            if not all_baselines.has_key(name):
                baselines = []
                for p in peaks:
                    baselines.append(hist[p]*0.5)
                all_baselines[name] = baselines
                self.removeInfo(name, 'centroids')

            baselines = all_baselines[name]

            if not all_centroids.has_key(name):
                results = getPeakInformations(hist, peaks, baselines)
                all_centroids[name] = results['centroids'] - model['centerX']
                all_widths[name] = results['widths']

    def setBaseline(self, box_name, peak_num, new_baseline):
        """
        Change baseline and clear centroid and width for the specific box and peak
        :param box_name: box name (str)
        :param peak_num: peak name (int)
        :param new_baseline: new baseline value or percentage (str)
        :return:
        """
        new_baseline = str(new_baseline)
        baselines = self.info['baselines'][box_name]
        peak = self.info['moved_peaks'][box_name][peak_num]
        hist = self.info['subtracted_hists'][box_name]
        height = hist[peak]
        if "%" in new_baseline:
            # if new_baseline contain "%", baseline value will use this as percent of peak height
            percent = float(new_baseline.rstrip("%"))
            baseline = height * percent / 100.
        elif len(new_baseline) == 0:
            # if new_baseline is empty, baseline will by half-height
            baseline = float(height * .5)
        else:
            baseline = float(new_baseline)

        if height > baseline:
            baselines[peak_num] = baseline
            self.removeInfo(box_name, 'centroids')
            self.removeInfo(box_name, 'widths')

    def removeInfo(self, name, k = None):
        """
        Remove information from info dictionary by k as a key. If k is None, remove all information in the dictionary
        :param name: box name
        :param k: key of dictionary
        :return: -
        """
        ignore_list = ['lambda_sdd', 'program_version']

        if k is not None and self.info.has_key(k) and k not in ignore_list:
            d = self.info[k]
            if d.has_key(name):
                del d[name]

        if k is None:
            for k in self.info.keys():
                d = self.info[k]
                if k == 'box_names':
                    d.remove(name)
                else:
                    self.removeInfo(name, k)

    def loadCache(self):
        """
        Load info dict from cache. Cache file will be filename.info in folder "bm_cache"
        :return: cached info (dict)
        """
        cache_path = fullPath(self.dir_path, "pt_cache")
        cache_file = fullPath(cache_path, self.filename + '.info')

        if exists(cache_path) and isfile(cache_file):
            cinfo = pickle.load(open(cache_file, "rb"))
            if cinfo != None:
                if cinfo['program_version'] == self.version:
                    return cinfo
        return None

    def cacheInfo(self):
        """
        Save info dict to cache. Cache file will be save as filename.info in folder "qf_cache"
        :return: -
        """
        cache_path = fullPath(self.dir_path, 'pt_cache')
        createFolder(cache_path)
        cache_file = fullPath(cache_path, self.filename + '.info')

        self.info["program_version"] = self.version
        pickle.dump(self.info, open(cache_file, "wb"))


def layerlineModel(x, centerX, bg_line, bg_sigma, bg_amplitude, center_sigma1, center_amplitude1, center_sigma2, center_amplitude2, **kwargs):
    """
    Model for fitting layer line pattern
    :param x: x axis
    :param centerX: center of x axis
    :param bg_line: linear background
    :param bg_sigma: background sigma
    :param bg_amplitude: background amplitude
    :param center_sigma1: meridian background sigma
    :param center_amplitude1: meridian background amplitude
    :param center_sigma2: meridian sigma
    :param center_amplitude2: meridian amplitude
    :param kwargs: other peaks properties
    :return:
    """

    #### Background and Meridian
    result = layerlineModelBackground(x, centerX, bg_line, bg_sigma, bg_amplitude, center_sigma1, center_amplitude1, center_sigma2, center_amplitude2,**kwargs)

    #### Other peaks
    i = 0
    while 'p_'+str(i) in kwargs:
        p = kwargs['p_'+str(i)]
        sigma = kwargs['sigma'+str(i)]
        amplitude = kwargs['amplitude' + str(i)]
        if kwargs.has_key('gamma' + str(i)):
            gamma = kwargs['gamma' + str(i)]

            mod = VoigtModel()
            result += mod.eval(x=x, amplitude=amplitude, center=centerX + p, sigma=sigma, gamma=gamma)
            result += mod.eval(x=x, amplitude=amplitude, center=centerX - p, sigma=sigma, gamma=-gamma)
        else:
            mod = GaussianModel()
            result += mod.eval(x=x, amplitude=amplitude, center=centerX + p, sigma=sigma)
            result += mod.eval(x=x, amplitude=amplitude, center=centerX - p, sigma=sigma)

        i += 1

    return result

def layerlineModelBackground(x, centerX, bg_line, bg_sigma, bg_amplitude, center_sigma1, center_amplitude1, center_sigma2, center_amplitude2,**kwargs):
    """
    Model for fitting layer line pattern
    :param x: x axis
    :param centerX: center of x axis
    :param bg_line: linear background
    :param bg_sigma: background sigma
    :param bg_amplitude: background amplitude
    :param center_sigma1: meridian background sigma
    :param center_amplitude1: meridian background amplitude
    :param center_sigma2: meridian sigma
    :param center_amplitude2: meridian amplitude
    :param kwargs: nothing
    :return:
    """
    return layerlineBackground(x, centerX, bg_line, bg_sigma, bg_amplitude) + \
           meridianBackground(x, centerX, center_sigma1, center_amplitude1) + \
           meridianGauss(x, centerX, center_sigma2, center_amplitude2)


def layerlineBackground(x, centerX, bg_line, bg_sigma, bg_amplitude, **kwargs):
    """
    Model for largest background of layer line pattern
    :param x: x axis
    :param centerX: center of x axis
    :param bg_line: linear background
    :param bg_sigma: background sigma
    :param bg_amplitude: background amplitude
    :param kwargs: nothing
    :return:
    """
    mod = GaussianModel()
    return  mod.eval(x=x, amplitude=bg_amplitude, center=centerX, sigma=bg_sigma) + bg_line

def meridianBackground(x, centerX, center_sigma1, center_amplitude1, **kwargs):
    """
    Model for background of meridian of layer line pattern
    :param x: x axis
    :param centerX: center of x axis
    :param center_sigma1: meridian background sigma
    :param center_amplitude1: meridian background amplitude
    :param kwargs: nothing
    :return:
    """
    mod = GaussianModel()
    return mod.eval(x=x, amplitude=center_amplitude1, center=centerX, sigma=center_sigma1)

def meridianGauss(x, centerX, center_sigma2, center_amplitude2, **kwargs):
    """
    Model for background of layer line pattern
    :param x: x axis
    :param centerX: center of x axis
    :param center_sigma2: meridian sigma
    :param center_amplitude2: meridian amplitude
    :param kwargs:
    :return:
    """
    mod = GaussianModel()
    return mod.eval(x=x, amplitude=center_amplitude2, center=centerX, sigma=center_sigma2)