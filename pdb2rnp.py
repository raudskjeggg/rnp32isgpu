#!/usr/bin/python2

from Bio.PDB import *
from numpy import *
import re
import sys

# if len(sys.argv)<4:
# 	print "Usage: initialstructure.pdb finalstructure.pdb inputfile.sopscgpu"
# 	exit(1)
# outputname=sys.argv[3]
# PDBname2=sys.argv[2]
# PDBname=sys.argv[1]

if len(sys.argv)<2:
	print "Usage: structure.pdb inputfile.sopscgpu"
	exit(1)
outputname=sys.argv[2]
PDBname=sys.argv[1]

print "PDB 1 ",PDBname
#print "PDB 2 ",PDBname2
print "SOP-SC GPU input file ", outputname

#Protein residue names
resnames=["GLY", "ALA", "VAL", "LEU", "ILE", "MET", "PHE", "PRO", "SER", "THR", "ASN", "GLN", "TYR", "TRP", "ASP", "GLU", "HSE", "HSD", "HIS", "LYS", "ARG", "CYS"]

#Backbone atoms
BBA=["CA","N","C","O","HA","HN","1H","2H","3H","H","2HA","HA3","HT1","HT2","HT3","OT1","OT2","OXT"]


#RNA residue names
rnanames=["A","U","G","C"]
#PHA=["OP1","OP2","P","OP3","O5\'"]
SUA=["C1\'","C2\'","C3\'","C4\'","C5\'","O4\'","H1\'","H2\'","H3\'","H4\'","H5\'","H5\'\'","O2\'","HO2\'"]
BAA=["N1","C2","N3","C4","C5","C6","N2","N6","N7","C8","N9","N4","O4","O2","H1","H2","H21","H22","H3","H41","H42","H5","H6","H61","H62","H8"]



charged=["GLU","ASP","ARG","LYS","HIS"]
q=dict()
qlist=[-1,-1,-1,1,1] #respective charges in list charged
for i,res in enumerate(charged): 
	q[res]=qlist[i]

#dielectricepsilon=10.
#elstatprefactor=(4.8*4.8*6.02/4184.*1e+2)/dielectricepsilon #kcal/mol
 
#SOP-SC parameters. el is actually defined in the simulation code right now
ebb=0.55
ess=0.3
ebs=0.4

erna=0.7
eCG=2.5
eAU=2.
#el=1.
GoCut=8.
GoCutsq=GoCut**2


#Get CA and sidechain-center-of-mass positions (to lists cas and cbs) from the PDB structure. Get native contant and salt bridges lists
def pdb2rnp(structure,cas,casv,cbs,cbsv,phs,sus,bas,phsv,susv,basv,terres,rterres,seq,rseq,ncs,sbs):
	# for model in structure:
	for chain in structure[0]:
		rnum=chain.get_list()[0].get_id()[1]
		if chain.get_list()[0].get_resname().strip() in resnames:
			for residue in chain:
				if not residue.get_resname().strip() in resnames:
					print "Warning: non-AA ",residue.get_resname().strip()," in chain ",chain
					break;
				if residue.get_id()[1]-rnum>1:
					print "Warning: break in ", chain, " at ", residue, residue.get_id()[1]-rnum-1," residues missing"
					terres.append(len(cas)-1)
				rnum=residue.get_id()[1]
				seq.append(residue.get_resname())
				ca=residue['CA']
				#cas.append(list(ca.get_vector()))
				cas.append(ca.get_coord())
				casv.append(ca.get_vector())
				#cm=Vector(0,0,0)
				m=0
				cm=zeros(3)
				for atom in residue:
					if not atom.get_name() in BBA:
						cm+=atom.get_coord()*atom.mass
						#cm+=atom.get_vector().left_multiply(atom.mass)
						m+=atom.mass
					if (atom.get_name()=='CB') or (atom.get_name()=='HA1'):
						cb=atom.get_coord()
				cm/=m
				#cbg=cm
				cbg=cm
				#print cb,cm
				#cbs.append(list(cbg))
				cbs.append(cbg)
				cbsv.append(Vector(cbg))
			terres.append(len(cas)-1);  #Terminal residues
		
		if chain.get_list()[0].get_resname().strip() in rnanames:
			for residue in chain:
				if not residue.get_resname().strip() in rnanames:
					print "Warning: non-nucleotide ",residue.get_resname().strip()," in chain ", chain
					break;
				if residue.get_id()[1]-rnum>1:
					print "Warning: break in ", chain, " at ", residue, residue.get_id()[1]-rnum-1," residues missing"
					rterres.append(len(phs)-1)
				rnum=residue.get_id()[1]
				rseq.append(residue.get_resname().strip())
				p=residue['P']
				phs.append(p.get_coord());phsv.append(p.get_vector())
				sm=0;bm=0;
				scm=zeros(3);bcm=zeros(3)
				for atom in residue:
					if atom.get_name() in SUA:
						scm+=atom.get_coord()*atom.mass
						sm+=atom.mass
					if atom.get_name() in BAA:
						bcm+=atom.get_coord()*atom.mass
						bm+=atom.mass
				bcm/=bm;scm/=sm;
				sus.append(scm);susv.append(Vector(scm))
				bas.append(bcm);basv.append(Vector(bcm))
			rterres.append(len(phs)-1);  #Terminal residues
		
		Naa=len(cas) #Number of protein residues
		Nnuc=len(phs) #Number of rna residues
		
#Native contacts and salt-bridges
	for i in range(Naa):
	        print "Amino acid %d/%d\r" % (i,Naa)
		for j in range(i,Naa):
			if (j-i)>2:
				if ((casv[i]-casv[j]).normsq()<GoCutsq):
					ncs.append([i,j,(casv[i]-casv[j]).norm(),ebb])
				if ((cbsv[i]-cbsv[j]).normsq()<GoCutsq):
					ncs.append([i+Naa,j+Naa,(cbsv[i]-cbsv[j]).norm(),ess*fabs(BT[seq[i]][seq[j]]-.7)])
				if ((casv[i]-cbsv[j]).normsq()<GoCutsq):
					ncs.append([i,j+Naa,(casv[i]-cbsv[j]).norm(),ebs])
				if ((cbsv[i]-casv[j]).normsq()<GoCutsq):
					ncs.append([i+Naa,j,(cbsv[i]-casv[j]).norm(),ebs])
				if q.has_key(seq[i]) and q.has_key(seq[j]):
					sbs.append([i+Naa,j+Naa,q[seq[i]]*q[seq[j]]])
					
#RNA native contacts
	for i in range(Nnuc):
	        print "Nucleotide %d/%d\r" % (i,Nnuc)
		for j in range(i,Nnuc):
			if (j-i)>2:
				if ((phsv[i]-phsv[j]).normsq()<GoCutsq):
					ncs.append([2*Naa+i,2*Naa+j,(phsv[i]-phsv[j]).norm(),erna])
				if ((susv[i]-susv[j]).normsq()<GoCutsq):
					ncs.append([2*Naa+i+Nnuc,2*Naa+j+Nnuc,(susv[i]-susv[j]).norm(),erna])
				if ((basv[i]-basv[j]).normsq()<GoCutsq):
					if (rseq[i]=="A" and rseq[j]=="U") or (rseq[i]=="U" and rseq[j]=="A"):
						ncs.append([2*Naa+i+2*Nnuc,2*Naa+j+2*Nnuc,(basv[i]-basv[j]).norm(),eAU])
					elif (rseq[i]=="C" and rseq[j]=="G") or (rseq[i]=="G" and rseq[j]=="C"):
						ncs.append([2*Naa+i+2*Nnuc,2*Naa+j+2*Nnuc,(basv[i]-basv[j]).norm(),eCG])
					else:
						ncs.append([2*Naa+i+2*Nnuc,2*Naa+j+2*Nnuc,(basv[i]-basv[j]).norm(),erna])
					
				if ((phsv[i]-susv[j]).normsq()<GoCutsq):
					ncs.append([2*Naa+i,2*Naa+j+Nnuc,(phsv[i]-susv[j]).norm(),erna])
				if ((susv[i]-phsv[j]).normsq()<GoCutsq):
					ncs.append([2*Naa+i+Nnuc,2*Naa+j,(susv[i]-phsv[j]).norm(),erna])
					
				if ((phsv[i]-basv[j]).normsq()<GoCutsq):
					ncs.append([2*Naa+i,2*Naa+j+2*Nnuc,(phsv[i]-basv[j]).norm(),erna])
				if ((basv[i]-phsv[j]).normsq()<GoCutsq):
					ncs.append([2*Naa+i+2*Nnuc,2*Naa+j,(basv[i]-phsv[j]).norm(),erna])
					
				if ((basv[i]-susv[j]).normsq()<GoCutsq):
					ncs.append([2*Naa+i+2*Nnuc,2*Naa+j+Nnuc,(basv[i]-susv[j]).norm(),erna])
				if ((susv[i]-basv[j]).normsq()<GoCutsq):
					ncs.append([2*Naa+i+Nnuc,2*Naa+j+2*Nnuc,(susv[i]-basv[j]).norm(),erna])
					
#RNA to protein native
		for j in range(Naa):
			if ((phsv[i]-casv[j]).normsq()<GoCutsq):
				ncs.append([2*Naa+i,j,(phsv[i]-casv[j]).norm(),erna])
			if ((susv[i]-casv[j]).normsq()<GoCutsq):
				ncs.append([2*Naa+i+Nnuc,j,(susv[i]-casv[j]).norm(),erna])
			if ((basv[i]-casv[j]).normsq()<GoCutsq):
				ncs.append([2*Naa+i+2*Nnuc,j,(basv[i]-casv[j]).norm(),erna])
			if ((phsv[i]-cbsv[j]).normsq()<GoCutsq):
				ncs.append([2*Naa+i,j+Naa,(phsv[i]-cbsv[j]).norm(),erna])
			if ((susv[i]-cbsv[j]).normsq()<GoCutsq):
				ncs.append([2*Naa+i+Nnuc,j+Naa,(susv[i]-cbsv[j]).norm(),erna])
			if ((basv[i]-cbsv[j]).normsq()<GoCutsq):
				ncs.append([2*Naa+i+2*Nnuc,j+Naa,(basv[i]-cbsv[j]).norm(),erna])
			
			
	return 1




# Read the Betancourt-Thirumalai matrix (see Betancourt M. R. & Thirumalai, D. (1999). Protein Sci. 8(2),361-369. doi:10.1110/ps.8.2.361)
BT=dict()
f=open('tb.dat')
aas=re.split(' ',f.readline().strip())[1:]
for i in range(len(aas)):
	if not BT.has_key(aas[i]):
		BT[aas[i]]=dict();
	l=re.split(' ',f.readline().strip())[1:]
	for j in range(i,len(aas)):
		BT[aas[i]][aas[j]]=double(l[j])
		if not BT.has_key(aas[j]):
			BT[aas[j]]=dict()
		BT[aas[j]][aas[i]]=double(l[j])
f.close

#Read the van der Waals diameters of the side chains
sbb=3.8
sss=dict()
f=open('aavdw.dat')
for l in f:
	s=re.split(' ',l)
	sss[s[0]]=2.*double(s[1])
print sss

sphs=4.2
ssug=4.4
sbas=3.8
	

parser=PDBParser()

#Get CAs, CBs, native contacts and salt bridges for initial structure
structure=parser.get_structure('Starting',PDBname)
cas=[];casv=[];cbs=[];cbsv=[];phs=[];phsv=[];sus=[];susv=[];bas=[];basv=[];terres=[];rterres=[];seq=[];rseq=[];ncs=[];sbs=[]
pdb2rnp(structure,cas,casv,cbs,cbsv,phs,sus,bas,phsv,susv,basv,terres,rterres,seq,rseq,ncs,sbs);

# #Get CAs, CBs, native contacts and salt bridges for final structure
# structure=parser.get_structure('Final',PDBname2)
# cas2=[];casv2=[];cbs2=[];cbsv2=[];terres2=[];seq2=[];ncs2=[];sbs2=[]
# pdb2sop(structure,cas2,casv2,cbs2,cbsv2,terres2,seq2,ncs2,sbs2)	

print "Native Contacts in starting structure: ", len(ncs)
#print "Native Contacts in final structure: ", len(ncs2)
print "Salt bridges: ", len(sbs)

Naa=len(cas); #Number of aa residues
Nnuc=len(phs); #Number of nucleic acid residues
Nch=len(terres); #Number of protein chains
Nchr=len(rterres); #Number of RNA chains
Nb=2*Naa-Nch+3*Nnuc-Nchr; #Number of bonds in SOP-SC. Each residue has two bonds, except for Nch terminal residues
#Nb=Naa-Nch; #Number of bonds in SOP. Each residue has a bond, except for Nch terminal residues	



f=open('start.xyz','w')
f.write("%d\nAtoms\n" % (2*Naa+3*Nnuc))
for i in range(Nnuc):
	f.write("P %f %f %f\n" % (phs[i][0],phs[i][1],phs[i][2]))
	f.write("S %f %f %f\n" % (sus[i][0],sus[i][1],sus[i][2]))
	f.write("B %f %f %f\n" % (bas[i][0],bas[i][1],bas[i][2]))
for i in range(Naa):
	f.write("CA %f %f %f\n" % (cas[i][0],cas[i][1],cas[i][2]))
	f.write("CB %f %f %f\n" % (cbs[i][0],cbs[i][1],cbs[i][2]))
f.close

#Output everything to sopsc-gpu input file
f=open(outputname,'w')
f.write("NumSteps 3e+7\n")
f.write("Timestep(h) 0.05\n")
f.write("Friction(zeta) 50.\n")
f.write("Temperature 0.59\n")
f.write("NeighborListUpdateFrequency 10\n")
f.write("OutputFrequency 1000\n")
f.write("TrajectoryWriteFrequency 10000\n")
f.write("Trajectories 1\n")
f.write("RandomSeed 1234\n")
f.write("KernelBlockSize 512\n")

f.write("ProteinResidues\n")
f.write("%d\n" % Naa) #Number of amino acid residues
f.write("ProteinChains\n")
f.write("%d\n" % Nch)  #Number of protein chains
f.write("RNAResidues\n")
f.write("%d\n" % Nnuc) #Number of nucleic acid residues
f.write("RNAChains\n")
f.write("%d\n" % Nchr)  #Number of RNA chains
f.write("ChainsStart@\n")
#Chain starts
for ter in terres[:-1]:
	f.write("%d\n" % (ter+1))
for ter in rterres[:-1]:
	f.write("%d\n" % (ter+1))

f.write("Bonds\n")
f.write("%d\n" % Nb)  #Number of bonds

#Bonds
for i in range(Naa):
	f.write("%d %d %f\n" % (i,i+Naa,(casv[i]-cbsv[i]).norm()))
	if not i in terres:
		f.write("%d %d %f\n" % (i,i+1,(casv[i]-casv[i+1]).norm()))
		
for i in range(Nnuc):
	f.write("%d %d %f\n" % (2*Naa+i,2*Naa+i+Nnuc,(phsv[i]-susv[i]).norm()))
	f.write("%d %d %f\n" % (2*Naa+i+Nnuc,2*Naa+i+2*Nnuc,(susv[i]-basv[i]).norm()))
	if (phsv[i]-susv[i]).norm()>10:
		print i, susv[i], phsv[i]
	if (susv[i]-basv[i]).norm()>10:
		print i, susv[i], basv[i]
	if not i in rterres:
		f.write("%d %d %f\n" % (2*Naa+i+Nnuc,2*Naa+i+1,(susv[i]-phsv[i+1]).norm()))
		if (susv[i]-phsv[i+1]).norm()>10:
			print "Si->Pi+1",i, susv[i], phsv[i+1]

#Native contacts of starting structure
f.write("%d\n" % len(ncs))
for nc in ncs:
	f.write("%d %d %f %f\n" % (nc[0],nc[1],nc[2],nc[3]))

# #Native contacts of final structure
# f.write("%d\n" % len(ncs2))
# for nc in ncs2:
# 	f.write("%d %d %f %f\n" % (nc[0],nc[1],nc[2],nc[3]))

#Sigmas for soft sphere repulsion				
for aa in seq:
	f.write('%f\n' % sbb)
for aa in seq:
	f.write('%f\n' % sss[aa])
for i in range(Nnuc):
	f.write('%f\n' % sphs)
	f.write('%f\n' % ssug)
	f.write('%f\n' % sbas)

# #Exclusions from soft shpere interactions (additional to bonded beads: ss of neighboring residues, bs to ss of neighboring residues)
# f.write("%d\n" % (2*(Naa-0*Nch)))
# for i in range(Naa):
# 	#f.write("%d %d\n" % (i,i+Naa))
# 	#if not i in terres:
# 		#f.write("%d %d\n" % (i,i+1))
# 	f.write("%d %d %f\n" % (i,i+Naa+1,0))
# 	f.write("%d %d %f\n" % (i+Naa,i+Naa+1,0))

#Salt bridges	
f.write("%d\n" % len(sbs))
for sb in sbs:
	f.write("%d %d %f\n" % (sb[0],sb[1],sb[2]))	

#Starting coordinates
if Naa>0:
	for ac in vstack([array(cas),array(cbs)]):
		f.write("%f %f %f\n" % (ac[0],ac[1],ac[2]))
if Nnuc>0:
	for ac in vstack([array(phs),array(sus),array(bas)]):
		f.write("%f %f %f\n" % (ac[0],ac[1],ac[2]))
	
f.close
