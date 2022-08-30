from scipy.stats import norm
import scipy.signal as sig
from scipy.io import wavfile
import numpy as np
import math

import copy

def bandpower(ps, mode='psd'):
    """
    estimate bandpower, see https://de.mathworks.com/help/signal/ref/bandpower.html
    """
    if mode=='time':
        x = ps
        l2norm = linalg.norm(x)**2./len(x)
        return l2norm
    elif mode == 'psd':
        return sum(ps)   
        
def getIndizesAroundPeak(arr, peakIndex,searchWidth=1000):
    peakBins = []
    magMax = arr[peakIndex]
    curVal = magMax
    for i in range(searchWidth):
        newBin = peakIndex+i
        newVal = arr[newBin]
        if newVal>curVal:
            break
        else:
            peakBins.append(int(newBin))
            curVal=newVal
    curVal = magMax
    for i in range(searchWidth):
        newBin = peakIndex-i
        newVal = arr[newBin]
        if newVal>curVal:
            break
        else:
            peakBins.append(int(newBin))
            curVal=newVal
    return np.array(list(set(peakBins)))
    
def freqToBin(fAxis, Freq):
    return np.argmin(abs(fAxis-Freq))

def getPeakInArea(psd, faxis, estimation, searchWidthHz = 10):
    """
    returns bin and frequency of the maximum in an area
    """
    binLow = freqToBin(faxis, estimation-searchWidthHz)
    binHi = freqToBin(faxis, estimation+searchWidthHz)
    
    try: 
        mx = np.argmax(psd[binLow:binHi])
    except:
        mx = 0
    peakbin = binLow+mx
    return peakbin, faxis[peakbin]
    

def getHarmonics(fund,sr,nHarmonics=6,aliased=False):
    harmonicMultipliers = np.arange(2,nHarmonics+2)
    harmonicFs = fund*harmonicMultipliers
    if not aliased:
        harmonicFs[harmonicFs>sr/2] = -1
        harmonicFs = np.delete(harmonicFs,harmonicFs==-1)
    else:
        nyqZone = np.floor(harmonicFs/(sr/2))
        oddEvenNyq = nyqZone%2  
        harmonicFs = np.mod(harmonicFs,sr/2)
        harmonicFs[oddEvenNyq==1] = (sr/2)-harmonicFs[oddEvenNyq==1]
    return harmonicFs 
def conv_to_float(num):
    if (num >= 32767):
        new = 1.0
    elif (num <= -32768):
        new = -1.0
    else:
        new = num / 32768.0
    return new
    
def noise_detector(y,sr):	
	#sr, y = wavfile.read('Downloads/babble_15dB/15dB/sp03_babble_sn15.wav')
	#sr, y = wavfile.read('output.wav')
	#y = [conv_to_float(num) for num in y]
	#y = np.array(y, dtype=np.float64)
	#print(y)
    faxis,ps = sig.periodogram(y,fs=sr, window=('kaiser',38)) #get periodogram, parametrized like in matlab

    fundBin = np.argmax(ps) #estimate fundamental at maximum amplitude, get the bin number
    fundIndizes = getIndizesAroundPeak(ps,fundBin) #get bin numbers around fundamental peak
    fundFrequency = faxis[fundBin] #frequency of fundamental

    nHarmonics = 6
    harmonicFs = getHarmonics(fundFrequency,sr,nHarmonics=nHarmonics,aliased=True) #get harmonic frequencies
	#print('harmonic frequencies estimated: {}'.format(harmonicFs))

    harmonicBorders = np.zeros([2,nHarmonics],dtype=np.int16).T
    fullHarmonicBins = np.array([], dtype=np.int16)
    fullHarmonicBinList = []
    harmPeakFreqs=[]
    harmPeaks=[]
    for i,harmonic in enumerate(harmonicFs):
        searcharea = 0.1*fundFrequency
        estimation = harmonic
	    
        binNum, freq = getPeakInArea(ps,faxis,estimation,searcharea)
        harmPeakFreqs.append(freq)
        harmPeaks.append(ps[binNum])
        allBins = getIndizesAroundPeak(ps, binNum,searchWidth=1000)
        fullHarmonicBins=np.append(fullHarmonicBins,allBins)
        fullHarmonicBinList.append(allBins)
        harmonicBorders[i,:] = [allBins[0], allBins[-1]]
	    
    fundIndizes.sort()

    noisePrepared = copy.copy(ps)
    noisePrepared[fundIndizes] = 0
    noisePrepared[fullHarmonicBins] = 0
    noiseMean = np.median(noisePrepared[noisePrepared!=0])
    noisePrepared[fundIndizes] = noiseMean 
    noisePrepared[fullHarmonicBins] = noiseMean

    noisePower = bandpower(noisePrepared)
    noisePower = 10*np.log10(noisePower)

    if noisePower >= 0:
        return 'measured Noise: {} dB\n Too noisy'.format(noisePower)
    else:
        return 'measured Noise: {} dB\n Acceptable noise'.format(noisePower)

	   
