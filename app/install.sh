#!/bin/bash
export SITE_PACKAGES=$(python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")
cd $SITE_PACKAGES 
git clone http://Armandex123@intranet.igp.gob.pe:8082/SMH/SMH-materials-dashboard admin_material