from __future__ import print_function
import numpy as np

def get_moments_dmrg(self,n=1000):
  """Get the moments with DMRG"""
  self.setup_task("dos",task={"nkpm":str(n)})
  self.write_hamiltonian() # write the Hamiltonian to a file
  self.run() # perform the calculation
  return self.execute(lambda: np.genfromtxt("KPM_MOMENTS.OUT").transpose()[0])









def get_moments_dynamical_correlator_dmrg(self,i=0,j=0,
        name="XX",delta=1e-1):
  """Get the moments with DMRG"""
  try: # select the right operators, be consistent with mpscpp.x
      from . import operatornames
      namei,namej = operatornames.recognize(name)
      namei = operatornames.hermitian(namei) # get the Hermitian operator
  except:
      print("Dynamical correlator not recognised")
      raise
  task= {       "kpmmaxm":str(self.kpmmaxm),
                "site_i_kpm":str(i),"site_j_kpm":str(j),
                "kpm_scale":str(self.kpm_scale),
                "kpm_n_scale":str(self.kpm_n_scale),
                "kpm_delta":str(delta),
                "kpm_cutoff":str(self.kpmcutoff),
                "kpm_operator_i":namei,"kpm_operator_j":namej}
  self.setup_task("dynamical_correlator",task=task) 
  self.write_hamiltonian() # write the Hamiltonian to a file
  self.run() # perform the calculation
  m = self.execute(lambda: np.genfromtxt("KPM_MOMENTS.OUT").transpose())
#  return m[1]
  return m[0]+1j*m[1]





from . import pychain
from .algebra.kpm import generate_profile

#def get_dos(self,n=1000,mode="DMRG",ntries=10):
#  if mode=="DMRG": 
##  if False: 
#    mus = [get_moments_dmrg(self,n=n) for i in range(ntries)] # get the moments
#    scale = np.genfromtxt("KPM_SCALE.OUT") # scale of the dos
#  else:
#    m  = self.get_full_hamiltonian()
#    mus = [pychain.kpm.random_trace(m/15.0,ntries=1,n=1000)
#                 for i in range(ntries)]
#    scale = 1./15.
#  mus = np.mean(np.array(mus),axis=0)
#  mus = mus[0:100]
#  xs = 0.99*np.linspace(-1.0,1.0,2000,endpoint=True) # energies
#  ys = generate_profile(mus,xs,use_fortran=False).real # generate the DOS
#  xs /= scale
#  ys *= scale
#  np.savetxt("DOS.OUT",np.matrix([xs,ys]).T)
#  return (xs,ys)


def restrict_interval(x,y,window):
  """Restrict the result to a certain energy window"""
  if window is None: return (x,y)
  i = np.argwhere(x<window[0]) # last one
  j = np.argwhere(x>window[1]) # last one
  if len(i)==0: i = 0
  else: i = i[0][-1]
  if len(j)==0: j = len(x)
  else: j = j[0][0]
  return x[i:j].real,y[i:j]







def get_dynamical_correlator(self,n=1000,mode="DMRG",i=0,j=0,
             window=[-1,10],name="XX",delta=2e-2,es=None,
             **kwargs):
  """
  Compute a dynamical correlator using the KPM-DMRG method
  """
  self.to_folder() # go to temporal folder
  if mode=="DMRG": 
# get the moments
    mus = get_moments_dynamical_correlator_dmrg(self,i=i,j=j,
            name=name,delta=delta,**kwargs) 
    # scale of the dos
    kpmscales = self.execute(lambda: np.genfromtxt("KPM_SCALE.OUT"))
    emin = kpmscales[0] # minimum energy
    emax = kpmscales[1] # maximum energy
    scale = kpmscales[2] # scaling of the energies
    # ground state energy
    e0 = self.execute(lambda: np.genfromtxt("GS_ENERGY.OUT"))
    self.e0 = e0 # add this quantity
    n = self.execute(lambda: np.genfromtxt("KPM_NUM_POLYNOMIALS.OUT"))
    xs = 0.99*np.linspace(-1.0,1.0,n*10,endpoint=True) # energies
    ys = generate_profile(mus,xs,use_fortran=False,kernel="lorentz") # generate the DOS
    xs /= scale # scale back the energies
    ys *= scale # renormalize the y positions
#    e0 = self.gs_energy() # ground state energy
    # now retain only an energy window
  else: 
    h = self.get_full_hamiltonian()
    sc = self.get_pychain()
    from .pychain import correlator as pychain_correlator
    if delta is None: delta = float(self.ns)/n*1.5
    if mode=="fullKPM":
      (xs,ys) = pychain_correlator.dynamical_correlator_kpm(sc,h,n=n,i=i,j=j,
                         namei=name[0],namej=name[1])
    elif mode=="ED":
      (xs,ys) = pychain_correlator.dynamical_correlator(sc,h,delta=delta,i=i,
                        j=j,namei=name[0],namej=name[1])
    else: raise
  self.to_origin() # go to origin folder
  if es is None:
    (xs,ys) = restrict_interval(xs,ys,window) # restrict the interval
  else:
    (xs,ys) = restrict_interval(xs,ys,[min(es),max(es)]) # restrict the interval
  from scipy.interpolate import interp1d
  fr = interp1d(xs, ys.real,fill_value=0.0,bounds_error=False)
  fi = interp1d(xs, ys.imag,fill_value=0.0,bounds_error=False)
  if es is None: 
      ne = int(100*(window[1] - window[0])/delta) # number of energies
      xs = np.linspace(window[0],window[1],ne)
  else: xs = np.array(es).copy() # copy input array
  ys = fr(xs) + 1j*fi(xs) # evaluate the interpolator
  np.savetxt("DYNAMICAL_CORRELATOR.OUT",np.matrix([xs.real,ys.real,ys.imag]).T)
  return (xs,ys)



