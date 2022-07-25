# ffuf the web

Presentation slides available at: <a href="https://io.fi/ffuf-workshop">https://io.fi/ffuf-workshop</a>

## index
 * Example pipeline
 * Testing range
 * Tools examples
 * Utils examples

## example automation pipeline (simple SSTI testing)

This can be saved as a shell script, and it takes a single parameter: the domain name

```
# Read the domain name from the (first) command line parameter, eg: ./script.sh ffuf.io.fi
TARGET=$1

# Run a link finder; hakrawler against our target and save the output
echo https://$TARGET |hakrawler -subs -u |tee target_links.txt

# Run in_scope.py util in order to filter out all out-of-scope urls, save the output
cat target_links.txt |python3 inscope_http.py -s $TARGET |tee inscope_links.txt 

# Extract URL paths from in scope links, these may be separate web applications(!)
cat inscope_links.txt |python3 inscope_http.py -s $TARGET -o dirpath |tee inscope_paths.txt

# Extract GET parameter keys and values from the links list
cat inscope_links.txt |unfurl keys |anew inscope_keys.txt
cat inscope_links.txt |unfurl values |anew inscope_values.txt

# Append a common-known list of parameter names and our custom values to a single wordlist
cat SecLists/Discovery/Web-Content/burp-parameter-names.txt |anew custom_keys.txt
cat inscope_keys.txt |anew custom_keys.txt
cat inscope_values.txt |anew custom_keys.txt

# Use a single SSTI payload for readability, in reality you would have more entries in the wordlist
# If it gets computed, we should see "random25random" in the HTTP response.
echo 'random{{5*5}}random' > ssti.txt

# fuzz through all potential combinations of web path, parameter name and the SSTI payload
# note the -mr parameter detection rule here
ffuf -v -w inscope_paths.txt:PATH -w custom_keys.txt:KEY -w ssti.txt:VALUE -mr 'random25random' -o target_ffuf.json -u 'PATH/?KEY=VALUE'

# Use jq to parse the ffuf results. note the -e flag that causes jq to write exit code based on result
# so we can detect if there were findings or not. Store the return code to a variable "retVal"
jq -e -r '.results [].url' target_ffuf.json > target_results.txt
retVal=$?

# Check if jq returned values, and report them using a Mattermost webhook snippet
if [ $retVal -eq 0 ]; then
    # Combine the results with a header
    echo "SSTI vulnerabilities found:" > target_report.txt
    cat target_results.txt >> target_report.txt
    # Send off the results
    cat target_report.py |python3 mm_webhook.py
fi
```

## Testing range

There is a sample, completely artificial web application with couple of vulnerabilities included available for you to mess around with. Going forward, it's greatly beneficial to build your own testing range to further develop your automation workflows.

The testing range instances are identical, but there's a couple as one box can only handle a limited amount of simultaneous connections.

## Tools examples

Note that many of these tools are written in Go, and in order to install them you need to have a fairly recent version of Go in your system. A guided install is available at <a href="https://go.dev/doc/install">https://go.dev/doc/install</a> 

The binaries installed via `go install` will land in `$HOME/go/bin` so make sure you add that to your `$PATH`. This will be guided in the Go installation linked above.

### Recon

#### Amass
A great, versatile tool for subdomain recon. This tool is very versatile and has a ton of different bells and whistles. 

While it's not a part of the training range of this workshop, you should definitely keep it on your radar when (hopefully) later extending what you learn here.

<a href="https://github.com/OWASP/Amass">https://github.com/OWASP/Amass</a>

#### nmap
The industry standard port scanner that has everything you need from different scanning strategies to service detection and information gathering. Make sure to check the different NSE scripts provided to make your life easier.

Nmap is not a part of the training range, but it's a great addition to the automation later on. With it you are able to easily expand your scope to web services running on nonstandard ports.

<a href="https://nmap.org/">https://nmap.org/</a>


#### httpx

Httpx is a powerful HTTP toolkit that has a bunch of very interesting features like that can help you on your way. As an example you can do web technology detection with it or if you want to expand your scope even further you can for example see if you find new in-scope domains from the CSP headers... 

Make sure you use the `-json` flag to make it easier to post-process with tools like `jq`.

*Installation*
```
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
```

*Example usage*
```
# http technology detection / information gathering
cat target_hosts.txt |httpx -tech-detect -json
```

#### ffuf

A swiss army knife web fuzzer. Allows you to do different scans or recon tasks at scale. There's a ton of features available, the basics are explained in detail in <a href="https://github.com/joohoi/ffuf-workshop/blob/master/ffuf-basics.md">https://github.com/joohoi/ffuf-workshop/blob/master/ffuf-basics.md</a>

*Installation*

```
go install -v github.com/ffuf/ffuf@latest
```
...or if you are running Kali Linux, just 
```
apt update && apt install -y ffuf
```

*Example usage*
Scan for bunch of resources with a list of target https domains while doing per-host autocalibration for the targets.
```
ffuf -w resources.txt:RESOURCE -w domains.txt:DOMAIN -u https://DOMAIN/FUZZ -ac -ach
```

<a href="https://github.com/ffuf/ffuf">https://github.com/ffuf/ffuf</a>

#### hakrawler
A fast web crawler to extract links and 

- httpx
- ffuf
- hakrawler
- interactsh
- notify
- jq
- gron
- unfurl
- tee
- anew


## Utils examples

