#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import json
import argparse
import sys

def main():
    args = parse_args()
    '''scripts for pd'''
    server_ip = args.uid.split(":")[0]
    uid = args.uid.split(":")[1]
    cluster_name_url = ""
    cluster_pd_api = ""
    cluster_url = json.loads(args.pd_cluster)
    num = len(cluster_url)
    for pd_ip in cluster_url:
        pd_ip_port = pd_ip.replace("_", ":")
        if num > 1:
            cluster_name_url += cluster_url[pd_ip] + f"=http://{pd_ip_port},"
            cluster_pd_api += f"{pd_ip_port},"
            num -= 1
        else:
            cluster_name_url += cluster_url[pd_ip] + f"=http://{pd_ip_port}"
            cluster_pd_api += f"{pd_ip_port}"
    if args.type == 'PD':
        Script = f"mkdir -p {args.dir}/data.pd \nmkdir -p {args.dir}/log \n\nbin/pd-server \ \n    --name=\"{uid}\" \ \n    --client-urls=\"http://{server_ip}:{args.status_port}\" \ \n    --advertise-client-urls=\"http://{server_ip}:{args.status_port}\" \ \n    --peer-urls=\"http://{server_ip}:{args.server_port}\" \ \n    --advertise-peer-urls=\"{server_ip}:{args.server_port}\" \ \n    --data-dir=\"{args.dir}/data.pd\" \ \n    --initial-cluster=\"{cluster_name_url}\" \ \n    --config=conf/pd.toml \ \n    --log-file=\"{args.dir}/log/pd.log\" 2>> \"{args.dir}/log/pd_stderr.log\"\n"
    elif args.type == "TIKV":
        Script = f"mkdir -p {args.dir}/data \nmkdir -p {args.dir}/log \n\nbin/tikv-server \ \n    --addr \"0.0.0.0:{args.status_port}\" \ \n    --advertise-addr \"{server_ip}:{args.status_port}\" \ \n    --status-addr \"{server_ip}:{args.server_port}\" \ \n    --pd \"{cluster_pd_api}\" \ \n    --data-dir \"{args.dir}/data\" \ \n    --config conf/tikv.toml \ \n    --log-file \"{args.dir}/log/tikv.log\" 2>> \"{args.dir}/log/tikv_stderr.log\" \n"
    elif args.type == "TIDB":
        Script = f"mkdir -p {args.dir}/data \nmkdir -p {args.dir}/log \n\nbin/tidb-server \ \n    -P {args.server_port} \ \n    --status=\"{args.status_port}\" \ \n    --advertise-address=\"{server_ip}\" \ \n    --path=\"{cluster_pd_api}\" \ \n    --config=conf/tidb.toml \ \n    --log-slow-query=\"{args.dir}/log/tidb_slow_query.log\" \ \n    --log-file=\"{args.dir}/log/tidb.log\" 2>> \"{args.dir}/log/tidb_stderr.log\" \n"
    else:
        print("Please input TIKV or PD or TIDB")
        sys.exit(1)

    print(Script)

    return Script


def parse_args():
    parser = argparse.ArgumentParser(
        description="To generate the script")
    parser.add_argument("-dir",
                        dest="dir",
                        help="The installation directory",
                        default="/data/deploy")
    parser.add_argument("-status_port",
                        dest="status_port",
                        help="Status Port",
                        default="status_port")
    parser.add_argument("-server_port",
                        dest="server_port",
                        help="Server Port",
                        default="server_port")
    parser.add_argument("-pd_cluster_ip_uid",
                        dest="pd_cluster",
                        help="Deploy the PD_IP, for example: {\"ip1_port\": \"uid1\", \"ip2_port\":\"uid2\", \"ip3_port\":\"uid3\"}",
                        default="{\"ip1_port\":\"uid1\", \"ip2_port\":\"uid2\"}")
    parser.add_argument("-uid",
                        dest="uid",
                        help="Deploy the pd uid, for example: \"ip1\":\"uid\"",
                        default="ip1:uid1")
    parser.add_argument("type", help="TIKV or TIDB or PD")
    args = parser.parse_args()

    return args


if __name__ == "__main__":
    main()
