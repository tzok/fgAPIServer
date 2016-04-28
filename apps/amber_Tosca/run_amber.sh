#!/bin/bash
#
# amber_run.sh - This script is meant to run on Grid or Container
#

if [ "$VO_ENMR_EU_SW_DIR" != "" ]; then
  echo "Running on Grid"
  /bin/uname -a | /bin/grep 'x86_64' > /dev/null && ARCH='64' || ARCH='32'
  export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/amber11/lib
  AMBERHOME=$VO_ENMR_EU_SW_DIR/CIRMMP/amber/11/$ARCH
  DIRAE=$AMBERHOME/exe/
else
  echo "Running on Container"
  export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/amber14/lib
  AMBERHOME=/usr/local/amber14
  DIRAE=$AMBERHOME/bin/
fi

# Extract in
tar xvfz in.tgz

#AMBER_COMMAND
$DIRAE/sander -O -i sander0.in -o sander0.out -p prmtop -c prmcrd -r sander0.crd -ref  prmcrd
$DIRAE/ambpdb -p prmtop < sander0.crd > amber_final0.pdb

# Collect output
tar cvfz pro.tgz ./* --exclude in.tgz --exclude run_amber.sh

# Notify end
echo "Done"
