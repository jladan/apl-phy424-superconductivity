# Superconductivity Lab - Condensed Matter Physics

*(PHY424 - University of Toronto Advanced Physics Labs)*
[official repository](https://gitlab.physics.utoronto.ca/advanced-lab/experiments/cmp-superconductivity)

The purpose of the CMP superconductivity lab is to measure the
Temperature-Resistance curve of a high-temperature superconductor sample. The
sample is placed inside a Liquid-Nitrogen cooled cryostat, and the resistance is
measured using a digital lock-in amplifier.

The files here manage the data acquisition needed in the CMP Superconductivity
experiment. The most important files are

- `src/lockin_7270.py`:
    A class to manage serial communications with the lockin-amplifier.
- `src/sim922.py`:
    A class to manage serial communications with the SIM922 thermodiode monitor
- `src/daq_example.py`:
    An example how to use the two classes to measure temperatures and voltages.

While `daq_example.py` can technically be used to perform the experiment, there
are problems with it, which make it very easy to loose your measurements. We
recommend writing your own script, which periodically saves the measurements,
and does not overwrite existing files.

Please read through the source code and try to understand how it works. This is
a great skill to practice. 


## Requirements 

The following python libraries must be installed on your computer. They have
already been installed on the lab computer.

- numpy
- pyusb
- pyvisa

In addition to the python modules, additional drivers must be installed for the
lockin amplifier. They can either be obtained from the manufacturer's website,
or created using libusb.

To find a list of modules that are available for your python distribution open a
python console or jupyter-notebook file and run:
`help("modules")`
This command will output a list of python modules you have available. If one of
the modules above is not in the list, install it. A quick google search will
show you how. 

