#!/bin/sh
# Installs git-http on the Omega so update-git.sh can pull from GitHub over HTTPS,
# then checks that git can actually reach the repo.
#
# Run on the Omega: sh /root/wthr-pstr/install-git-http.sh

REPO_URL=https://github.com/hijinksinc/wthr-pstr.git

# The Omega has no battery-backed clock, so it starts up thinking it's 2019 until it gets the
# time from the internet. HTTPS certificate checks fail while the date is wrong.
check_clock() {
	year=$(date +%Y)
	if [ "$year" -lt 2024 ]; then
		echo "The clock says $(date), syncing it from the internet..."
		ntpd -q -n -p 0.lede.pool.ntp.org -p 1.lede.pool.ntp.org
		year=$(date +%Y)
		if [ "$year" -lt 2024 ]; then
			echo "Couldn't set the clock. Check the Omega is connected to the internet and try again."
			exit 1
		fi
		echo "Clock is now $(date)"
	fi
}

if ! command -v git >/dev/null 2>&1; then
	echo "git isn't installed, installing git and git-http"
	PACKAGES="git git-http"
elif [ -x "$(git --exec-path)/git-remote-https" ]; then
	echo "git-http is already installed"
	PACKAGES=""
else
	PACKAGES="git-http"
fi

if [ -n "$PACKAGES" ]; then
	check_clock

	# Some feeds in /etc/opkg/distfeeds.conf (the old LEDE snapshot ones) no longer exist, so
	# opkg update reports errors for them. The Onion feeds, which have git-http, still work.
	echo "Updating package lists..."
	opkg update

	echo "Installing $PACKAGES..."
	if ! opkg install $PACKAGES; then
		echo
		echo "Couldn't install $PACKAGES. Check the Omega is online and can reach the Onion package feed:"
		echo "  wget -q -O /dev/null http://repo.onion.io/omega2/packages/packages/Packages.gz && echo reachable"
		exit 1
	fi

	if [ ! -x "$(git --exec-path)/git-remote-https" ]; then
		echo "opkg finished but git's HTTPS support is still missing"
		exit 1
	fi
	echo "git-http installed"
fi

check_clock

echo "Checking git can reach $REPO_URL..."
if output=$(GIT_TERMINAL_PROMPT=0 git ls-remote "$REPO_URL" 2>&1); then
	echo "OK, git can pull from GitHub over HTTPS"
else
	echo "git couldn't reach the repo:"
	echo "$output"
	exit 1
fi
