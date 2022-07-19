# ffuf it up


## The basics
Many of the command line flags of `ffuf` are the same than in `curl` so in case you are an avid curl user, you should feel right at home with many ffuf commands.

To configure a ffuf run, two things are mandatory: 
 - Having a wordlist, or a command that provides different inputs
 - Setting up a `FUZZ` keyword in some part of the request

```
# Example
ffuf -w wordlist.txt -u 'https://ffuf.io.fi/FUZZ'
```

### Wordlists
In order to tell ffuf about different inputs to test out, a wordlist is needed. You can supply one or more wordlists on the command line, and in case you wish (or are using multiple wordlists) you can choose a custom `FUZZ` keyword for them. To do this, add a colon and the name after the wordlist filename (without whitespaces). Default is always `FUZZ`. A single keyword can also be used in multiple locations in the HTTP request.
```
# Custom FUZZ keyword example
ffuf -w wordlist.txt:MYCUSTOMKEYWORD -u 'https://ffuf.io.fi/MYCUSTOMKEYWORD'
```

#### Multiple wordlists
You can supply ffuf with multiple wordlists (remember to configure a custom keyword for them though!). The behavior differs from the operation mode selected, these are explained below.

```
# Multi-wordlist example
ffuf -w domains.txt:DOMAIN -w wordlist.txt:WORD -u 'https://DOMAIN/WORD'
```

##### Clusterbomb mode
This is the default mode for multi-wordlists, and is active if no other `-mode` is selected.  

First word of first wordlist is tested against all the words from the second wordlist before moving along to test the second word in first wordlist against all the words in the second wordlist. In short, all of the different combinations are tried out.

This of course applies up to infinity, as the number of wordlists are not capped. Be noted however that the complete run length will grow exponentally when adding new wordlists in to the mix.

```
# Multi-wordlist clusterbomb example
ffuf -mode clusterbomb -w domains.txt:DOMAIN -w wordlist.txt:WORD -u 'https://DOMAIN/WORD'
```

##### Pitchfork mode
This is an alternative multi-wordlist mode. When running a pitchfork operation, the words from the wordlists are read in lockstep. This means that the first word from all the wordlists is used in the first request, second word from all of the wordlists is used for the second and so on.

```
# Pitchfork example
ffuf -mode pitchfork -w usernames.txt:USER -w user_ids.txt:UID -u 'https://example.org/u/UID/profile/USER'
```

#### Wordlist resources
Here are links to couple of really good wordlist collections / combinations.

- A combination wordlist from multiple sources, very powerful: https://github.com/six2dez/OneListForAll
- Collection of context specific wordlists: https://github.com/danielmiessler/SecLists
- Check [OneListForAll README.md](https://github.com/six2dez/OneListForAll) for additional links to different wordlist resources

### Request configuration

There are quite a few different ways to customize the request, but I'm going to start with the most obvious one (and the most simple); a raw HTTP request saved to a file.

You can supply ffuf with a raw HTTP `-request` file. ffuf will parse the request and configure all the required headers, POST/PUT/PATCH body data, request verb - you name it. 

The only information the raw HTTP request does not carry over is the protocol - either HTTP or HTTPS. In the modern world HTTPS is the default, and ffuf is no different in this regard. If you however are targeting a plain HTTP service, you can tell that to ffuf with a command line parameter `-reqeust-proto http` 

```
# Raw request example
ffuf -w wordlist.txt -request raw_req.txt
```

#### HTTP verb

You can use any verb available (and unavailable, there's nothing stopping you from trying something obscure), by using command line argument `-X VERBNAME`

```
# Verb example
ffuf -X PATCH -w wordlist.txt -u https://ffuf.io.fi/FUZZ
```

#### Headers

You can either define different header key-value pairs by using command line argument `-H 'Name: Value'` You can also use any of the keywords as a part of either (or a part of); the header key or value.

```
# Header example
ffuf -w wordlist.txt -u 'https://ffuf.io.fi/' -H 'FUZZ: 127.0.0.1'
```

#### Request body (data)

To add a request body to the request, the argument `-d your_request_body_here`. Please be aware that ffuf does not set up any header values based on your request body content. 

A very common mistake people make is to not to include a proper `Content-Type` - header when working with for example JSON or HTML form data.

```
# Request body example
ffuf -w sqli_payloads.txt -u 'https://ffuf.io.fi/api/v1/users/1' \
     -X PUT -H 'Content-Type: application/json' -d '{"uid":"FUZZ"}' -X PUT
```

#### Proxy

You can use HTTP or SOCKS proxies with ffuf in case you find yourself needing one. Like in curl, this can be done with a CLI argument `-x http://proxy_ip:proxy_port`

```
# Proxy example
ffuf -x 'http://127.0.0.1:8080' -w wordlist.txt -u 'https://ffuf.io.fi/FUZZ'
```
#### Replay-proxy

You can send only the requests that are matched by a _matcher_ and not filtered out by a _filter_ (more about these in the next chapter) - to a proxy of your choice. 

A proxy is typically in this case a Burp or ZAP proxy and are used in order to later manipulate these requests manually in a graphical repeater tool.

The reasoning to send only the matches is basically to not to overpopulate the proxy history with unnecessary hits that there can be hundreds of thousands of.

```
# Replay-proxy example
ffuf -w wordlist.txt -u 'https://ffuf.io.fi/FUZZ' -replay-proxy 'http://127.0.0.1:8080'
````
### Matching and filtering

The internal logic that ffuf utilizes is as follows:
1. Send request
2. Receive response
3. See if the response matches one of the _matchers_, if **not** discard the response and move on to next request
4. See if the response matches one of the _filters_, if it **does**, discard the response and move on to next request
5. If `-replay-proxy` is defined, re-send the request using the replay-proxy
6. Display the result, and keep it in the memory for output file writing later on

In this chapter we go through different matchers and filters. Each matcher has its filter counterpart, as the internal functionality is exactly the same, while the effect of them are complete opposites.

The user is able to mix and match (pun intended) different matchers and filters as they wish.

All of the numeric matchers & filters support multiple values (separated by comma)
```
-mc 200,301
```
and value ranges, denoted by a dash
```
-mc 200,300-304,401-403
```

#### Matcher types

**Response code: -mc and -fc**
This is the most common matcher/filter that inspects the response HTTP code, and makes decisions based on it. A global default in ffuf is matching response codes 200,204,301,302,307,401,403,405,500 for ease of use. 

-mc also has a special value "all" to tell ffuf to match everything, to later filter out based on some unwanted attribute of the response.

```
# Example: match all, but filter out all 400 (bad request) responses
ffuf -w wordlist.txt -u 'https://ffuf.io.fi/FUZZ' -mc all -fc 400
```

**Response size: -ms and -fs**
Matcher and filter based on the response Content-Length. This is often quite powerful when used in conjunction with -mc all, or in cases where a web service responds with for example a status code 200 to every request.

```
# Example: match all, but filter out all responses of size 42
ffuf -w wordlist.txt -u 'https://ffuf.io.fi/FUZZ' -mc all -fs 42
```

**Number of words: -mw and -fw**
Matcher and filter based on number of words (strings terminated by a whitespace) in the response. 

The most common use case for this is to filter out false positives where the service responds with varying Content-Length (if it reflects the user input for example), in which case the number of words in the response still stays static.

```
# Example: match all, but filter out all responses of word count 7
ffuf -w wordlist.txt -u 'https://ffuf.io.fi/FUZZ' -mc all -fw 7
```

**Number of lines: -ml and -fl**
Similar in both uses to -mw and -fw, but counts number of lines in the response instead of number of words. The use cases are also similar. In most cases where you can decide between word and line count matching / filtering, you most likely should go with the word numbers, as it's more specific.

**Regexp: -mr and -fr**
Using this matcher / filter, you can define an regular expression to either match wanted resources or to filter out unsuccessful ones. Regexes are notoriously human-hostlile but very powerful.

To use this type of matcher / filter you don't need to be an regex ninja though! The most common use case is to just look for the response for a specific string.

While regexes are case sensitive by default, you can prefix your regex with `(?i)` to make it case insensitive.

The example below fuzzes through different GET parameter names, and looks for open redirect vulnerabilities by looking into `Location` header in the response.

**Time based: -mt and -ft**
Response time based matching and filtering works great for timing attacks as well as matching for timing based sql injection attacks.

Different from the other filters and matchers, you can use greater than: > and smaller than < operators to match / filter for successfully executed sql injection.

The value is in milliseconds.

```
# Example timing based sql injection payload
ffuf -w sqli_payloads.txt -u 'https://ffuf.io.fi/api/something' \
     -H 'Content-Type: application/json' -d '{"id":"FUZZ"}' -mt >5000
```

### Output

ffuf has different ways to display output in both - standard output in terminal as well as output files in various file formats.

The output file name can be set with a command line argument `-o filename.ext` and the file format with: `-of json`

The different file types are as follows:
json, ejson, html, md, csv, ecsv
 - Good 'ol JSON `json`
 - Base64 encoded payload in JSON for funky input data `ejson`
 - HTML page with interactive searchable table: `html`
 - Markdown:  `md`
 - CSV: `csv`
 - Base64 encoded payload in CSV for funky input data `ecsv`
 - All of the above: `all`, the `-o filename` is used for the base name only, and the file format part is appended as an file name extension.

#### JSONlines stdout output

Changing the stdout messages from human-friendly default formatting to a jsonlines format for machine readable real-time output can prove to be beneficial in cases where the user might want to run `ffuf` as a part of automation process and to react on the matches real-time.

The stdout output can be changed to jsonlines with a command line flag `-json`
