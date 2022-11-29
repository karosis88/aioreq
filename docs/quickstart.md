# Usage

### Basic usage
---

First, import aioreq.
``` py 
>>> import aioreq
```
This is a very basic example of usage.
``` py
>>> client = aioreq.Client()
>>> import asyncio
>>> aynsio.run(client.get('http://google.com'))
<Response 200 b'OK'>
```

The client's context manager stores all of his connections and files and handles cleanup when we're done with them.
This is a suggested setup.

``` py
>>> async def main():
>>>     async with aioreq.Client() as client:
>>>         response = client.get("http://google.com")
```

This is how 'response' objects are used.
``` py
>>> response.request
<Request GET http://googlge.com>
>>> response.status
200
>>> response.status_message
b'OK'
```
`Aioreq` provides complete header control.
``` py
>>> response.headers
Headers:
	date: Thu, 24 Nov 2022 05:50:34 GMT
	expires: -1
	cache-control: private, max-age=0
	content-type: text/html; charset=ISO-8859-1
	cross-origin-opener-policy-report-only: same-origin-allow-popups; report-to="gws"
	report-to: {"group":"gws","max_age":2592000,"endpoints":[{"url":"https://csp.withgoogle.com/csp/report-to/gws/other"}]}
	p3p: CP="This is not a P3P policy! See g.co/p3phelp for more info."
	content-encoding: gzip
	server: gws
	content-length: 16622
	x-xss-protection: 0
	x-frame-options: SAMEORIGIN
```
As you can see, there is a 'content-encoding' header, and it is gzip.
Aioreq can automatically handle many types of encodings and can easily receive compressed data instead of raw data.

---

This is how accessing the body message works.
``` py
>>> body = response.content
>>> type(body)
bytes
>>> len(body)
50021
```
As you can see, the 'content-length' header has the value '16622,' indicating that the incoming data length should be 
16622, but our content field contains significantly more data than expected. It's because 'Aioreq' 'automatically told 
the server' to use compression for better performance, which is then decoded on the client.
---

If you need to receive very lots of data, use 'StreamClient' instead of 'Client.'
'StreamClient' methods return 'async iterators,' which allow us to receive only a small amount of data per iteration and write it to the hard drive, saving a lot of memory.

``` py
>>> async def main():
>>>     file = open('index.html', 'wb')
>>>     async with aioreq.StreamClient() as stream_client:
>>>         async for chunk in stream_client.get("http://aioreq.example.com")
>>>             file.write(chunk)
>>>     file.close()
```

## Headers

This is how Headers are set up.
``` py
>>> import aioreq
>>> headers = aioreq.Headers()
```

'Aioreq Headers' are objects that are similar to dictionary objects but have some differences.

- case-insensitivity
``` py
>>> headers['my-header'] = 'my-text'
>>> headers['MY-HeAdEr']
'my-text'
```

- pretty-print
``` py
>>> headers
Headers:
    my-header: my-text
```

- aioreq header types compatibility
``` py
>>> from aioreq import headers
>>> new_header = aioreq.Headers()
>>> header_obj = headers.Accept(types=( (headers.MimeType.json, 0.5), ))
>>> new_header.add_header(header_obj)
>>> new_header
Headers:
        accept: application/json; q=0.5
```

## Requests

There is how to make simple GET request.
``` py
>>> import aioreq
>>> async def main():
>>>     async with aioreq.Client() as client:
>>>         await client.get("https://google.com")
```

Alternatively, we can create a Request object and send it directly through the client.
``` py
>>> req = aioreq.Request(
...     url='https://google.com/',
...     method='GET',
...     )
>>> await cl.send_request(req)
```

What about sending path parameters?
``` py
>>> req = aioreq.Request(
...     url='https://google.com/',
...     method='GET',
...     params=(('example_1', 10 ), ('example_2', 20))
...    )
```

and perhaps a body message
``` py
>>> req = aioreq.Request(
...            url='https://google.com',
...            method='GET',
...            content=b'Text for the body')
```

If we want to send a JSON request, we must include the content-type parameter.
``` py
>>> req = aioerq.Request(
...        url='https://google.com',
...        method='GET',
...        content=b'{"test": "test"}',
...        headers = {'content-type': 'application/json'})
```

Alternatively, we can use JsonRequest.
``` py
>>> req = aioerq.JsonRequest(
...        url='https://google.com',
...        method='GET',
...        content=b'{"test": "test"}',
...       )
```

Each response object contains his request.
The 'request' field provides access to the Request object.
``` py
>>> response.request
<Request GET https://google.com>
```

## Clients

Initialization of the client.
``` py
>>> client = aioreq.Client()
>>> stream_client = aioerq.StreamClient()
```

or
``` py
>>> async with aioreq.Client() as client, aioreq.StreamClient() as stream_client:
...	   ...
```

You can provide the client with default headers.
The client employs his headers in all of his requests.

``` py
>>> aioreq.Client(headers={'Accept': 'application/json'})
```

The initialization interface for StreamClient is the same, but the request sending logic is different.

This is how StreamClient requests works.
``` py
>>> async def main(file):
>>> 	async with aioreq.StreamClient() as stream_client:
>>>			async for chunk in stream_client.get('https://youtube.com'):
>>>				file.write(chunk)
```

You can use StreamClient if you don't need a full response right away and want to save a lot of RAM.