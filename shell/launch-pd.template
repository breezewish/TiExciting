#!/bin/sh

mkdir -p ./data1/deploy_v3.0.3/data.pd/
mkdir -p ./data1/deploy_v3.0.3/log/

if test -f "pid"; then
  echo "pd-server running, kill pd..."
  kill -9 `cat pid`
  rm pid
fi

nohup ./pd-server \
    --name="pd_xiaohou-vm1" \
    --client-urls="http://192.168.233.128:2379" \
    --advertise-client-urls="http://192.168.233.128:2379" \
    --peer-urls="http://192.168.233.128:2380" \
    --advertise-peer-urls="http://192.168.233.128:2380" \
    --data-dir="./data1/deploy_v3.0.3/data.pd" \
    --initial-cluster="pd_xiaohou-vm1=http://192.168.233.128:2380" \
    --log-file="./data1/deploy_v3.0.3/log/pd.log" 2>> "./data1/deploy_v3.0.3/log/pd_stderr.log" & echo $! > pid
