#!/bin/bash
echo BOOT_START $(date)
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq 2>&1 | tail -1
apt-get install -y -qq -o Dpkg::Options::="--force-confnew" openssh-server git curl > /tmp/apt6.log 2>&1
echo APT_INSTALL=$?
mkdir -p /run/sshd
echo "root:kmpgD2CsB3DB2kA-fixlater" | chpasswd 2>/dev/null; echo CHTEMP
PW=$(tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 20)
echo "root:$PW" | chpasswd && echo CHPASS_OK
(echo KVPSJSON:PASS='$PW'; echo root:'$PW') | tee -a /tmp/pwfile > /dev/null
/usr/sbin/sshd -D -p 22 > /tmp/sshd6.log 2>&1 &
sleep 2; ss -tlnp | grep :22 && echo SSHD_OK
if [ ! -x /tmp/cfb ]; then
  curl -sL -o /tmp/cfb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 2>/dev/null
  chmod +x /tmp/cfb
fi
echo BIN_OK
nohup /tmp/cfb tunnel --url tcp://127.0.0.1:22 --no-autoupdate --protocol http2 > /tmp/cf.log 2>&1 &
CFURL=""
for i in $(seq 1 40); do
  sleep 5
  CFURL=$(grep -o 'https://[a-z0-9.-]*trycloudflare.com' /tmp/cf.log 2>/dev/null | tail -1)
  [ -n "$CFURL" ] && break
done
echo CFURL="$CFURL"
echo KVPSJSON:{"\"\"'"'"'x'"'"'\"\""}
echo KVPSJSON:{"host":"$CFURL","port":22,"pass":"$PW"}
while true; do sleep 30; grep -q 'Connection registered' /tmp/cf.log || true; done &
echo BOOT_DONE
