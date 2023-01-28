# nScraper
A python script downloader

## Current Supported sites
* **NHentai.net [Mirror site: Nhentai.to]**

## About

**Goals**
```
>Collect data from NHentai
>Automatically save the metadata(tags)
>Download pages concurrently
>API Template (For possible other websites to support)
```

**Libraries used**
```
>bs4 
>Httpx
>Anyio (Trio Backend)
>Trio
>pyyaml
>undetected-chromedriver 
```

**Installation: **
`git clone https://github.com/Kinuseka/nScraper.git`


**Repositories:**


>[Undetected Chromedriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver)


## Run:
`python Start_download.py [args -n/--nuke-code]`
**ex:**
`python Start_download.py -n 401084` or `https://nhentai.net/g/401084`




## Note:
> Bypassing cloudflare requires a modified selenium which does not support headless mode. If you are not on a 
desktop environment, install a virtual desktop using xvfb. Then run it as xvfb-run python Startdownload.py -n <Num>

> Mirror server is enabled by default incase the official site is not available, if you prefer
to disable this. Please set "mirror_available" to `false` in config.json

> The Mirror server is slightly outdated compared to the official site. Some titles might not be available especially to newer release like 40000+.
though they are being continually updated as time goes.


## XVFB INSTALLATION
You can run this program using XVFB if you are trying to run this on headless mode (console only)

Here's how:


Install xvfb: 


Ubuntu/Debian: `sudo apt install xvfb` 

CentOS: `yum install xorg-x11-server-Xvfb`


Then run it as `xvfb-run python Startdownload.py -n <Num>`
