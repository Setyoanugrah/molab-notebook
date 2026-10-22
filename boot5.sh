#!/bin/bash
L=/root/kvboot.log
echo "BOOT_START $(date -u)" > "$L"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq > /dev/null 2>&1
echo "APT_UPDATE=$?" >> "$L"
apt-get install -y -qq openssh-server sshpass curl >> "$L" 2>&1
echo "APT_INSTALL=$?" >> "$L"
KP="kmp$(head -c12 /dev/urandom | base64 | tr -d '/+=' | head -c 12)"
printf "root:%s\n" "$KP" | chpasswd
echo "CHPASS_OK" >> "$L"
mkdir -p /run/sshd
ssh-keygen -A > /dev/null 2>&1
[ -f /etc/ssh/sshd_config.d/99-kvps.conf ] || printf "Port 22\nPasswordAuthentication yes\nPermitRootLogin yes\n" > /etc/ssh/sshd_config.d/99-kvps.conf
/usr/sbin/sshd
echo "SSHD_OK" >> "$L"
nohup bash -c 'while true; do ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ServerAliveInterval=15 -o ExitOnForwardFailure=yes -T -p 443 -R0:localhost:22 tcp@free.pinggy.io 2>&1; echo "> reconnect"; sleep 3; done' > /tmp/pinggy.log 2>&1 &
U=""
for i in $(seq 1 90); do
  U=$(grep -o "tcp://[a-zA-Z0-9.-]*:[0-9]*" /tmp/pinggy.log | tail -1)
  [ -n "$U" ] && break
  sleep 2
done
H=$(echo "$U" | sed 's|tcp://||;s|:.*||'); P=$(echo "$U" | sed 's|.*:||')
echo "KVPSJSON {\"host\":\"$H\",\"port\":$P,\"user\":\"root\",\"pass\":\"$KP\",\"updated\":\"$(date -u +%FT%TZ)\"}"
echo "KVPS ssh -p $P root@$H pass=$KP"
echo "DONE" >> "$L"
last="x"
while true; do
  sleep 30
  U2=$(grep -o "tcp://[a-zA-Z0-9.-]*:[0-9]*" /tmp/pinggy.log | tail -1)
  [ -n "$U2" ] && [ "$U2" != "$last" ] || continue
  last="$U2"
  H=$(echo "$U2" | sed 's|tcp://||;s|:.*||'); P=$(echo "$U2" | sed 's|.*:||')
  echo "KVPSJSON {\"host\":\"$H\",\"port\":$P,\"user\":\"root\",\"pass\":\"$KP\",\"updated\":\"$(date -u +%FT%TZ)\"}"
done
