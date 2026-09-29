#!/bin/sh
# Updates the poster's code from GitHub, then installs the setup web app and the
# weather service. Runs from /etc/rc.local at boot.
#
# Everything is inside main() so the whole script is read before it runs:
# git reset below can replace this file while it's running.

REPO_URL=https://github.com/hijinksinc/wthr-pstr.git
BRANCH=main
DIR=/root/wthr-pstr

main() {
	cd $DIR || exit 1

	# At boot this runs before WiFi is up and the clock is set (the Omega starts up thinking
	# it's 2019, which breaks HTTPS). Wait up to 2 minutes for the clock to be set from the internet.
	tries=0
	while [ "$(date +%Y)" -lt 2024 ] && [ $tries -lt 24 ]; do
		sleep 5
		tries=$((tries + 1))
	done

	git remote set-url origin $REPO_URL
	old_head=$(git rev-parse HEAD)

	# Only replace local files if the download worked and has the poster code in it,
	# so no internet or an empty repo leaves the current code in place
	if git fetch origin $BRANCH && git cat-file -e FETCH_HEAD:weather.py 2>/dev/null; then
		git reset --hard FETCH_HEAD
		logger -t update-git "updated to $(git rev-parse --short HEAD)"
	else
		logger -t update-git "couldn't get code from $REPO_URL ($BRANCH), keeping current code"
	fi

	chmod +x $DIR/gpiomux.sh
	chmod +x $DIR/update-git.sh
	chmod +x $DIR/nothing.sh

	# Install the setup web app and service script, a firmware upgrade wipes /www and /etc/init.d
	cp $DIR/app.fc503d7800c18071df4d.js /www/OnionOS/static/js/
	cp $DIR/Onion-Logo-Full.png /www/OnionOS/static/img/
	if [ -d $DIR/www/apps/weather-location ]; then
		mkdir -p /www/apps
		rm -rf /www/apps/weather-location
		cp -r $DIR/www/apps/weather-location /www/apps/
	fi
	cp $DIR/weather-service /etc/init.d/weather-service
	chmod +x /etc/init.d/weather-service

	# The weather service starts before this runs at boot, so restart it to pick up new code.
	# Left alone if it's been disabled.
	if [ "$(git rev-parse HEAD)" != "$old_head" ] && /etc/init.d/weather-service enabled; then
		logger -t update-git "restarting weather-service"
		/etc/init.d/weather-service restart
	fi
}

main
exit 0
