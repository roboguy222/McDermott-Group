# Qubit spectroscopy with a network analyzer.

import os
import numpy as np

from labrad.units import V, GHz, MHz, dB, dBm

import qubit_na_experiment


comp_name = os.environ['COMPUTERNAME'].lower()
Resources = [   
                { # SIM Voltage Source
                    'Interface': 'SIM928 Voltage Source',
                    'Address': ('SIM900 - ' + comp_name + 
                                ' GPIB Bus - GPIB0::26::INSTR::SIM900::3'),
                    'Variables': 'Qubit Flux Bias Voltage'
                },
                { # Network Analyzer
                    'Interface': 'Network Analyzer',
                    'Variables': {'NA Center Frequency': {'Setting': 'Center Frequency'},
                                  'NA Frequency Span': {'Setting': 'Span Frequency'},
                                  'NA Source Power': {'Setting': 'Source Power'},
                                  'NA Sweep Points': {'Setting': 'Sweep Points'},
                                  'NA Average Points': {'Setting': 'Average Points'},
                                  'NA Start Frequency': {'Setting': 'Start Frequency'},
                                  'NA Stop Frequency': {'Setting': 'Stop Frequency'},
                                  'Trace': {'Setting': 'Get Trace'}}
                },
                { # Leiden Fridge
                    'Interface': 'Leiden',
                    'Variables': {'Temperature': {'Setting': 'Mix Temperature'}}
                },
                { # Readings entered manually, software parameters
                    'Interface': None,
                    'Variables': []
                }
            ]

# Experiment Information
ExptInfo = {
            'Device Name': 'MH060',
            'User': 'Guilhem Ribeill',
            'Base Path': 'Z:\mcdermott-group\Data\Syracuse Qubits\MH060',
            'Experiment Name': 'FreqPower2D',
            'Comments': '-10 dB on input of NA' 
           }
 
# Experiment Variables
ExptVars = {
            'NA Center Frequency': 4.914 * GHz,
            'NA Frequency Span': 25 * MHz,
            
            'NA Source Power': -63 * dBm,
            
            'NA Sweep Points': 801,
            'NA Average Points': 500,
            
            'Qubit Flux Bias Voltage': 0 * V 
           }

with qubit_na_experiment.QubitNAExperiment() as run:
    
    run.set_experiment(ExptInfo, Resources, ExptVars) 
    
    #run.sweep('NA Source Power', np.linspace(-80, -20, 121) * dBm, save=True)
    run.sweep('Qubit Flux Bias Voltage', np.linspace(-3, 3, 201) * V, save=True)