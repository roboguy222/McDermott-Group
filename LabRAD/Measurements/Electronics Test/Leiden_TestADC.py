# HEMT read out of a qubit connected to a resonator.

import os
import numpy as np

from labrad.units import (us, ns, V, GHz, MHz, rad, dB, dBm,
                          DACUnits, PreAmpTimeCounts)

import adc_test_experiment


comp_name = os.environ['COMPUTERNAME'].lower()
Resources = [ {
                'Interface': 'GHz FPGA Boards',
                'Boards': [
                           'Leiden Board DAC 4',
                           'Leiden Board ADC 7'
                          ],

                'Leiden Board DAC 4': {
                                        'DAC A': 'RF Q',
                                        'DAC B': 'RF I',
                                      },
                'Leiden Board ADC 7': {
                                        'RunMode': 'demodulate', #'average'
                                        'FilterType': 'square',
                                        'FilterWidth': 4000 * ns,
                                        'FilterStartAt': 0 * ns,
                                        'FilterLength': 4000 * ns,
                                        'FilterStretchAt': 0 * ns,
                                        'FilterStretchLen': 0 * ns,
                                        'DemodPhase': 0 * rad,
                                        'DemodCosAmp': 255,
                                        'DemodSinAmp': 255,
                                        'DemodFreq': -200 * MHz,
                                        'ADCDelay': 0 * ns,
                                        'Data': True
                                      },
                'Variables': {
                                'Init Time': {},
                                'RF SB Frequency': {'Value': 0 * MHz},
                                'RF Amplitude': {'Value': 0 * DACUnits},
                                'RF Time': {'Value': 0 * ns},
                                'RF Phase': {'Value': 0 * rad},
                                'ADC Wait Time': {'Value': 0 * ns},
                                'ADC Demod Frequency': {'Value': -50 * MHz},
                                'Spiral': {'Value': 0}
                             }
                },
                { # Lab RF Generator
                    'Interface': 'Lab Brick RF Generator',
                    'Serial Number': 10776,
                    'Variables': {  
                                    'RF Power': {'Setting': 'Power'}, 
                                    'RF Frequency': {'Setting': 'Frequency'}
                                 }
                },
                { # Lab Brick Attenuator
                    'Interface': 'Lab Brick Attenuator',
                    'Serial Number': 7032,
                    'Variables': 'RF Attenuation'
                },
                { # Leiden
                    'Interface': 'Leiden',
                    'Variables': {'Temperature': {'Setting': 'Mix Temperature'}}
                },
                { # Readings entered manually, software parameters.
                    'Interface': None,
                    'Variables': ['Reps', 'Runs'],
                }
            ]

# Experiment Information
ExptInfo = {
            'Device Name': 'ADC7',
            'User': 'Guilhem Ribeill',
            'Base Path': r'Z:\mcdermott-group\Data\ADC Testing',
            #'Base Path': r'C:\Users\5107-1\Desktop\Data\Syracuse Qubits\Leiden DR 2015-10-22 - Qubits and JPMs',
            'Experiment Name': 'ADCStressTest2',
            'Comments': 'ADC demodulation test. LabBrick RF - DAC4 IQ mix - LabBrick attenuator - MiniCircuits Amp - 7dB atten - 4.9-6.2 GHz BP - ADC7 IQ' 
           }
 
# Experiment Variables
ExptVars = {
            'Reps': 2000, # should not exceed ~5,000, use argument "runs" in sweep parameters instead 

            'Init Time': 100 * us,
            

            'RF Frequency': 5.1 * GHz,
            'RF Power': 10 * dBm,
            'RF Attenuation': 10 * dB, #42 * dB, # should be in (0, 63] range
            'RF SB Frequency': 125 * MHz, # no filters on the IQ-mixer
            'RF Amplitude': 1.0 * DACUnits,
            'RF Phase': 0.0 * rad,
            'RF Time': 4000 * ns,
            
            'Spiral': 0,
                         
            'ADC Demod Frequency': 125 * MHz
           }


with adc_test_experiment.ADCTestDemodulation() as run:
    
    run.set_experiment(ExptInfo, Resources, ExptVars)
    
    # run.single_shot_iqs(save=True, plot_data=True)
    # run.single_shot_osc(save=False, plot_data=['I', 'Q'])
    # run.avg_osc(save=True, plot_data=['I', 'Q'], runs=1000)
   
    # run.sweep('RF Amplitude', np.linspace(0, 1, 101) * DACUnits, 
              # print_data=['I','Q'],plot_data=['I','Q'],
              # save=True, runs=1, max_data_dim=2)
    # for i in xrange(100):
        # run.sweep('RF Phase', np.linspace(0, 2*np.pi, 73) * rad, 
                  # print_data=['I','Q'],plot_data=['I','Q'],
                  # save=True, runs=1, max_data_dim=2)
              
    # run.sweep('RF SB Frequency', np.linspace(0, 200, 201) * MHz, 
                # print_data=['I', 'Q'], plot_data=['I','Q','Amplitdue'],
                # save=True, runs=1, max_data_dim=1)
                
    # run.sweep('RF Time', np.linspace(0, 4000, 251) * ns, 
                # print_data=['I','Q'], plot_data = ['I', 'Q', 'Amplitude'],
                # save=True, runs=1, max_data_dim=1)
                
    # run.sweep('RF Attenuation', np.linspace(3, 60, 58) * dB, 
                # print_data=['I', 'Q'], plot_data=['Amplitude'],
                # save=True, runs=1, max_data_dim=1)
with adc_test_experiment.ADCTestLogSpiral() as run:
    
    run.set_experiment(ExptInfo, Resources, ExptVars)  
    
    run.sweep('Spiral', np.linspace(0, 20, 101), print_data=['I', 'Q'],
                plot_data=['I', 'Q'], save=True, runs = 1,
                max_data_dim=2)