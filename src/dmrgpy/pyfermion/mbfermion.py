from . import states
from ..pychain.spectrum import ground_state
import numpy as np
from scipy.sparse import csc_matrix,identity
import scipy.sparse.linalg as slg


nmax = 15 # maximum number of levels

def get_spinless_hamiltonian(m0,hubbard=None):
    """Compute ground state energy"""
    MBf = MBFermion(len(m0)) # create many body fermion object
    MBf.add_hopping(m0)
#    h = MBf.one2many(m0) # get the single body matrix
#    h = states.one2many(m0) # single to many body Hamiltonian
    if hubbard is not None: # if hubbard given
        MBf.add_hubbard(hubbard)
    return MBf.h

def gs_energy(m0,spinless=True,hubbard=None):
    if spinless:
      h = get_spinless_hamiltonian(m0,hubbard=hubbard)
    else: raise
    return ground_state(h)[0] # return GS energy



class MBFermion():
    """
    Class for a many body fermionic Hamiltonian
    """
    def __init__(self,n):
        """
        Initialize the object
        """
        self.n = n # number of different levels
        if n>nmax: raise # too big system
        self.c_dict = dict() # dictionary with the annhilation operators
        self.basis = states.generate_basis(self.n,lambda x: True) # basis
        self.nMB = len(self.basis) # dimension of many body hamiltonian
        self.basis_dict = states.get_dictionary(self.basis) # dictionary
        self.h = csc_matrix(([],([],[])),shape=(self.nMB,self.nMB)) # Hamil
    def get_c(self,i):
        """
        Return the annhilation operator for site i in the many body basis
        """
        if i in self.c_dict: # if already computed
            return self.c_dict[i] # return matrix
        else: # not computed yet
            m = states.destroy(self.basis,self.basis_dict,self.n,i)
            self.c_dict[i] = m # store matrix
            return m
    def clean(self):
        """
        Initialize the Hamiltonian
        """
        self.h = csc_matrix(([],([],[])),shape=(self.nMB,self.nMB))
    def add_hopping(self,m):
        """
        Add a single particle term to the Hamiltonian
        """
        self.h = self.h + self.one2many(m) # add contribution
    def add_hubbard(self,hubbard):
        """
        Add a Hubbard term to the hamiltonian
        """
        if hubbard is None: return
        self.h = self.h + self.hubbard(hubbard) # add Hubbard term
    def get_gs(self):
        """
        Return the ground state
        """
        e,wf = ground_state(self.h) # return GS
        self.energy = e # store energy
        self.wf0 = wf # store wavefunction
        return self.energy
    def get_cd(self,i):
        """
        Return the creation operator for site i in the many body basis
        """
        return self.get_c(i).H # return the dagger
    def get_density(self,i):
        """
        Return the density operator
        """
        return self.get_cd(i)@self.get_c(i)
    def one2many(self,m0):
        """
        Convert a single body Hamiltonian into a many body one
        """
        m = csc_matrix(([],([],[])),shape=(self.nMB,self.nMB)) # initialize
        for i in range(len(m0)):
          for j in range(len(m0)):
              if abs(m0[i,j])>1e-7:
                m = m + self.get_cd(i)*self.get_c(j)*m0[i,j] # add contribution
        return m # return many body hamiltonian
    def hubbard(self,m0):
        """
        Return the many body matrix for certain hubbard couplings
        """
        m = csc_matrix(([],([],[])),shape=(self.nMB,self.nMB)) # initialize
        for i in range(len(m0)):
          for j in range(len(m0)):
              if abs(m0[i,j])>1e-7:
                ci = self.get_c(i)
                ni = ci.H*ci
                cj = self.get_c(j)
                nj = cj.H*cj
                m = m + ni*nj*m0[i,j] # add contribution
        return m # return many body hamiltonian
    def correlator(self,pairs,wf):
        """
        Compute a set of correlators for a wavefunction
        """
        out = [] # output list
        for p in pairs: # loop over pairs
            m = self.get_cd(p[0])*self.get_c(p[1]) # get matrix
            raise # not finished yet
    def get_operator(self,name,i):
        """
        Return a certain operator
        """
        if name=="density": return self.get_density(i)
        elif name=="C": return self.get_c(i)
        elif name=="Cdag": return self.get_cd(i)
        else: raise
    def get_dynamical_correlator(self,i=0,j=0,
            es=np.linspace(-1.0,10,500),delta=1e-1,
            name="densitydensity"):
        """
        Compute the dynamical correlator
        """
        from ..algebra import kpm
        from .. import operatornames
        self.get_gs() # compute ground state
        namei,namej = operatornames.recognize(None,name) # get the operator
        namei = operatornames.hermitian(namei) # get the dagger
        A = self.get_operator(namei,i)
        B = self.get_operator(namej,j)
#        A = self.get_cd(i) # first operator
#        B = self.get_cd(j) # second operator
        vi = A@self.wf0 # first wavefunction
        vj = B@self.wf0 # second wavefunction
        m = -identity(self.h.shape[0])*self.energy+self.h # matrix to use
        emax = slg.eigsh(self.h,k=1,ncv=20,which="LA")[0] # upper energy
        scale = np.max([np.abs(self.energy),np.abs(emax)])*3.0
        n = int(scale/delta) # number of polynomials
        (xs,ys) = kpm.dm_vivj_energy(m,vi,vj,scale=scale,
                                    npol=n*4,ne=n*10,x=es)
        return xs,np.conjugate(ys)/scale*np.pi*2 # return correlator










