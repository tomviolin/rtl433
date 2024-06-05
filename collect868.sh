#!/bin/bash
rtl_433 -s 3200000 -f 915.2M -F log -F json:data`date +%Y%m%d_%H%M%S`.json -M level -M noise -M time:utc -M protocol -M stats -Y autolevel 
# rtl_433 -s 960000 -f 433.90M  -F json:data`date +%Y%m%d_%H%M%S`.json -M level -M noise -M time:utc -M protocol -M stats -Y autolevel

