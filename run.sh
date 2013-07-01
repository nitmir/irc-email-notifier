#!/bin/bash
while true; do
/usr/bin/python $1 &>> "/tmp/`/usr/bin/basename $1`.txt"
/bin/sleep 5;
done;
