#!/usr/bin/env python3

from __future__ import absolute_import
from __future__ import print_function
from google.protobuf.any_pb2 import Any

import argparse
import attribute_pb2
import datetime
import gobgp_pb2
import gobgp_pb2_grpc
import grpc
import os
import socket
import time

_TIMEOUT_SECONDS = 2
_PEER_GROUP_NAME = 'reflectors'

class Speaker():
    def __init__(self, host, port):
        self._reflector_addr_1 = os.environ['REFLECTOR_ADDR_1']
        self._reflector_addr_2 = os.environ['REFLECTOR_ADDR_2']
        self._as = int(os.environ['AS'])
        host_ip = socket.gethostbyname(host)
        print(f'Connecting with gobgpd {host_ip}:{port}')
        self.api = gobgp_pb2_grpc.GobgpApiStub(grpc.insecure_channel(f'{host_ip}:{port}'))

    def start(self, router_id):
        print(f'StarBgp: as {self._as}, router_id {router_id}')
        global_params = {'as': self._as, 'router_id': router_id, 'listen_port': -1}
        global_config = gobgp_pb2.Global(**global_params)
        request_params = {'global': global_config}
        self.api.StartBgp(gobgp_pb2.StartBgpRequest(**request_params))

    def stop(self):
        print(f'DeletePeer: neighbor_address {self._reflector_addr_1}')
        try:
            self.api.DeletePeer(gobgp_pb2.DeletePeerRequest(
                address = self._reflector_addr_1))
        except Exception as e:
            print(e)

        print(f'DeletePeer: neighbor_address {self._reflector_addr_2}')
        try:
            self.api.DeletePeer(gobgp_pb2.DeletePeerRequest(
                address = self._reflector_addr_2))
        except Exception as e:
            print(e)

        print(f'DeletePeerGroup: name {_PEER_GROUP_NAME}')
        try:
            self.api.DeletePeerGroup(
                gobgp_pb2.DeletePeerGroupRequest(
                    name = _PEER_GROUP_NAME))
        except Exception as e:
            print(e)

        print('StopBgp')
        self.api.StopBgp(gobgp_pb2.StopBgpRequest())

    def add_peers(self, restart_time, is_restart):
        print(f'AddPeerGroup: peer_as {self._as}, peer_group_name {_PEER_GROUP_NAME}, restart_time {restart_time}, hold_time {restart_time} local_restarting {is_restart}')
        peer_group_conf = gobgp_pb2.PeerGroupConf(
            peer_as = self._as,
            peer_group_name = _PEER_GROUP_NAME)
        timers = gobgp_pb2.Timers(
            config = gobgp_pb2.TimersConfig(
                hold_time = restart_time))
        graceful_restart = gobgp_pb2.GracefulRestart(
            enabled = True,
            restart_time = restart_time,
            local_restarting = is_restart)
        afi_safis = [
            gobgp_pb2.AfiSafi(
                mp_graceful_restart = gobgp_pb2.MpGracefulRestart(
                    config = gobgp_pb2.MpGracefulRestartConfig(enabled = True)),
                config = gobgp_pb2.AfiSafiConfig(
                    family = gobgp_pb2.Family(afi = gobgp_pb2.Family.AFI_IP, safi = gobgp_pb2.Family.SAFI_UNICAST),
                    enabled = True)),
            gobgp_pb2.AfiSafi(
                mp_graceful_restart = gobgp_pb2.MpGracefulRestart(
                    config = gobgp_pb2.MpGracefulRestartConfig(enabled = True)),
                config = gobgp_pb2.AfiSafiConfig(
                    family = gobgp_pb2.Family(afi = gobgp_pb2.Family.AFI_IP6, safi = gobgp_pb2.Family.SAFI_UNICAST),
                    enabled = True))
        ]
        self.api.AddPeerGroup(
            gobgp_pb2.AddPeerGroupRequest(
                peer_group = gobgp_pb2.PeerGroup(
                    conf = peer_group_conf,
                    timers = timers,
                    graceful_restart = graceful_restart,
                    afi_safis = afi_safis)))

        print(f'AddPeer: neighbor_address {self._reflector_addr_1}, peer_group_name {_PEER_GROUP_NAME}')
        self.api.AddPeer(gobgp_pb2.AddPeerRequest(
            peer = gobgp_pb2.Peer(
                conf = gobgp_pb2.PeerConf(
                    neighbor_address = self._reflector_addr_1,
                    peer_group = _PEER_GROUP_NAME),
                graceful_restart = graceful_restart)))

        print(f'AddPeer: neighbor_address {self._reflector_addr_2}, peer_group_name {_PEER_GROUP_NAME}')
        self.api.AddPeer(gobgp_pb2.AddPeerRequest(
            peer = gobgp_pb2.Peer(
                conf = gobgp_pb2.PeerConf(
                    neighbor_address = self._reflector_addr_2,
                    peer_group = _PEER_GROUP_NAME),
                graceful_restart = graceful_restart)))

    def add(self, prefix, prefix_len, next_hop):
        print(f'AddPath: prefix {prefix}, prefix_len {prefix_len}, next_hop {next_hop}')
        nlri_any = Any()
        nlri_any.Pack(attribute_pb2.IPAddressPrefix(
            prefix_len = prefix_len,
            prefix = prefix))
        origin_any = Any()
        origin_any.Pack(attribute_pb2.OriginAttribute(origin = 2))
        next_hop_any = Any()
        next_hop_any.Pack(attribute_pb2.NextHopAttribute(next_hop = next_hop))
        self.api.AddPath(
            gobgp_pb2.AddPathRequest(
                table_type = gobgp_pb2.GLOBAL,
                path = gobgp_pb2.Path(
                    nlri = nlri_any,
                    pattrs = [origin_any, next_hop_any],
                    family = gobgp_pb2.Family(afi = gobgp_pb2.Family.AFI_IP, safi = gobgp_pb2.Family.SAFI_UNICAST))),
            _TIMEOUT_SECONDS)

    def delete(self, prefix, prefix_len, next_hop):
        print(f'DeletePath: prefix {prefix}, prefix_len {prefix_len}, next_hop {next_hop}')
        nlri_any = Any()
        nlri_any.Pack(attribute_pb2.IPAddressPrefix(
            prefix_len = prefix_len,
            prefix = prefix))
        origin_any = Any()
        origin_any.Pack(attribute_pb2.OriginAttribute(origin = 2))
        next_hop_any = Any()
        next_hop_any.Pack(attribute_pb2.NextHopAttribute(next_hop = next_hop))
        self.api.DeletePath(
            gobgp_pb2.DeletePathRequest(
                table_type = gobgp_pb2.GLOBAL,
                path=gobgp_pb2.Path(
                    nlri = nlri_any,
                    pattrs = [origin_any, next_hop_any],
                    family = gobgp_pb2.Family(afi=gobgp_pb2.Family.AFI_IP, safi=gobgp_pb2.Family.SAFI_UNICAST))),
            _TIMEOUT_SECONDS)

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description='GoBGP Speaker')
    arg_parser.add_argument('--host', type=str, required=True, help='IP address of gobgpd')
    arg_parser.add_argument('--port', type=int, default=50051, help='gRPC port of gobgpd (default: 50051)')
    arg_parser.add_argument('--router-id', type=str, help='BGP Router Id')
    arg_parser.add_argument('--prefix', type=str, help='Prefix')
    arg_parser.add_argument('--prefix-len', type=int, help='Prefix length')
    arg_parser.add_argument('--next-hop', type=str, help='Next hop')
    arg_parser.add_argument('--restart-time', type=int, default=300, help='Graceful restart time (default: 300)')
    arg_parser.add_argument('--restart', action='store_true', help='Indicates if local is restarting')

    arg_group = arg_parser.add_mutually_exclusive_group(required=True)
    arg_group.add_argument('--start', action='store_true', help='Start speaker (requires --router-id)')
    arg_group.add_argument('--stop', action='store_true', help='Stop speaker')
    arg_group.add_argument('--add-peers', action='store_true', help='Restart speaker (requires --router-id)')
    arg_group.add_argument('--add-path', action='store_true', help='Add path (requires --prefix, --prefix-len, --next-hop)')
    arg_group.add_argument('--delete-path', action='store_true', help='Delete path (requires --prefix, --prefix-len, --next-hop)')
    args = arg_parser.parse_args()
    speaker = Speaker(args.host, args.port)
    if args.start:
        if not args.router_id:
            print('Invalid --router_id')
            os.Exit(1)
        speaker.start(args.router_id)
    elif args.stop:
        speaker.stop()
    elif args.add_peers:
        speaker.add_peers(args.restart_time, args.restart == True)
    elif args.add_path:
        if not args.prefix or not args.prefix_len or not args.next_hop:
            print('Invalid --prefix or --prefix_len or --next_hop')
            os.Exit(1)
        speaker.add(args.prefix, args.prefix_len, args.next_hop)
    elif args.delete_path:
        if not args.prefix or not args.prefix_len or not args.next_hop:
            print('Invalid --prefix or --prefix_len or --next_hop')
            os.Exit(1)
        speaker.delete(args.prefix, args.prefix_len, args.next_hop)
    else:
        print('Invalid arguments')
