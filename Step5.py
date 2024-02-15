"""
Author: Ethan Avila, Carter Young

Date: ___

Description:
This file is supposed to implement the 5th step of our CS429 project where
we implement an L1 Instruction and Data cache and an L2 shared cache
We aim to simulate this by creating 3 instances of the writeback cache class Carter made
in the previous steps
Additionally, we'll need to calculate, in cycles...
AMAT = 1 + L1Miss * (10 + L2Miss * 100)

We'll collect info on set associativities for 1, 4, 16, 64, 128 for all 3 trace files
"""