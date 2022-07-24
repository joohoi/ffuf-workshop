# ffuf the web

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

There is a sample web application with couple of vulnerabilities included available for you to mess around with. Going forward, it's greatly beneficial to build your own testing range to further develop your automation workflows.
/
