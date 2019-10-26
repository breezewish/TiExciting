#!/bin/sh

mkdir -p ./data1/deploy_v3.0.3/data.pd/
mkdir -p ./data1/deploy_v3.0.3/log/

if test -f "pid"; then
  echo "tikv-server running, kill pd..."
  kill -9 `cat pid`
  rm pid
fi

nohup ./tikv-server \
    --addr "0.0.0.0:20160" \
    --advertise-addr "192.168.233.129:20160" \
    --status-addr "192.168.233.129:20180" \
    --pd "192.168.233.128:2379" \
    --data-dir "./data1/deploy_v3.0.3/data" \
    --log-file "./data1/deploy_v3.0.3/log/tikv.log" 2>> "./data1/deploy_v3.0.3/log/tikv_stderr.log" & echo $! > pid
