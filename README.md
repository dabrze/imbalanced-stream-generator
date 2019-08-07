# Imbalanced Data Stream Generator

Reproducible code and experimental scripts accompanying the paper "The impact of data difficulty factors on classification of imbalanced and concept drifting data streams".

## Contents

The repository contains generator source code, experimental scripts including data stream generation scripts, and detailed results of the classification experiments discussed in "The impact of data difficulty factors on classification of imbalanced and concept drifting data streams". The repository is divided into the following folders:

- the main folder contains a (bash) `makefile`, list of python modules used to process experimental results (`python.requirements`), and a script for generating various streams discussed in the accompanying research paper
- `src` contains Java source code compatible with MOA; to use the data stream generator and classifiers attach this code to your project or include it while running moa.jar
- `scripts` contains python source code use to post-process experimental results
- `research/evaluations` contains cached experiment results

## Contact

If you have trouble reproducing the experiments or have any comments/suggestions, feel free to write at dariusz.brzezinski (at) cs.put.poznan.pl
