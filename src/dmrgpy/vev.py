# compute vacuum expectation values using multioperators

from . import multioperator

import numpy as np

def vev(self,MO):
    """
    Compute a VEV using multioperators
    """
    MO = multioperator.obj2MO(MO,name="vev_multioperator")
    if MO.name!="vev_multioperator": raise
    self.get_gs()
    taskd = MO.get_dict() # get the dictionary
    taskd["vev"] = "true" # do a VEV
    self.task = taskd # assign the task
    self.write_task() # write the tasks in a file
    self.write_hamiltonian() # write the Hamiltonian to a file
    self.run() # perform the calculation
    m = self.execute(lambda: np.genfromtxt("VEV.OUT"))
    return m[0]+1j*m[1] # return result













