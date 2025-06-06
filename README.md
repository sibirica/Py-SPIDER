<img src="https://github.com/sibirica/PySPIDER/blob/main/PySPIDER_logo.png" width="144" align="right">

# PySPIDER: a Python implementation of the SPIDER framework for data-driven equivariant modeling of continuous and discrete systems

## Introduction
[SPIDER](https://github.com/sibirica/PySPIDER/blob/main/DG_Dissertation.pdf) (Sparse Physics-Informed Discovery of Empirical Relations) is a framework for using sparse regression to perform data-driven inference of symmetry-equivariant models of spatiotemporally extended physical systems. These take the form of sets of tensor-valued
- partial differential equations describing continuous systems or
- partial integro-differential equations describing systems of discrete interacting particles or agents.

PySPIDER is a Python implementation that employs techniques from programming language theory to automate library generation, evaluation, and symbolic deduction, allowing the user to quickly obtain a full physically meaningful and quantitatively accurate description of the dataset. 

Please check out [my dissertation](https://github.com/sibirica/PySPIDER/blob/main/DG_Dissertation.pdf) to learn more!

## Getting started
The "tutorials" directory contains demonstrations of how to use PySPIDER to learn models for both [continuous](https://github.com/sibirica/PySPIDER/blob/main/tutorials/01_Continuous.ipynb) and [discrete](https://github.com/sibirica/PySPIDER/blob/main/tutorials/02_Discrete.ipynb) systems. 

We're working on making PySPIDER into a PyPI package (PySPIDER-SR) so you can automatically install it and all of the dependencies with pip, but for now, please clone this GitHub.

## Dependencies: 
Python version: 3.12+

### Libraries:

z3-solver - Z3 satisfiability modulo theory (SMT) solver for library generation \
findiff - for finite differencing \
numba-kdtree - for fast coarse-graining of discrete data \
ffmpeg (optional) - for creating videos of data \
h5py (optional) - to read HDF5 or MATLAB v7.3 data files \
\
note: make sure that the latest version of scipy is installed (>=1.6)

## Organization
The package is organized into three groups of modules:
- *commons* contains modules corresponding to general concepts that are used for both continuous and discrete problems.
- *continuous* contains modules specific to continuous systems.
- *discrete* contains modules specific to systems of discrete interacting particles or agents.

## Using PySPIDER for your project
Please feel free to contact us if you are interested in using PySPIDER for a project. We are happy to help you set it up for your problem of interest.

If you use PySPIDER, please cite the following [paper](https://www.cambridge.org/core/journals/journal-of-fluid-mechanics/article/learning-fluid-physics-from-highly-turbulent-data-using-sparse-physicsinformed-discovery-of-empirical-relations-spider/FB279BC082B965AFCCD768FD50ACEB08) as well as (check back later):

```
@article{gurevich_learning_2024,  
	author = {Gurevich, Daniel R. and Golden, Matthew R. and Reinbold, Patrick A.K. and Grigoriev, Roman O.},  
	title = {Learning fluid physics from highly turbulent data using sparse physics-informed discovery of empirical relations ({SPIDER})},  
 	journal = {Journal of Fluid Mechanics},  
	volume = {996},  
	year = {2024},  
	pages = {A25}  
}
```

## Contributing to SPIDER
We have plenty of ideas for improving SPIDER, ranging from relatively simple coding projects to substantial conceptual generalizations, but not enough manpower to implement all of them currently. Several of these would substantially expand SPIDER's range of scientific applications and lead to some nice papers. If you might be interested in contributing to the project, we would be glad to chat.

## Thank you
Thank you for checking out PySPIDER! Please let us know if you encounter any issues using this code or have comments or questions.

Daniel Gurevich\
dgurevich@princeton.edu

