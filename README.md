# Weather Poster

Software for bringing your Typifed Weather Poster back to life. Migrates weather data to OpenMeteo.
## Updating your poster

Existing posters need a one-time software update to keep getting the weather. After this update, your poster checks this repo for new software by itself every time it's switched on.

It should take about 10 minutes start to finish to get your poster updated. Just copy and paste the commands below.

### What you need

- Your poster, plugged in and already connected to your home WiFi through the regular setup process. Reach out if you need help getting it connected to your WiFi. 
- A Mac, or a Windows 10 or 11 PC
- Your poster's password: the one you use to log in on the poster's setup page (I'm unsure if they differ, but mine was weather6124)

**Note: ** the documentation below lists the address weatherposter.local or weatherposter, if you have issues connecting, you can also try the default IP of the Omega2+ which is 192.168.1.3
### 1. Connect to your poster

1. On your computer, join the WiFi network called **WeatherPoster**. This is your poster's own network. If it asks for a password, use the WiFi password from your poster's setup instructions.
2. Open a terminal:
   - **Mac:** open **Terminal** (in Applications → Utilities).
   - **Windows:** right-click the Start button and choose **Terminal** or **Windows PowerShell**.
3. Type or paste this command and press Return (Enter on Windows):

   ```bash
   ssh -o HostKeyAlgorithms=+ssh-rsa root@weatherposter
   ```

4. The first time, it asks whether you want to continue connecting. Type `yes` and press Return.
5. Enter your poster's password when asked. Nothing appears on screen while you type it; that's normal. Press Return.

You're connected when you see a banner and a line ending in `root@weatherposter:~#`. Run the commands in the next steps one at a time, pressing Return after each and waiting for it to finish before starting the next.

### 2. Set the poster's clock

The poster doesn't keep time while it's switched off, and downloads fail while its clock is wrong. This sets the clock from the internet:

```bash
ntpd -q -n -p pool.ntp.org
```

It finishes in a few seconds. To check, run `date`: it should show today's date.

### 3. Make sure the poster can download updates

```bash
wget -O /tmp/install-git-http.sh https://raw.githubusercontent.com/hijinksinc/wthr-pstr/main/install-git-http.sh
```

```bash
sh /tmp/install-git-http.sh
```

The last line should say **OK, git can pull from GitHub over HTTPS**. You may see some "Failed to download" errors along the way; those are expected.

### 4. Update the poster

```bash
wget -O /tmp/update-git.sh https://raw.githubusercontent.com/hijinksinc/wthr-pstr/main/update-git.sh
```

```bash
sh /tmp/update-git.sh
```

To check it worked:

```bash
logread -e update-git | tail -3
```

You should see a line saying **updated to** followed by a short code. If it says **keeping current code** instead, see Troubleshooting below.

You can now type `exit` and press Return to disconnect.

### 5. Set your poster's location

The updated poster shows the weather for a location you choose.

1. While still connected to the **WeatherPoster** WiFi, open this address in your web browser: **http://weatherposter.local/apps/weather-location/**
2. Log in with your poster's username (`root`) and password.
3. Search for your city or ZIP code, choose it from the list, and click **Save location**.

Your poster will show the forecast for that location within about an hour. You can reconnect your computer to your usual WiFi now.

### Troubleshooting

- **"no matching host key type found"**: make sure you copied the whole `ssh` command from step 1, including `-o HostKeyAlgorithms=+ssh-rsa`.
- **"Connection timed out" or "No route to host"** when connecting: check your computer is still on the **WeatherPoster** WiFi. Some computers switch back to your home network automatically.
- **"certificate is not yet activated" or "not yet valid"**: the poster's clock is wrong. Repeat step 2, then try again.
- **"unable to resolve host address"**: the poster isn't connected to the internet. Open **http://192.168.3.1** in your browser and connect the poster to your home WiFi again, then start over from step 2.
- **"keeping current code"** after step 4: the poster couldn't download the update. Check it's online, then run step 4 again. Your poster keeps working with its current software in the meantime.
- **The poster still isn't showing the weather after an hour:** reconnect as in step 1 and run `logread -e weather | tail -20`. Include what it shows when you ask for help.
