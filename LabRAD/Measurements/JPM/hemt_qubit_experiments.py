# Copyright (C) 2015 Guilhem Ribeill, Ivan Pechenezhskiy
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
if __file__ in [f for f in os.listdir('.') if os.path.isfile(f)]:
    # This is executed when the script is loaded by the labradnode.
    SCRIPT_PATH = os.path.dirname(os.getcwd())
else:
    # This is executed if the script is started by clicking or
    # from a command line.
    SCRIPT_PATH = os.path.dirname(__file__)
LABRAD_PATH = os.path.join(SCRIPT_PATH.rsplit('LabRAD', 1)[0])
import sys
if LABRAD_PATH not in sys.path:
    sys.path.append(LABRAD_PATH)

import numpy as np
import matplotlib.pyplot as plt

import labrad.units as units

import LabRAD.Measurements.General.experiment as expt
import LabRAD.Measurements.General.pulse_shapes as pulse
import LabRAD.Servers.Instruments.GHzBoards.command_sequences as seq
import data_processing


class HEMTExperiment(expt.Experiment):        
    def single_shot_iqs(self, adc=None, save=False, plot_data=None):
        """
        Run a single experiment, saving individual I and Q points.
        
        Inputs:
            adc: ADC board name. If the board is not specified
                and there is only one board in experiment resource 
                dictionary than it will be used by default.
            save: if True save the data (default: False).
            plot_data: if True plot the data (default: True).
        Output:
            None.
        """
        adc = self.boards.get_adc(adc)
        previous_adc_mode = self.boards.get_adc_setting('RunMode', adc)
        self.boards.set_adc_setting('RunMode', 'demodulate', adc)
        
        data = self._process_data(self.run_once())
        
        self.boards.set_adc_setting('RunMode', previous_adc_mode, adc)
        
        if plot_data is not None:
            self._plot_iqs(data)

        # Save the data.
        if save:
            self._save_data(data)

    def single_shot_osc(self, adc=None, save=False, plot_data=None):
        """
        Run a single shot experiment in average mode, and save the 
        time-demodulated data to file.
        
        Inputs: 
            adc: ADC board name. If the board is not specified
                and there is only one board in experiment resource
                dictionary than it will be used by default.
            save: if True save the data if save is True (default: False).
            plot_data: data variables to plot (default: None).
        Output:
            None.
        """
        self.avg_osc(adc, save, plot_data, runs=1)

    def avg_osc(self, adc=None, save=False, plot_data=None, runs=100):
        """
        Run a single experiment in average mode specified number of
        times and average the results together.
        
        Inputs:
            adc: ADC board name.
            save: if True save the data if save is True (default: False).
            plot_data: data variables to plot.
            runs: number of runs (default: 100).
        Output:
            None.
        """
        print('\nCollecting the ADC data...\n')
              
        self._run_status= ''
        self._run_message = ''
        
        adc = self.boards.get_adc(adc)
        previous_adc_mode = self.boards.get_adc_setting('RunMode', adc)
        self.boards.set_adc_setting('RunMode', 'average', adc)
            
        data = self._process_data(self.run_once())

        # Make a list of data variables that should be plotted.
        if plot_data is not None:
            for var in self._combine_strs(plot_data):
                if var not in data:
                    print("Warning: variable '" + var + 
                    "' is not found among the data dictionary keys: " + 
                    str(data.keys()) + ".")
            plot_data = [var for var in
                    self._combine_strs(plot_data) if var in data]
        if plot_data:
            self._init_1d_plot([['ADC Time']], [[data['ADC Time']['Value']]],
                    data, plot_data)
 
        if runs > 1:        # Run multiple measurement shots.
            print('\t[ESC]:\tAbort the run.' + 
                  '\n\t[S]:\tAbort the run but [s]ave the data.\n')
            sys.stdout.write('Progress: 0%')
            self.add_var('Runs', runs)
            stepsize = max(int(round(runs / 25)), 1)
            data_to_plot = {}
            for key in data:
                data_to_plot[key] = data[key].copy()
            for r in range(runs - 1):
                # Check if the specified keys are pressed.
                self._listen_to_keyboard(recog_keys=[27, 83, 115], 
                        clear_buffer=False)
                if self._run_status in ['abort', 'abort-and-save']:
                    self.value('Runs', r + 1, output=False)
                    sys.stdout.write(str(round(100 * self.value('Runs') / float(runs), 1)) + '%\n')
                    print(self._run_message)
                    break  
                run_data = self.run_once()
                for key in data:
                    if data[key]['Type'] == 'Dependent':
                        # Accumulate the data values.
                        # These values should be divided by the actual
                        # number of Reps to get the average values.
                        data[key]['Value'] = data[key]['Value'] + run_data[key]['Value']
                if np.mod(r, stepsize) == 0:
                    sys.stdout.write('.')
                    if plot_data:
                        for key in plot_data:
                            data_to_plot[key]['Value'] = data[key]['Value'] / float(r + 1)
                        self._update_1d_plot([['ADC Time']], [[data['ADC Time']['Value']]],
                                data_to_plot, plot_data, np.size(data['ADC Time']['Value']) - 1)
                if r == runs - 2:
                    sys.stdout.write('100%\n')
            for key in data:
                if 'Value' in data[key] and data[key]['Type'] == 'Dependent':
                    data[key]['Value'] = data[key]['Value'] / float(runs)
        
        if plot_data:        # Save the data.
            self._update_1d_plot([['ADC Time']], [[data['ADC Time']['Value']]],
                    data, plot_data, np.size(data['ADC Time']['Value']) - 1)
        
        self.boards.set_adc_setting('RunMode', previous_adc_mode, adc)
        
        # Save the data.
        if ((save and self._run_status != 'abort') or
            self._run_status == 'abort-and-save'):
            self._save_data(data)
        
    def _plot_iqs(self, data):
        plt.ion()
        plt.figure(13)
        plt.plot(data['Single Shot Is']['Value'], data['Single Shot Qs']['Value'], 'b.')
        plt.xlabel('I [ADC units]')
        plt.ylabel('Q [ADC units]')
        plt.title('Single Shot Is and Qs')
        plt.draw()


class HEMTQubitReadout(HEMTExperiment):
    """
    Read out a qubit connected to a resonator.
    """
    def run_once(self, adc=None, plot_waveforms=False):
        #QUBIT VARIABLES###########################################################################
        self.send_request('Qubit Attenuation')                          # qubit attenuation
        self.send_request('Qubit Power')                                # qubit power
        if self.value('Qubit Frequency') is not None:
            if self.value('Qubit SB Frequency') is not None:            # qubit frequency
                self.send_request('Qubit Frequency',
                        value=self.value('Qubit Frequency') + 
                              self.value('Qubit SB Frequency'))
            else:
                self.send_request('Qubit Frequency')
    
        #RF DRIVE (READOUT) VARIABLES##############################################################
        self.send_request('Readout Attenuation')                        # readout attenuation
        self.send_request('Readout Power')                              # readout power
        if self.value('Readout Frequency') is not None:
            if self.value('Readout SB Frequency') is not None:          # readout frequency
                self.send_request('Readout Frequency',
                        value=self.value('Readout Frequency') + 
                              self.value('Readout SB Frequency'))
            else:
                self.send_request('Readout Frequency')

        #DC BIAS VARIABLES#########################################################################
        self.send_request('Qubit Flux Bias Voltage')

        #CAVITY DRIVE (READOUT) VARIABLES##########################################################
        RO_SB_freq = self.value('Readout SB Frequency')['GHz']       # readout sideband frequency
        RO_amp = self.value('Readout Amplitude')['DACUnits']         # amplitude of the sideband modulation
        RO_time = self.value('Readout Time')['ns']                   # length of the readout pulse
        
        #QUBIT DRIVE VARIABLES#####################################################################
        QB_SB_freq = self.value('Qubit SB Frequency')['GHz']         # qubit sideband frequency
        QB_amp = self.value('Qubit Amplitude')['DACUnits']           # amplitude of the sideband modulation
        QB_time = self.value('Qubit Time')['ns']                     # length of the qubit pulse
      
        #TIMING VARIABLES##########################################################################
        QBtoRO = self.value('Qubit Drive to Readout Delay')['ns']    # delay from the start of the qubit pulse to the start of the readout pulse
        ADC_wait_time = self.value('ADC Wait Time')['ns']            # delay from the start of the readout pulse to the start of the demodulation
        
        ###WAVEFORMS###############################################################################
        DAC_ZERO_PAD_LEN = self.boards.consts['DAC_ZERO_PAD_LEN']['ns']

        waveforms = {}
        if 'None' in self.boards.requested_waveforms:
            waveforms['None'] = np.hstack([pulse.DC(2 * DAC_ZERO_PAD_LEN + QB_time + QBtoRO + RO_time, 0)])
        
        if 'Readout I' in self.boards.requested_waveforms:
            waveforms['Readout I'] = np.hstack([pulse.DC(DAC_ZERO_PAD_LEN + QB_time + QBtoRO, 0),
                                                pulse.CosinePulse(RO_time, RO_SB_freq, RO_amp, 0.0, 0.0),
                                                pulse.DC(DAC_ZERO_PAD_LEN, 0)])

        if 'Readout Q' in self.boards.requested_waveforms:
            waveforms['Readout Q'] = np.hstack([pulse.DC(DAC_ZERO_PAD_LEN + QB_time + QBtoRO, 0),
                                                pulse.SinePulse(RO_time, RO_SB_freq, RO_amp, 0.0, 0.0),
                                                pulse.DC(DAC_ZERO_PAD_LEN, 0)])
 
        if 'Qubit I' in self.boards.requested_waveforms:            
            waveforms['Qubit I'] = np.hstack([pulse.DC(DAC_ZERO_PAD_LEN, 0),
                                              pulse.CosinePulse(QB_time, QB_SB_freq, QB_amp, 0.0, 0.0),
                                              pulse.DC(QBtoRO + RO_time + DAC_ZERO_PAD_LEN, 0)])

        if 'Qubit Q' in self.boards.requested_waveforms:        
            waveforms['Qubit Q'] = np.hstack([pulse.DC(DAC_ZERO_PAD_LEN, 0),
                                              pulse.SinePulse(QB_time, QB_SB_freq, QB_amp, 0.0, 0.0),
                                              pulse.DC(QBtoRO + RO_time + DAC_ZERO_PAD_LEN, 0)])
 
        dac_srams, sram_length, sram_delay = self.boards.process_waveforms(waveforms)

        if plot_waveforms:
            self._plot_waveforms([waveforms[wf] for wf in self.boards.requested_waveforms],
                    ['r', 'g', 'b', 'k'], self.boards.requested_waveforms)

        ###SET BOARDS PROPERLY#####################################################################
        demod_freq = -self.value('Readout SB Frequency')
        self.boards.set_adc_setting('DemodFreq', demod_freq, adc)
        # Waiting time before the demodulation start.
        self.boards.set_adc_setting('ADCDelay', (DAC_ZERO_PAD_LEN +
                ADC_wait_time + QB_time + QBtoRO) * units.ns, adc)

        mems = [seq.mem_simple(self.value('Init Time')['us'], sram_length, 0, sram_delay)
                for k, dac in enumerate(self.boards.dacs)]
        
        ###RUN#####################################################################################
        self.acknowledge_requests()
        self.send_request('Temperature')
        result = self.boards.load_and_run(dac_srams, mems, self.value('Reps'))
        
        ###DATA POST-PROCESSING####################################################################
        Is, Qs = result[0] 
        Is = np.array(Is)
        Qs = np.array(Qs)

        if self.boards.get_adc_setting('RunMode', adc) == 'demodulate':
            I = np.mean(Is)
            Q = np.mean(Qs)
            return {
                    'Single Shot Is': { 
                        'Value': Is * units.ADCUnits,
                        'Dependencies': ['Rep Iteration'],
                        'Preferences':  {'linestyle': 'b.'}},
                    'Single Shot Qs': { 
                        'Value': Qs * units.ADCUnits,
                        'Dependencies': ['Rep Iteration'],
                        'Preferences':  {'linestyle': 'g.'}},
                    'I': {
                        'Value': I * units.ADCUnits,
                        'Distribution': 'normal',
                        'Preferences':  {'linestyle': 'b-'}},
                    'Q': { 
                        'Value': Q * units.ADCUnits,
                        'Distribution': 'normal',
                        'Preferences':  {'linestyle': 'g-'}}, 
                    'I Std Dev': { 
                        'Value': np.std(Is) * units.ADCUnits},
                    'Q Std Dev': { 
                        'Value': np.std(Qs) * units.ADCUnits},
                    'ADC Amplitude': { 
                        'Value': np.sqrt(I**2 + Q**2) * units.ADCUnits,
                        'Preferences':  {'linestyle': 'r-'}},
                    'ADC Phase': { # numpy.arctan2(y, x) expects reversed arguments.
                        'Value': np.arctan2(Q, I) * units.rad,
                        'Preferences':  {'linestyle': 'k-'}},
                    'Rep Iteration': {
                        'Value': np.linspace(1, len(Is), len(Is)),
                        'Type': 'Independent'},
                    'Temperature': {
                        'Value': self.acknowledge_request('Temperature')}
                   }
        elif self.boards.get_adc_setting('RunMode', adc) == 'average':
            self.value('Reps', 1, output=False)
            time = np.linspace(0, 2 * (len(Is) - 1), len(Is))
            I, Q = data_processing.software_demod(time, demod_freq, Is, Qs)
            return {
                    'I': { 
                        'Value': Is * units.ADCUnits,
                        'Dependencies': ['ADC Time'],
                        'Preferences':  {'linestyle': 'b-'}},
                    'Q': { 
                        'Value': Qs * units.ADCUnits,
                        'Dependencies': ['ADC Time'],
                        'Preferences':  {'linestyle': 'g-'}},
                    'Software Demod I': { 
                        'Value': I * units.ADCUnits,
                        'Preferences':  {'linestyle': 'b.'}},
                    'Software Demod Q': { 
                        'Value': Q * units.ADCUnits,
                        'Preferences':  {'linestyle': 'g.'}}, 
                    'Software Demod ADC Amplitude': { 
                        'Value': np.sqrt(I**2 + Q**2) * units.ADCUnits,
                        'Preferences':  {'linestyle': 'r.'}},
                    'Software Demod ADC Phase': { 
                        'Value': np.arctan2(Q, I) * units.rad,
                        'Preferences':  {'linestyle': 'k.'}},
                    'ADC Time': {
                        'Value': time * units.ns,
                        'Type': 'Independent'},
                    'Temperature': {
                        'Value': self.acknowledge_request('Temperature')}
                   }

    def average_data(self, data):
        for key in data:
            if key in ['I', 'Q']:
                if 'Single Shot ' + key + 's' in data:
                    data[key]['Value'] = np.mean(data['Single Shot ' + key + 's']['Value'])
                    data[key + ' Std Dev']['Value'] = np.std(data['Single Shot ' + key + 's']['Value'])
                else:
                    data[key]['Value'] = np.mean(data[key]['Value'], axis=0)
                    data[key]['Distribution'] = 'normal'
                    data[key + ' Std Dev']['Value'] = np.std(data[key]['Value'], axis=0)
            elif key in ['Software Demod I', 'Software Demod Q']:
                data[key]['Value'] = np.mean(data[key]['Value'], axis=0)
                data[key]['Distribution'] = 'normal'
                data[key + ' Std Dev']['Value'] = np.std(data[key]['Value'], axis=0)
        
        for key in data:      
            if key == 'ADC Amplitude':
                data['ADC Amplitude']['Value'] = np.sqrt(data['I']['Value']**2 + data['Q']['Value']**2)
            elif key == 'ADC Phase':
                data['ADC Phase']['Value'] = np.arctan2(data['Q']['Value'], data['I']['Value'])
            
            elif key == 'Software Demod ADC Amplitude':
                data['Software Demod ADC Amplitude']['Value'] = np.sqrt(data['Software Demod I']**2 + 
                                                                        data['Software Demod Q']**2)
            elif key == 'Software Demod ADC Phase':
                data['Software Demod ADC Phase']['Value'] = np.arctan2(data['Software Demod Q'],
                                                                       data['Software Demod I']) 
        return data
        

class HEMTCavityJPM(HEMTExperiment):
    """
    Probe a resonator that is driven by a switching JPM with a HEMT.
    """
    def run_once(self, adc=None, plot_waveforms=False):
        #RF DRIVE (READOUT) VARIABLES##############################################################
        self.send_request('RF Attenuation')                             # RF attenuation
        self.send_request('RF Power')                                   # RF power
        if self.value('RF Frequency') is not None:
            if self.value('RF SB Frequency') is not None:               # RF frequency
                self.send_request('RF Frequency',
                        value=self.value('RF Frequency') + 
                              self.value('RF SB Frequency'))
            else:
                self.send_request('RF Frequency')

        #DC BIAS VARIABLES#########################################################################
        self.send_request('Qubit Flux Bias Voltage')

        #RF VARIABLES##############################################################################
        ADC_wait_time = self.value('ADC Wait Time')['ns']               # delay from the start of the fast pulse to the start of the demodulation
        
        #JPM VARIABLES#############################################################################
        JPM_FPT = self.value('Fast Pulse Time')['ns']                   # length of the DAC pulse
        JPM_FPA = self.value('Fast Pulse Amplitude')['DACUnits']        # amplitude of the DAC pulse
        JPM_FPW = self.value('Fast Pulse Width')['ns']                  # DAC pulse rise time 
        
        ###WAVEFORMS###############################################################################
        DAC_ZERO_PAD_LEN = self.boards.consts['DAC_ZERO_PAD_LEN']['ns']
        
        JPM_smoothed_FP = pulse.GaussPulse(JPM_FPT, JPM_FPW, JPM_FPA)
                
        waveforms = {}
        if 'JPM Fast Pulse' in self.boards.requested_waveforms:
            waveforms['JPM Fast Pulse'] = np.hstack([pulse.DC(DAC_ZERO_PAD_LEN, 0),
                                                     JPM_smoothed_FP,
                                                     pulse.DC(DAC_ZERO_PAD_LEN, 0)])

        if 'None' in self.boards.requested_waveforms:
            waveforms['None'] = np.hstack([pulse.DC(2 * DAC_ZERO_PAD_LEN + JPM_smoothed_FP.size, 0)])

        dac_srams, sram_length, sram_delay = self.boards.process_waveforms(waveforms)

        if plot_waveforms:
            self._plot_waveforms([waveforms[wf] for wf in self.boards.requested_waveforms],
                    ['r', 'g', 'b', 'k'], self.boards.requested_waveforms)

        ###SET BOARDS PROPERLY#####################################################################
        self.boards.set_adc_setting('ADCDelay', (DAC_ZERO_PAD_LEN +
                ADC_wait_time) * units.ns, adc)
        self.boards.set_adc_setting('DemodFreq', -self.value('RF SB Frequency'), adc)
        
        # Create a memory command list.
        # The format is described in Servers.Instruments.GHzBoards.command_sequences.
        mem_lists = self.boards.init_mem_lists()
        
        mem_lists[0].append({'Type': 'Bias', 'Channel': 1, 'Voltage': 0})
        mem_lists[0].append({'Type': 'Delay', 'Time': self.value('Init Time')['us']})
        mem_lists[0].append({'Type': 'Bias', 'Channel': 1,
                'Voltage': self.value('Bias Voltage')['V']})
        mem_lists[0].append({'Type': 'Delay', 'Time': self.value('Bias Time')['us']})
        mem_lists[0].append({'Type': 'SRAM', 'Start': 0, 'Length': sram_length, 'Delay': sram_delay})
        mem_lists[0].append({'Type': 'Timer', 'Time': self.value('Measure Time')['us']})
        mem_lists[0].append({'Type': 'Bias', 'Channel': 1, 'Voltage': 0})

        mem_lists[1].append({'Type': 'Delay', 'Time': self.value('Init Time')['us'] +
                                      self.value('Bias Time')['us']})
        mem_lists[1].append({'Type': 'SRAM', 'Start': 0, 'Length': sram_length, 'Delay': sram_delay})
        mem_lists[1].append({'Type': 'Timer', 'Time': self.value('Measure Time')['us']})

        mems = [seq.mem_from_list(mem_list) for mem_list in mem_lists]
        
        ###RUN#####################################################################################
        self.acknowledge_requests()
        self.send_request('Temperature')
        result = self.boards.load_and_run(dac_srams, mems, self.value('Reps'))

        ###DATA POST-PROCESSING####################################################################
        Is, Qs = result[0]
        Is = np.array(Is)
        Qs = np.array(Qs)

        if self.boards.get_adc_setting('RunMode', adc) == 'demodulate':
            I = np.mean(Is)
            Q = np.mean(Qs)
            return {
                    'Single Shot Is': { 
                        'Value': Is * units.ADCUnits,
                        'Dependencies': ['Rep Iteration'],
                        'Preferences':  {'linestyle': 'b.'}},
                    'Single Shot Qs': { 
                        'Value': Qs * units.ADCUnits,
                        'Dependencies': ['Rep Iteration'],
                        'Preferences':  {'linestyle': 'g.'}},
                    'I': {
                        'Value': I * units.ADCUnits,
                        'Distribution': 'normal',
                        'Preferences':  {'linestyle': 'b-'}},
                    'Q': { 
                        'Value': Q * units.ADCUnits,
                        'Distribution': 'normal',
                        'Preferences':  {'linestyle': 'g-'}}, 
                    'I Std Dev': { 
                        'Value': np.std(Is) * units.ADCUnits},
                    'Q Std Dev': { 
                        'Value': np.std(Qs) * units.ADCUnits},
                    'Mean ADC Amplitude': { 
                        'Value': np.mean(np.sqrt(Is**2 + Qs**2)) * units.ADCUnits,
                        'Distribution': 'normal',
                        'Preferences':  {'linestyle': 'r-'}},
                    'Mean ADC Amplitude Std Dev': { 
                        'Value': np.std(np.sqrt(Is**2 + Qs**2)) * units.ADCUnits},
                    'ADC Phases': { # numpy.arctan2(y, x) expects reversed arguments.
                        'Value': np.arctan2(Qs, Is) * units.rad,
                        'Dependencies': ['Rep Iteration'],
                        'Preferences':  {'linestyle': 'k-'}},
                    'Rep Iteration': {
                        'Value': np.linspace(1, len(Is), len(Is)),
                        'Type': 'Independent'},
                    'Temperature': {
                        'Value': self.acknowledge_request('Temperature')}
                   }
        elif self.boards.get_adc_setting('RunMode', adc) == 'average':
            self.value('Reps', 1, output=False)
            time = np.linspace(0, 2 * (len(Is) - 1), len(Is))
            I, Q = data_processing.software_demod(time, 0, Is, Qs)
            return {
                    'I': { 
                        'Value': Is * units.ADCUnits,
                        'Dependencies': ['ADC Time'],
                        'Preferences':  {'linestyle': 'b-'}},
                    'Q': { 
                        'Value': Qs * units.ADCUnits,
                        'Dependencies': ['ADC Time'],
                        'Preferences':  {'linestyle': 'g-'}},
                    'Software Demod I': { 
                        'Value': I * units.ADCUnits,
                        'Preferences':  {'linestyle': 'b.'}},
                    'Software Demod Q': { 
                        'Value': Q * units.ADCUnits,
                        'Preferences':  {'linestyle': 'g.'}}, 
                    'Software Demod ADC Amplitude': { 
                        'Value': np.sqrt(I**2 + Q**2) * units.ADCUnits,
                        'Preferences':  {'linestyle': 'r.'}},
                    'Software Demod ADC Phase': { 
                        'Value': np.arctan2(Q, I) * units.rad,
                        'Preferences':  {'linestyle': 'k.'}},
                    'ADC Time': {
                        'Value': time * units.ns,
                        'Type': 'Independent'},
                    'Temperature': {
                        'Value': self.acknowledge_request('Temperature')}
                   }

    def average_data(self, data):
        raise NotImplementedError("Proper averaging of multiple runs " +
            "is not implemented for this specific experiment to avoid" +
            " any misinterpretation of the results.")