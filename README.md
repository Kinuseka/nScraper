# NHentai API
A python script that collects data from NHentai.net. 

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
**Repositories:**


>[Undetected Chromedriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver)


**Supported Sites at the moment**
```
• NHentai.net[Mirror sites: Nhentai.to])
```

## Run:
`python Start_download.py [args -n/--nuke-code]`
**ex:**
`python Start_download.py -n 401084`




## Note:
> Bypassing cloudflare requires a modified selenium which does not support headless mode. If you are not on a 
desktop environment, you are better off setting `cf_bypass` to `false` in config.json.

> Mirror server is enabled by default incase the official site is not available, if you prefer
to disable this. Please set "mirror_available" to `false` in config.json

> The Mirror server is slightly outdated compared to the official site. Some titles might not be available especially to newer release like 40000+.
though they are being continually updated as time goes.


