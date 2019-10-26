#!/bin/sh

mkdir -p ./data1/deploy_v3.0.3/data.pd/
mkdir -p ./data1/deploy_v3.0.3/log/

if test -f "pid"; then
  echo "tidb-server running, kill pd..."
  kill -9 `cat pid`
  rm pid
fi

nohup ./tidb-server \
    -P 4000 \
    --status="10080" \
    --advertise-address="192.168.233.128" \
    --path="192.168.233.128:2379" \
    --log-slow-query="./data1/deploy_v3.0.3/log/tidb_slow_query.log" \
    --log-file="./data1/deploy_v3.0.3/log/tidb.log" 2>> "./data1/deploy_v3.0.3/log/tidb_stderr.log" & echo $! > pid
