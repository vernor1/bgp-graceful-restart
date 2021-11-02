#!/bin/sh

as=$1
switch1=$2
switch2=$3
rid=$(ip ro get 8.8.8.8 | ip ro get 8.8.8.8 | awk -F"src " 'NR==1{split($2,a," ");print a[1]}')
cat gobgpd_reflector.conf.in | \
	sed -e "s/\$AS/$as/" | \
	sed -e "s/\$ROUTER_ID/$rid/" | \
	sed -e "s/\$SWITCH_ADDR_1/$switch1/" | \
	sed -e "s/\$SWITCH_ADDR_2/$switch2/" \
	> gobgpd_reflector.conf
exec ./gobgpd -f gobgpd_reflector.conf --log-level debug
