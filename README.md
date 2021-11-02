# bgp-graceful-restart
Proof of concept for BGP graceful restart

## Usage
The steps below are for simulating a restarting speaker which has changed its IP address

### Build and start containers
```
cd local-deployment
docker-compose build && docker-compose up -d
```

### Start speaker
```
docker-compose exec app sh -c "./speaker.py --host speaker-1 --start --router-id 192.168.200.1" && \
docker-compose exec app sh -c "./speaker.py --host speaker-1 --add-peers" && \
docker-compose exec app sh -c "./speaker.py --host speaker-1 --prefix 192.168.100.100 --prefix-len 32 --next-hop 192.168.100.1 --add-path"
```

### Interrupt speaker
```
docker-compose exec speaker-1 kill -2 $(docker-compose exec speaker-1 ps | grep gobgpd | awk '{split($1,a," ");print a[1]}')
```

### Restart speaker with the same IP address
```
docker-compose up -d
docker-compose exec app sh -c "./speaker.py --host speaker-1 --start --router-id 192.168.200.1" && \
docker-compose exec app sh -c "./speaker.py --host speaker-1 --prefix 192.168.100.100 --prefix-len 32 --next-hop 192.168.100.1 --add-path" && \
docker-compose exec app sh -c "./speaker.py --host speaker-1 --add-peers --restart"
```

### Restart speaker with a different IP address
```
docker-compose exec app sh -c "./speaker.py --host speaker-2 --start --router-id 192.168.200.1" && \
docker-compose exec app sh -c "./speaker.py --host speaker-2 --prefix 192.168.100.100 --prefix-len 32 --next-hop 192.168.100.1 --add-path" && \
docker-compose exec app sh -c "./speaker.py --host speaker-2 --add-peers --restart"
```

### Show reflector's neighbors
```
docker-compose exec reflector-1 sh -c "./gobgp neighbor"
docker-compose exec reflector-1 sh -c "./gobgp neighbor <neighbor-ip>"
```

### Show reflector's RIB
```
docker-compose exec reflector-1 sh -c "./gobgp global rib"
docker-compose exec reflector-1 sh -c "./gobgp global rib -j 192.168.100.100/32"
```