#!/bin/bash
rtl_433 -f 915M  -F json:data`date +%Y%m%d_%H%M%S`.json -M level -M noise -M time:utc -M protocol -M stats -Y autolevel 
# rtl_433 -s 960000 -f 433.90M  -F json:data`date +%Y%m%d_%H%M%S`.json -M level -M noise -M time:utc -M protocol -M stats -Y autolevel

