#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import json
import argparse
import sys
from jinja2 import Environment, FileSystemLoader
import os

path = os.path.join(os.path.abspath(os.path.split(sys.path[0])[0]), "shell")

def main():
    args = parse_args()
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
    env = Environment(loader = FileSystemLoader(path))
    if args.type == 'PD':
        template = env.get_template("pd-scripts.j2")
        Script = template.render(dir = args.dir, server_ip = server_ip,
            status_port = args.status_port, uid = uid, server_port = args.server_port,
            cluster_name_url = cluster_name_url)
    elif args.type == "TIKV":
        template = env.get_template("tikv-scripts.j2")
        Script = template.render(dir = args.dir, server_ip = server_ip,
            status_port = args.status_port, uid = uid, server_port = args.server_port,
            cluster_pd_api = cluster_pd_api)
    elif args.type == "TIDB":
        template = env.get_template("tidb-scripts.j2")
        Script = template.render(dir = args.dir, server_ip = server_ip,
            status_port = args.status_port, uid = uid, server_port = args.server_port,
            cluster_pd_api = cluster_pd_api)
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
